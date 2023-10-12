from dotenv import get_key
import time
import mysql.connector
from mysql.connector import pooling
import math
import jwt
from datetime import datetime, timedelta
import requests
from flask import *

booking = Blueprint('booking',__name__)

key = get_key(".env", "key")

conPool = pooling.MySQLConnectionPool(user= get_key(".env", "user"), password= get_key(".env", "password"), host='localhost', database='attractions', pool_name='attractionsConPool', pool_size=10)

def error(result, message):
	result["error"] = True
	result["message"] = message
	return result
	
@booking.route("/",methods=['POST'])
def bookingAttraction():
	result = {}
	try:
		try:
			token = request.headers['Authorization'][7:]
			userInfo = jwt.decode(token, key, algorithms="HS256")
		except:
			return error(result,"未登入系統，拒絕存取"), 403

		data = request.get_json()
		memberId = userInfo["id"]
		attractionId = data['attractionId']
		date = data['date']
		time = data['time']
		price = data['price']

		if not memberId or not attractionId or not date or not time or not price or datetime.strptime(date, '%Y-%m-%d').date() <= datetime.today().date():
			return error(result,"建立失敗，輸入不正確(例：無法選今天及過去日期)或其他原因"), 400

		con = conPool.get_connection()
		cursor = con.cursor()

		cursor.execute("INSERT INTO booking (memberId, attractionId, date, time, price) VALUES (%s, %s, %s, %s, %s)",(memberId, attractionId, date, time, price))
		con.commit()

		cursor.close()
		con.close()

		result["ok"] = True
		return result, 200
		
	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500

@booking.route("/",methods=['GET'])
def getBooking():
	result = {}
	try:
		try:
			token = request.headers['Authorization'][7:]
			userInfo = jwt.decode(token, key, algorithms="HS256")
		except:
			return error(result,"未登入系統，拒絕存取"), 403

		memberId = userInfo["id"]
		con = conPool.get_connection()
		cursor = con.cursor()
		
		sql = "SELECT booking.attractionId,main.name, main.address, (SELECT GROUP_CONCAT(image.images) FROM image WHERE image.attraction_id = main.id) AS imagescombined, booking.date, booking.time, booking.price, booking.id, booking.paymentStatus FROM booking LEFT JOIN main ON booking.attractionId = main.id LEFT JOIN image ON booking.attractionId = image.attraction_id WHERE booking.memberId = %s AND booking.paymentStatus = '未付款' GROUP BY booking.id"

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
			item["attraction"] = {}
			item["attraction"]["id"] = data[i][0]
			item["attraction"]["name"] = data[i][1]
			item["attraction"]["address"] = data[i][2]
			item["attraction"]["image"] = data[i][3].split(',')[0]
			item["date"] = data[i][4]
			item["time"] = data[i][5]
			item["price"] = data[i][6]
			item["bookingId"] = data[i][7]
			result["data"].append(item)
		return result, 200		

	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500

@booking.route("/",methods=['DELETE'])
def deleteBooking():
	result = {}
	try:
		try:
			token = request.headers['Authorization'][7:]
			userInfo = jwt.decode(token, key, algorithms="HS256")
		except:
			return error(result,"未登入系統，拒絕存取"), 403

		data = request.get_json()
		bookingId = data["bookingId"]
		memberId = userInfo["id"]
		con = conPool.get_connection()
		cursor = con.cursor()
		
		cursor.execute("DELETE FROM booking WHERE memberId=%s and id=%s",(memberId,bookingId))
		con.commit()

		cursor.close()
		con.close()

		result["ok"] = True
		return result, 200

	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500
