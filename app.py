import time
import mysql.connector
from mysql.connector import pooling
import math
import jwt
from datetime import datetime, timedelta
import requests
from flask import *
app=Flask(
	__name__,
  static_folder="public",
  static_url_path="/"
	)
app.config["JSON_AS_ASCII"]=False
app.config["TEMPLATES_AUTO_RELOAD"]=True
key = "secret"

conPool = pooling.MySQLConnectionPool(user='root', password='password', host='localhost', database='attractions', pool_name='attractionsConPool', pool_size=10)

def dataSetting(data):
  dict = {}
  dict["id"] = data[0]
  dict["name"] = data[1]
  dict["category"] = data[2]
  dict["description"] = data[3]
  dict["address"] = data[4]
  dict["transport"] = data[5]
  dict["mrt"] = data[6]
  dict["lat"] = data[7]
  dict["lng"] = data[8]
  dict["images"] = data[9].split(',')
  return dict

def error(result, message):
	result["error"] = True
	result["message"] = message
	return result

def responseWithHeaders(result):
	response = make_response(result)  #在需要設定headers可用make_response
	response.headers["Content-Type"] = "application/json; charset=utf-8"
	return response
	
# Pages
@app.route("/")
def index():
	return render_template("index.html")
@app.route("/attraction/<id>")
def attraction(id):
	return render_template("attraction.html")
@app.route("/booking")
def booking():
	return render_template("booking.html")
@app.route("/thankyou")
def thankyou():
	return render_template("thankyou.html")
@app.route("/orderlist")
def orderlist():
	return render_template("orderlist.html")
@app.route("/order")
def order():
	return render_template("order.html")
@app.route("/profile")
def profile():
	return render_template("profile.html")
# API
@app.route("/api/attractions",methods=['GET'])
def getPage():
	result = {}
	try:
		page = int(request.args.get("page", -1))
		keyword = request.args.get("keyword", None)

		if page < 0:
			return error(result, "page未輸入 或 page輸入非資料有效範圍內"), 500

		con = conPool.get_connection()
		cursor = con.cursor()

		if keyword == None:       #沒有給定關鍵字則不做篩選
			sql = "SELECT main.*, newimage.imagescombined FROM main LEFT JOIN (SELECT image.attraction_id, GROUP_CONCAT(image.images) AS imagescombined FROM image GROUP BY image.attraction_id) newimage ON main.id = newimage.attraction_id LIMIT %s, 13"

			cursor.execute(sql,(page*12,))
			data = cursor.fetchall()
			
		else:
			sql = "SELECT main.*, newimage.imagescombined FROM main LEFT JOIN (SELECT image.attraction_id, GROUP_CONCAT(image.images) AS imagescombined FROM image GROUP BY image.attraction_id) newimage ON main.id = newimage.attraction_id WHERE name LIKE %s OR mrt =%s LIMIT %s, 13"	

			cursor.execute(sql,("%"+ keyword +"%", keyword, page*12))
			data = cursor.fetchall()

			if (len(data) == 0) & (page == 0):
				return error(result,"找不到符合keyword資料") , 500

		cursor.close()
		con.close()

		if len(data) == 0:
			return error(result,"page輸入非資料有效範圍內"), 500

		if len(data) == 13:          #抓取資料為13筆，即下頁還有資料
			data.pop()                 #一頁為12筆，故去掉最後一個第13筆                    
			nextPage = page + 1
		else:
			nextPage = None            #抓取資料未達13筆，即下頁無資料

		result["nextPage"] = nextPage
		result["data"] = []

		for i in range(len(data)):
			result["data"].append(dataSetting(data[i]))
			
		return responseWithHeaders(result), 200

	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500


@app.route("/api/attraction/<int:attractionId>",methods=['GET'])
def getAttraction(attractionId):
	result = {}
	try:
		con = conPool.get_connection()
		cursor = con.cursor()
		
    #group_concat預設1024 character length, 若做較長的查詢，需增加以下暫時性length設定
		cursor.execute("SET SESSION group_concat_max_len = 1000000;")
		sql = "SELECT main.*, newimage.imagescombined FROM main LEFT JOIN (SELECT image.attraction_id, GROUP_CONCAT(image.images) AS imagescombined FROM image GROUP BY image.attraction_id) newimage ON main.id = newimage.attraction_id WHERE id =%s"	

		cursor.execute(sql,(attractionId,))
		data = cursor.fetchone()

		cursor.close()
		con.close()

		if (data == None):
			return error(result,"景點編號不正確") , 400

		result["data"] = dataSetting(data)
		return responseWithHeaders(result), 200

	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500

@app.route("/api/mrts",methods=['GET'])
def getMrts():
	result = {}
	try:
		con = conPool.get_connection()
		cursor = con.cursor()

		cursor.execute("SELECT count(name) AS name_count, mrt FROM main GROUP BY mrt ORDER BY name_count DESC, CONVERT(SUBSTR(mrt,1,1) USING UTF8) DESC LIMIT 40;")
		data = cursor.fetchall()

		cursor.close()
		con.close()

		result["data"] = []
		for i in range(len(data)):
			if (data[i][1] != None):
				result["data"].append(data[i][1])		
		return responseWithHeaders(result), 200

	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500
	
