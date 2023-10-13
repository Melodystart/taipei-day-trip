from flask import *
import time
from datetime import datetime, timedelta

class UserView:
  @staticmethod
  def signup(data):
    name = data['name'].strip()
    email = data['email'].strip()
    password = data['password'].strip()
    return name, email, password

  @staticmethod
  def signin(data):
    email = data["email"].strip()
    password = data["password"].strip()
    return email, password

  @staticmethod
  def payload(data):
    payload = {}
    payload["id"] = data[0]
    payload["name"] = data[1] 
    payload["email"] = data[2]
    payload["exp"] = datetime.utcnow() + timedelta(days=7)
    return payload

  @staticmethod
  def signin_result(result, data, userId):
    result["data"] ={}
    result["data"]["id"] = userId
    result["data"]["name"] = data[0]
    result["data"]["email"] = data[1]
    result["data"]["filename"] = data[2]
    return result