import mysql.connector
from mysql.connector import pooling
import math
from flask import *
app=Flask(
	__name__,
  static_folder="public",
  static_url_path="/"
	)
app.config["JSON_AS_ASCII"]=False
app.config["TEMPLATES_AUTO_RELOAD"]=True

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
			sql = "SELECT main.*, newimage.imagescombined FROM main LEFT JOIN (SELECT image.attraction_id, GROUP_CONCAT(image.images) AS imagescombined FROM image GROUP BY image.attraction_id) newimage ON main.id = newimage.attraction_id LIMIT %s, 13"

			cursor.execute(sql,(page*12,))
			data = cursor.fetchall()
			
		else:
			sql = "SELECT main.*, newimage.imagescombined FROM main LEFT JOIN (SELECT image.attraction_id, GROUP_CONCAT(image.images) AS imagescombined FROM image GROUP BY image.attraction_id) newimage ON main.id = newimage.attraction_id WHERE name LIKE %s OR mrt =%s LIMIT %s, 13"	

			cursor.execute(sql,("%"+ keyword +"%", keyword, page*12))
			data = cursor.fetchall()

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

		if len(data) == 13:          #抓取資料為13筆，即下頁還有資料
			data.pop()                 #一頁為12筆，故去掉最後一個第13筆                    
			nextPage = page + 1
		else:
			nextPage = None            #抓取資料未達13筆，即下頁無資料

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
			item["images"] = data[i][9].split(',')
			result["data"].append(item)
		response = make_response(result)
		response.headers["Content-Type"] = "application/json; charset=utf-8"
		return response, 200

	except Exception as e:
		result["error"] = True
		result["message"] = e.__class__.__name__+": "+str(e.args[0])
		return result, 500


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
		result["data"]["images"] = data[9].split(',')
		response = make_response(result)
		response.headers["Content-Type"] = "application/json; charset=utf-8"
		return response, 200

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

		cursor.execute("SELECT count(name) AS name_count, mrt FROM main GROUP BY mrt ORDER BY name_count DESC, CONVERT(SUBSTR(mrt,1,1) USING UTF8) DESC LIMIT 40;")
		data = cursor.fetchall()

		cursor.close()
		con.close()

		result["data"] = []
		for i in range(len(data)):
			if (data[i][1] != None):
				result["data"].append(data[i][1])
		response = make_response(result)
		response.headers["Content-Type"] = "application/json; charset=utf-8"
		return response, 200

	except Exception as e:
		result["error"] = True
		result["message"] = e.__class__.__name__+": "+str(e.args[0])
		return result, 500
	
app.run(host="0.0.0.0", port=3000)