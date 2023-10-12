from dotenv import get_key
import time
import mysql.connector
from mysql.connector import pooling
import math
from datetime import datetime, timedelta
import requests
from flask import *

attraction = Blueprint('attraction',__name__)

key = get_key(".env", "key")

conPool = pooling.MySQLConnectionPool(user= get_key(".env", "user"), password= get_key(".env", "password"), host='localhost', database='attractions', pool_name='attractionsConPool', pool_size=10)

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
	
@attraction.route("/api/attractions",methods=['GET'])
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


@attraction.route("/api/attraction/<int:attractionId>",methods=['GET'])
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

@attraction.route("/api/mrts",methods=['GET'])
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
