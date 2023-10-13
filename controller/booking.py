from model.booking import Booking
from dotenv import get_key
import time
import jwt
from datetime import datetime, timedelta
import requests
from flask import *

booking = Blueprint('booking',__name__)

key = get_key(".env", "key")

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

		booking = Booking()
		booking.post_booking(memberId, attractionId, date, time, price)

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

		booking = Booking()
		data = booking.get_booking(memberId)

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

		booking = Booking()
		booking.delete_booking(memberId,bookingId)

		result["ok"] = True
		return result, 200

	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500