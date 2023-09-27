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
		return error(result, e.__class__.__name__+": "+str(e.args[0])), 500


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
		return error(result, e.__class__.__name__+": "+str(e.args[0])), 500

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
		return error(result, e.__class__.__name__+": "+str(e.args[0])), 500
	
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
		return error(result, e.__class__.__name__+": "+str(e.args[0])), 500

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
		return error(result, e.__class__.__name__+": "+str(e.args[0])), 500

@app.route("/api/user/auth",methods=['GET'])
def getStatus():
	result = {}
	result["data"] ={}
	try:
		token = request.headers['Authorization'][7:]
		userInfo = jwt.decode(token, key, algorithms="HS256")
		result["data"]["id"] = userInfo["id"]
		result["data"]["name"] = userInfo["name"]
		result["data"]["email"] = userInfo["email"]
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

		# cursor.execute("SELECT* FROM booking WHERE memberId=%s",(memberId,))
		# data = cursor.fetchone()

		# if data != None:
		# 	cursor.execute("DELETE FROM booking WHERE memberId=%s",(memberId,))
		# 	con.commit()

		cursor.execute("INSERT INTO booking (memberId, attractionId, date, time, price) VALUES (%s, %s, %s, %s, %s)",(memberId, attractionId, date, time, price))
		con.commit()

		cursor.close()
		con.close()

		result["ok"] = True
		return result, 200
		
	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e.args[0])), 500

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
		
		sql = "SELECT booking.attractionId,main.name, main.address, (SELECT GROUP_CONCAT(image.images) FROM image WHERE image.attraction_id = main.id) AS imagescombined, booking.date, booking.time, booking.price, booking.id FROM booking LEFT JOIN main ON booking.attractionId = main.id LEFT JOIN image ON booking.attractionId = image.attraction_id WHERE booking.memberId = %s GROUP BY booking.id"

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
		return error(result, e.__class__.__name__+": "+str(e.args[0])), 500

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
		return error(result, e.__class__.__name__+": "+str(e.args[0])), 500

app.run(host="0.0.0.0", port=3000)