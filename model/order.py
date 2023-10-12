from dotenv import get_key
import time
import mysql.connector
from mysql.connector import pooling
import math
import jwt
from datetime import datetime, timedelta
import requests
from flask import *

order = Blueprint('order',__name__)

key = get_key(".env", "key")

conPool = pooling.MySQLConnectionPool(user= get_key(".env", "user"), password= get_key(".env", "password"), host='localhost', database='attractions', pool_name='attractionsConPool', pool_size=10)

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

			con = conPool.get_connection()
			cursor = con.cursor()

			for bookingId in bookingIdList:
				cursor.execute("SELECT * FROM booking WHERE paymentStatus=%s AND id=%s",("已付款",bookingId))
				data = cursor.fetchone()
				if data != None:
					cursor.close()
					con.close()
					return error(result,"訂單建立失敗，此訂單含已付過款行程，請重新整理預定行程頁面"), 400
				bookingIds += str(bookingId) + ","
				
			bookingIds = bookingIds.strip(",")
			cursor.execute("INSERT INTO orders (orderId,memberId, paymentStatus, amount, contactName, contactEmail, contactPhone, bookingIdList, transactionDate, firstImage) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",(orderId, memberId, "未付款", amount, contactName,contactEmail, contactPhone, bookingIds, transactionDate, firstImage))
			con.commit()

			for bookingId in bookingIdList:
				cursor.execute("UPDATE booking set orderId=%s WHERE id = %s and memberId= %s",(orderId, bookingId, memberId))
				con.commit()

			cursor.close()
			con.close()
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

		con = conPool.get_connection()
		cursor = con.cursor()

		if int(r["status"]) == 0:
			if r["order_number"] != orderId:
				cursor.execute("UPDATE orders set paymentStatus=%s, statusCode=%s, msg=%s, rec_trade_id =%s WHERE orderId = %s and memberId= %s",("付款異常", r["status"], r["msg"], r["rec_trade_id"], orderId, memberId))
				con.commit()
				
				cursor.close()
				con.close()
				return error(result,"付款訂單號碼與回傳訂單號碼不符，請聯絡專人處理"), 500

			cursor.execute("UPDATE orders set paymentStatus=%s, statusCode=%s, msg=%s, rec_trade_id =%s WHERE orderId = %s and memberId= %s",("已付款", r["status"], r["msg"], r["rec_trade_id"], orderId, memberId))
			con.commit()

			for bookingId in bookingIdList:
				cursor.execute("UPDATE booking set paymentStatus=%s WHERE id = %s and memberId= %s",('已付款', bookingId, memberId))
				con.commit()

			cursor.close()
			con.close()
			result["data"]["payment"]["message"] = "付款成功"
			return result, 200
		else:
			cursor.execute("UPDATE orders set statusCode=%s, msg=%s, rec_trade_id =%s WHERE orderId = %s and memberId= %s",(r["status"], r["msg"], r["rec_trade_id"], orderId, memberId))
			con.commit()

			cursor.close()
			con.close()
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
		con = conPool.get_connection()
		cursor = con.cursor()
		
		sql = "SELECT orderId, transactionDate, paymentStatus, amount,  msg, firstImage from orders WHERE memberId = %s"

		cursor.execute(sql,(memberId,))
		data = cursor.fetchall()

		cursor.close()
		con.close()
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
		memberId = userInfo["id"]
		con = conPool.get_connection()
		cursor = con.cursor()
		
		sql = "SELECT bookingIdList, amount, contactName, contactEmail, contactPhone, statusCode, msg from orders WHERE memberId = %s and orderId = %s;"

		cursor.execute(sql,(memberId,orderNumber))
		data = cursor.fetchone()

		if len(data) == 0:
			cursor.close()
			con.close()
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
			sql = "SELECT booking.price, booking.date, booking.time, booking.attractionId, main.name, main.address, (SELECT GROUP_CONCAT(image.images) FROM image WHERE image.attraction_id = main.id) AS imagescombined FROM booking LEFT JOIN main ON booking.attractionId = main.id LEFT JOIN image ON booking.attractionId = image.attraction_id WHERE booking.memberId = %s AND booking.id = %s GROUP BY booking.id;"

			cursor.execute(sql,(memberId, bookingIdList[i]))
			attraction = cursor.fetchone()	

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

		cursor.close()
		con.close()
		return result, 200		

	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500
