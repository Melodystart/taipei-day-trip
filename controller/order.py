from model.order import Order
from dotenv import get_key
import time
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
		order = Order()
		try:
			data = request.get_json()
			memberId = userInfo["id"]
			prime = data['prime']
			amount = data['order']['amount']
			contactName = data['order']['contact']['name']
			contactEmail = data['order']['contact']['email']
			contactPhone = data['order']['contact']['phone']
			bookingIdList = data['order']["bookingIdList"]
			firstImage = data['order']['details'][0]['trip']['attraction']['image']
			transactionTime = time.localtime()
			transactionDate = str(time.strftime("%Y/%m/%d %H:%M", transactionTime))
			orderId = str(time.strftime("%Y%m%d%H%M%S", transactionTime)) + str(memberId)
			bookingIds = ""

			if not memberId or not prime or not amount or not contactName or not contactEmail or not contactPhone or not bookingIdList or not orderId or len(contactPhone) != 10:
				return error(result,"訂單建立失敗，輸入不正確/不完整或其他原因"), 400

			for bookingId in bookingIdList:

				data = order.check_payment_status(bookingId)
				if data != None:
					return error(result,"訂單建立失敗，此訂單含已付過款行程，請重新整理預定行程頁面"), 400
				bookingIds += str(bookingId) + ","
				
			bookingIds = bookingIds.strip(",")

			order.create(orderId, memberId, amount, contactName,contactEmail, contactPhone, bookingIds, transactionDate, firstImage)

			for bookingId in bookingIdList:
				order.record_number_tobooking(orderId, bookingId, memberId)

		except Exception as e:
			return error(result, "訂單建立失敗，輸入不正確或其他原因"+e.__class__.__name__+": "+str(e)), 400

		partner_key = get_key(".env", "partner_key")
		merchant_id = 'start99start_CTBC'

		url = 'https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime'
		headers = {'Content-Type': 'application/json','x-api-key': partner_key}

		payment_details = {
			"prime": prime,
			"partner_key": partner_key,
			"merchant_id": merchant_id,
			"details":"台北一日遊",
			"amount": amount,
			"order_number": orderId,
			"cardholder": {
					"phone_number": contactPhone,
					"name": contactName,
					"email": contactEmail,
					"zip_code": "100",
					"address": "台北市天龍區芝麻街1號1樓",
					"national_id": "A123456789"
			},
			"remember": False
		}

		r = requests.post(url, json=payment_details, headers=headers).json()

		result["data"] = {}
		result["data"]["number"] = orderId
		result["data"]["payment"] = {}
		result["data"]["payment"]["status"] = r["status"]

		rec_status = r["status"]
		rec_msg = r["msg"]
		rec_trade_id = r["rec_trade_id"]

		if int(r["status"]) == 0:

			if r["order_number"] != orderId:
				order.record_payment("付款異常", rec_status, rec_msg, rec_trade_id, orderId, memberId)
				return error(result,"付款訂單號碼與回傳訂單號碼不符，請聯絡專人處理"), 500
			else:
				order.record_payment("已付款", rec_status, rec_msg, rec_trade_id, orderId, memberId)

			for bookingId in bookingIdList:
				order.record_payment_tobooking(bookingId, memberId)

			result["data"]["payment"]["message"] = "付款成功"
			return result, 200
		else:
			order.record_payment_failure(rec_status, rec_msg, rec_trade_id, orderId, memberId)
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
		order = Order()
		memberId = userInfo["id"]
		data = order.get_orders(memberId)
		result["data"] = []

		if len(data) == 0:
			result["data"] = None
			return result, 200

		for i in range(len(data)):
			item = {}
			item["orderId"] = data[i][0]
			item["transactionDate"] = data[i][1]
			item["paymentStatus"] = data[i][2]
			item["amount"] = data[i][3]
			item["msg"] = data[i][4]
			item["firstImage"] = data[i][5]
			result["data"].append(item)
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
		order = Order()
		memberId = userInfo["id"]
		data = order.get_order(memberId, orderNumber)

		if len(data) == 0:
			result["data"] = None
			return result, 200

		result["data"] = {}
		result["data"]["number"] = orderNumber
		result["data"]["amount"] = data[1]
		result["data"]["contact"] = {}
		result["data"]["contact"]["name"] = data[2]
		result["data"]["contact"]["email"] = data[3]
		result["data"]["contact"]["phone"] = data[4]
		result["data"]["status"] = data[5]
		result["data"]["msg"] = data[6]
		result["data"]["details"] = []

		bookingIdList = data[0].split(',')

		for i in range(len(bookingIdList)):
			bookingId = bookingIdList[i]
			attraction = order.get_order_booking(memberId, bookingId)
			item = {}
			item["price"] = attraction[0]
			item["trip"] = {}
			item["trip"]["date"] = attraction[1].strftime("%Y-%m-%d")
			item["trip"]["time"] = attraction[2]
			item["trip"]["attraction"] = {}
			item["trip"]["attraction"]["id"] = attraction[3]
			item["trip"]["attraction"]["name"] = attraction[4]
			item["trip"]["attraction"]["address"] = attraction[5]
			item["trip"]["attraction"]["image"] = attraction[6].split(',')[0]
			result["data"]["details"].append(item)

		return result, 200		

	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500