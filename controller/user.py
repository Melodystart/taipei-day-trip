from model.user import UserModel
from view.user import UserView
import shutil
import os
import pathlib
from dotenv import get_key
import jwt
import requests
from flask import *

user = Blueprint('user',__name__)

key = get_key(".env", "key")

def error(result, message):
	result["error"] = True
	result["message"] = message
	return result

@user.route("/",methods=['POST'])
def signup():
	result = {}
	try:
		data = request.get_json()
		name, email, password = UserView.signup(data)

		if not name or not email or not password:
			return error(result,"註冊失敗：欄位皆為必填"), 400
		
		data = UserModel.check_signup(email)

		if data != None:
			return error(result,"註冊失敗：email已註冊過"), 400
		else:
			UserModel.signup(name, email, password)
			result["ok"] = True
			return result, 200

	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500

@user.route("/auth",methods=['PUT'])
def signin():
	result = {}
	try:
		data = request.get_json()
		email, password = UserView.signin(data)

		if not email or not password:
			return error(result,"登入失敗：欄位皆為必填"), 400

		data = UserModel.signin(email, password)

		if ( data == None):
			return error(result,"登入失敗：帳號或密碼錯誤"), 400
		else:
			payload = UserView.payload(data)
			result["token"] = jwt.encode(payload, key, algorithm="HS256")
			return result, 200

	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500

@user.route("/auth",methods=['GET'])
def getStatus():
	result = {}
	try:
		token = request.headers['Authorization'][7:]
		userInfo = jwt.decode(token, key, algorithms="HS256")
		userId = userInfo["id"]
		data = UserModel.check_signin(userId)
		result = UserView.signin_result(result, data, userId)
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

		UserModel.update_profile(name, email, password, file, memberId)

		result["ok"] = True
		return result, 200
		
	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500