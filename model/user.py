import shutil
import os
import pathlib
from dotenv import get_key
import time
import mysql.connector
from mysql.connector import pooling
import math
import jwt
from datetime import datetime, timedelta
import requests
from flask import *

user = Blueprint('user',__name__)

key = get_key(".env", "key")

conPool = pooling.MySQLConnectionPool(user= get_key(".env", "user"), password= get_key(".env", "password"), host='localhost', database='attractions', pool_name='attractionsConPool', pool_size=10)

def error(result, message):
	result["error"] = True
	result["message"] = message
	return result

@user.route("/",methods=['POST'])
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

@user.route("/auth",methods=['PUT'])
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

@user.route("/auth",methods=['GET'])
def getStatus():
	result = {}
	result["data"] ={}
	try:
		token = request.headers['Authorization'][7:]
		userInfo = jwt.decode(token, key, algorithms="HS256")

		con = conPool.get_connection()
		cursor = con.cursor()
		sql = "SELECT name, email, filename from member WHERE id = %s"
		cursor.execute(sql,(userInfo["id"],))
		data = cursor.fetchone()
		cursor.close()
		con.close()

		result["data"]["id"] = userInfo["id"]
		result["data"]["name"] = data[0]
		result["data"]["email"] = data[1]
		result["data"]["filename"] = data[2]
		return result, 200		

	except:
		result["data"] = None
		return result, 200

@user.route("/profile",methods=['PUT'])
def updatingProfile():
	result = {}
	try:
		token = request.headers['Authorization'][7:]
		userInfo = jwt.decode(token, key, algorithms="HS256")
	except:
		return error(result,"未登入系統，拒絕存取"), 403

	try:
		try:
			file = request.files['file']
		except:
			file = None
		name = request.form['name']
		email = request.form['email']
		password = request.form.get('password')

		if not name or not email:
			return error(result,"建立失敗，名字與email為資料更新必填欄位"), 400

		memberId = userInfo["id"]

		if file != None:
			# 取得目前檔案所在的資料夾 
			SRC_PATH =  pathlib.Path(__file__).parent.parent.absolute()
			# 結合目前的檔案路徑和uploads路徑
			UPLOAD_FOLDER = os.path.join(SRC_PATH,  'public','uploads' ,str(memberId))
			if not os.path.isdir(UPLOAD_FOLDER):
				os.mkdir(UPLOAD_FOLDER)
			else:
				shutil.rmtree(UPLOAD_FOLDER)
				os.mkdir(UPLOAD_FOLDER)
			file.save(os.path.join(UPLOAD_FOLDER, file.filename))

		con = conPool.get_connection()
		cursor = con.cursor()

		if password != None and file != None:
			cursor.execute("UPDATE member set name=%s, email=%s, password=%s, filename=%s WHERE id = %s",(name, email, password, file.filename, memberId))
			con.commit()
		elif password != None and file == None:
			cursor.execute("UPDATE member set name=%s, email=%s, password=%s WHERE id = %s",(name, email, password, memberId))
			con.commit()
		elif password == None and file != None:
			cursor.execute("UPDATE member set name=%s, email=%s, filename=%s WHERE id = %s",(name, email, file.filename, memberId))
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