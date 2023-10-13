from model.booking import BookingModel
from view.booking import BookingView
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
		attractionId, date, time, price = BookingView.attraction(data)

		if not memberId or not attractionId or not date or not time or not price or datetime.strptime(date, '%Y-%m-%d').date() <= datetime.today().date():
			return error(result,"建立失敗，輸入不正確(例：無法選今天及過去日期)或其他原因"), 400

		BookingModel.post_booking(memberId, attractionId, date, time, price)

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

		data = BookingModel.get_booking(memberId)

		result = BookingView.booking(result, data)
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

		BookingModel.delete_booking(memberId,bookingId)

		result["ok"] = True
		return result, 200

	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500