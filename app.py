import mysql.connector
from mysql.connector import pooling
import math
from flask import *
app=Flask(__name__)
app.config["JSON_AS_ASCII"]=False
app.config["TEMPLATES_AUTO_RELOAD"]=True

def getImages(id):
	con = conPool.get_connection()
	cursor = con.cursor()
	cursor.execute("SELECT images FROM main LEFT JOIN image on main.id = image.attraction_id WHERE main.id =%s",(int(id),))
	items = cursor.fetchall()
	cursor.close()
	con.close()

	images = []
	for item in items:
		images.append(item[0])
	return images

conPool = pooling.MySQLConnectionPool(user='root', password='password', host='localhost', database='attractions', pool_name='attractionsConPool', pool_size=10)

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

@app.route("/api/attractions",methods=['GET'])
def getPage():
	result = {}
	try:
		page = int(request.args.get("page", -1))
		keyword = request.args.get("keyword", None)

		if page < 0:
			result["error"] = True
			result["message"] = "page未輸入 或 page輸入非資料有效範圍內"
			return result, 500

		con = conPool.get_connection()
		cursor = con.cursor()

		if keyword == None:       #沒有給定關鍵字則不做篩選
			cursor.execute("SELECT * FROM main LIMIT %s, 12",(page*12,))
			data = cursor.fetchall()

			cursor.execute("SELECT * FROM main LIMIT %s, 12",(page*12+12,))
			nextData = cursor.fetchall()
			
		else:                     #關鍵字完全比對捷運站名稱
			cursor.execute("SELECT * FROM main WHERE mrt =%s LIMIT %s, 12",(keyword, page*12))
			data = cursor.fetchall()

			cursor.execute("SELECT * FROM main WHERE mrt =%s LIMIT %s, 12",(keyword, page*12+12))
			nextData = cursor.fetchall()
			if len(data) == 0:      #關鍵字模糊比對景點名稱
				cursor.execute("SELECT * FROM main WHERE name LIKE %s LIMIT %s, 12",("%"+ keyword +"%", page*12))
				data = cursor.fetchall()

				cursor.execute("SELECT * FROM main WHERE name LIKE %s LIMIT %s, 12",("%"+ keyword +"%", page*12+12))
				nextData = cursor.fetchall()

				if (len(data) == 0) & (page == 0):
					result["error"] = True
					result["message"] = "找不到符合keyword資料"
					return result, 500

		cursor.close()
		con.close()

		if len(data) == 0:
			result["error"] = True
			result["message"] = "page輸入非資料有效範圍內"
			return result, 500

		nextPage = page + 1
		if len(nextData) == 0: 
			nextPage = None

		result["nextPage"] = nextPage
		result["data"] = []

		for i in range(len(data)):
			item = {}
			item["id"] = data[i][0]
			item["name"] = data[i][1] 
			item["category"] = data[i][2]
			item["description"] = data[i][3]
			item["address"] = data[i][4]	
			item["transport"] = data[i][5]	
			item["mrt"] = data[i][6]	    
			item["lat"] = data[i][7]
			item["lng"] = data[i][8]	
			item["images"] = getImages(data[i][0])	
			result["data"].append(item)
		return result, 200

	except Exception as e:
		result["error"] = True
		result["message"] = e.__class__.__name__+": "+e.args[0]
		return result, 500


@app.route("/api/attraction/<int:attractionId>",methods=['GET'])
def getAttraction(attractionId):
	result = {}
	try:
		con = conPool.get_connection()
		cursor = con.cursor()

		cursor.execute("SELECT * FROM main WHERE id =%s",(attractionId,))
		data = cursor.fetchone()

		cursor.close()
		con.close()

		if (data == None):
			result["error"] = True
			result["message"] = "景點編號不正確"
			return result, 400

		result["data"] = {}
		result["data"]["id"] = data[0]
		result["data"]["name"] = data[1] 
		result["data"]["category"] = data[2]
		result["data"]["description"] = data[3]
		result["data"]["address"] = data[4]	
		result["data"]["transport"] = data[5]	
		result["data"]["mrt"] = data[6]	    
		result["data"]["lat"] = data[7]
		result["data"]["lng"] = data[8]	
		result["data"]["images"] = getImages(data[0])	
		return result, 200

	except Exception as e:
		result["error"] = True
		result["message"] = e.__class__.__name__+": "+str(e.args[0])
		return result, 500

@app.route("/api/mrts",methods=['GET'])
def getMrts():
	result = {}
	try:
		con = conPool.get_connection()
		cursor = con.cursor()

		cursor.execute("SELECT count(name) AS name_count, mrt FROM main GROUP BY mrt ORDER BY name_count DESC LIMIT 40;")
		data = cursor.fetchall()

		cursor.close()
		con.close()

		result["data"] = []
		for i in range(len(data)):
			result["data"].append(data[i][1])
		return result, 200

	except Exception as e:
		result["error"] = True
		result["message"] = e.__class__.__name__+": "+e.args[0]
		return result, 500
	
app.run(host="0.0.0.0", port=3000)