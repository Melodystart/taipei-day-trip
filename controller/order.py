from model.order import OrderModel
from view.order import OrderView
from dotenv import get_key
import jwt
import requests
from flask import *

order = Blueprint('order',__name__)

key = get_key(".env", "key")

def error(result, message):
	result["error"] = True
	result["message"] = message
	return result

@order.route("/api/orders",methods=['POST'])
def ordering():
	result = {}
	try:
		token = request.headers['Authorization'][7:]
		userInfo = jwt.decode(token, key, algorithms="HS256")
	except:
		return error(result,"未登入系統，拒絕存取"), 403

	try:
		try:
			data = request.get_json()
			memberId, prime, amount, contactName, contactEmail, contactPhone, bookingIdList, firstImage, transactionTime, transactionDate, orderId = OrderView.ordering(userInfo, data)
			bookingIds = ""

			if not memberId or not prime or not amount or not contactName or not contactEmail or not contactPhone or not bookingIdList or not orderId or len(contactPhone) != 10:
				return error(result,"訂單建立失敗，輸入不正確/不完整或其他原因"), 400

			for bookingId in bookingIdList:

				data = OrderModel.check_payment_status(bookingId)
				if data != None:
					return error(result,"訂單建立失敗，此訂單含已付過款行程，請重新整理預定行程頁面"), 400
				bookingIds += str(bookingId) + ","
				
			bookingIds = bookingIds.strip(",")

			OrderModel.create(orderId, memberId, amount, contactName,contactEmail, contactPhone, bookingIds, transactionDate, firstImage)

			for bookingId in bookingIdList:
				OrderModel.record_number_tobooking(orderId, bookingId, memberId)

		except Exception as e:
			return error(result, "訂單建立失敗，輸入不正確或其他原因"+e.__class__.__name__+": "+str(e)), 400

		partner_key = get_key(".env", "partner_key")
		merchant_id = 'start99start_CTBC'
		url = 'https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime'
		headers = {'Content-Type': 'application/json','x-api-key': partner_key}
		payment_details = OrderView.payment_details(prime, partner_key, merchant_id, amount, orderId, contactPhone, contactName, contactEmail)

		r = requests.post(url, json=payment_details, headers=headers).json()

		result, rec_status, rec_msg, rec_trade_id = OrderView.payment_result(result, orderId, r)

		if int(rec_status) == 0:

			if r["order_number"] != orderId:
				OrderModel.record_payment("付款異常", rec_status, rec_msg, rec_trade_id, orderId, memberId)
				return error(result,"付款訂單號碼與回傳訂單號碼不符，請聯絡專人處理"), 500
			else:
				OrderModel.record_payment("已付款", rec_status, rec_msg, rec_trade_id, orderId, memberId)

			for bookingId in bookingIdList:
				OrderModel.record_payment_tobooking(bookingId, memberId)

			result["data"]["payment"]["message"] = "付款成功"
			return result, 200
		else:
			OrderModel.record_payment_failure(rec_status, rec_msg, rec_trade_id, orderId, memberId)
			result["data"]["payment"]["message"] = "付款失敗："+ r["msg"]
			return result, 200

	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500

@order.route("/api/orders",methods=['GET'])
def getOrders():
	result = {}
	try:
		token = request.headers['Authorization'][7:]
		userInfo = jwt.decode(token, key, algorithms="HS256")
	except:
		return error(result,"未登入系統，拒絕存取"), 403

	try:
		memberId = userInfo["id"]
		data = OrderModel.get_orders(memberId)
		result = OrderView.orders(result, data)
		return result, 200		
	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500

@order.route("/api/order/<int:orderNumber>",methods=['GET'])
def getOrderDetails(orderNumber):
	result = {}
	try:
		token = request.headers['Authorization'][7:]
		userInfo = jwt.decode(token, key, algorithms="HS256")
	except:
		return error(result,"未登入系統，拒絕存取"), 403

	try:
		memberId = userInfo["id"]
		data = OrderModel.get_order(memberId, orderNumber)

		if len(data) == 0:
			result["data"] = None
			return result, 200

		result = OrderView.order(result, data, orderNumber)

		bookingIdList = data[0].split(',')

		for i in range(len(bookingIdList)):
			bookingId = bookingIdList[i]
			attraction = OrderModel.get_order_booking(memberId, bookingId)
			item = OrderView.booking_in_order(attraction)
			result["data"]["details"].append(item)

		return result, 200		

	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500