@app.route("/api/user",methods=['POST'])
def signup():
	result = {}
	try:
		data = request.get_json()
		name = data['name'].strip()
		email = data['email'].strip()
		password = data['password'].strip()

		if not name or not email or not password:
			return error(result,"註冊失敗：欄位皆為必填"), 400
		
		con = conPool.get_connection()
		cursor = con.cursor()

		cursor.execute("SELECT email FROM member WHERE email=%s",(email,))
		data = cursor.fetchone()

		if data != None:
			cursor.close()
			con.close()
			return error(result,"註冊失敗：email已註冊過"), 400
		else:
			cursor.execute("INSERT INTO member (name, email, password) VALUES (%s, %s, %s)",(name, email, password))
			con.commit()
			cursor.close()
			con.close()

			result["ok"] = True
			return result, 200

	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500

@app.route("/api/user/auth",methods=['PUT'])
def signin():
	result = {}
	try:
		data = request.get_json()
		email = data["email"].strip()
		password = data["password"].strip()

		if not email or not password:
			return error(result,"登入失敗：欄位皆為必填"), 400

		con = conPool.get_connection()
		cursor = con.cursor()

		cursor.execute("SELECT id, name, email FROM member WHERE email=%s AND password=%s",(email, password))
		data = cursor.fetchone()

		cursor.close()
		con.close()

		if ( data == None):
			return error(result,"登入失敗：帳號或密碼錯誤"), 400
		else:
			payload = {}
			payload["id"] = data[0]
			payload["name"] = data[1] 
			payload["email"] = data[2]
			payload["exp"] = datetime.utcnow() + timedelta(days=7)

			result["token"] = jwt.encode(payload, key, algorithm="HS256")
			return result, 200

	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500

@app.route("/api/user/auth",methods=['GET'])
def getStatus():
	result = {}
	result["data"] ={}
	try:
		token = request.headers['Authorization'][7:]
		userInfo = jwt.decode(token, key, algorithms="HS256")

		con = conPool.get_connection()
		cursor = con.cursor()
		sql = "SELECT name, email from member WHERE id = %s"
		cursor.execute(sql,(userInfo["id"],))
		data = cursor.fetchone()
		cursor.close()
		con.close()

		result["data"]["id"] = userInfo["id"]
		result["data"]["name"] = data[0]
		result["data"]["email"] = data[1] 
		return result, 200		

	except:
		result["data"] = None
		return result, 200

@app.route("/api/booking",methods=['POST'])
def bookingAPI():
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

		if not memberId or not attractionId or not date or not time or not price:
			return error(result,"建立失敗，輸入不正確或其他原因"), 400

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

@app.route("/api/booking",methods=['GET'])
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

@app.route("/api/booking",methods=['DELETE'])
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

@app.route("/api/orders",methods=['POST'])
def orders():
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

			if not memberId or not prime or not amount or not contactName or not contactEmail or not contactPhone or not bookingIdList or not orderId:
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

		partner_key = 'partner_NqF3u1pTphB2ariDyIUM6Pl4n6ghMkHB0sVgbiwkVsN9WsFYBwVKRdWN'
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

@app.route("/api/orders",methods=['GET'])
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

@app.route("/api/order/<int:orderNumber>",methods=['GET'])
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
		#待研究：下面查詢只會跑出第一個而無法跑出全部的booking(1,2)，先改成下方以迴圈方式跑出全部的booking
		# sql = "SELECT booking.price, booking.date, booking.time, booking.attractionId, main.name, main.address, (SELECT GROUP_CONCAT(image.images) FROM image WHERE image.attraction_id = main.id) AS imagescombined FROM booking LEFT JOIN main ON booking.attractionId = main.id LEFT JOIN image ON booking.attractionId = image.attraction_id WHERE booking.memberId = %s AND booking.id IN (%s) GROUP BY booking.id;"

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

@app.route("/api/profile",methods=['PUT'])
def updateProfile():
	result = {}
	try:
		token = request.headers['Authorization'][7:]
		userInfo = jwt.decode(token, key, algorithms="HS256")
	except:
		return error(result,"未登入系統，拒絕存取"), 403

	try:
		data = request.get_json()
		name = data['name']
		email = data['email']

		if not name or not email:
			return error(result,"建立失敗，名字與email為資料更新必填欄位"), 400

		memberId = userInfo["id"]
		con = conPool.get_connection()
		cursor = con.cursor()

		if len(data) == 3:
			password = data['password']
			cursor.execute("UPDATE member set name=%s, email=%s, password=%s WHERE id = %s",(name, email, password, memberId))
			con.commit()
		else:
			cursor.execute("UPDATE member set name=%s, email=%s WHERE id = %s",(name, email, memberId))
			con.commit()			

		cursor.close()
		con.close()

		result["ok"] = True
		return result, 200
		
	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500

# @app.route("/api/profile",methods=['GET'])
# def getProfile():
# 	result = {}
# 	try:
# 		token = request.headers['Authorization'][7:]
# 		userInfo = jwt.decode(token, key, algorithms="HS256")
# 	except:
# 		return error(result,"未登入系統，拒絕存取"), 403

	# try:
		# memberId = userInfo["id"]
		# con = conPool.get_connection()
		# cursor = con.cursor()
		
		# sql = "SELECT name, email, password from member WHERE memberId = %s"

		# cursor.execute(sql,(memberId,))
		# data = cursor.fetchall()

		# cursor.close()
		# con.close()
		# result["data"] = {}

	# 	if len(data) == 0:
	# 		result["data"] = None
	# 		return result, 200


	# 	return result, 200		

	# except Exception as e:
	# 	return error(result, e.__class__.__name__+": "+str(e)), 500

app.run(host="0.0.0.0", port=3000)