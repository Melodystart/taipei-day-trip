from model.attraction import AttractionModel
from view.attraction import AttractionView
from dotenv import get_key
import requests
from flask import *

attraction = Blueprint('attraction',__name__)

key = get_key(".env", "key")

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

		data = AttractionModel.get_attractions(keyword, page)

		if len(data) == 0:
			return error(result,"page輸入非資料有效範圍內"), 500

		result = AttractionView.attractions(result, data, page)
		return responseWithHeaders(result), 200

	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500


@attraction.route("/api/attraction/<int:attractionId>",methods=['GET'])
def getAttraction(attractionId):
	result = {}
	try:

		data = AttractionModel.get_attraction(attractionId)

		if (data == None):
			return error(result,"景點編號不正確") , 400

		result = AttractionView.attraction(result, data)
		return responseWithHeaders(result), 200

	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500


@attraction.route("/api/mrts",methods=['GET'])
def getMrts():
	result = {}
	try:
		data = AttractionModel.get_mrts()
		result = AttractionView.mrts(result, data)
		return responseWithHeaders(result), 200

	except Exception as e:
		return error(result, e.__class__.__name__+": "+str(e)), 500
