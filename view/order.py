from flask import *
import time

class OrderView:
  @staticmethod
  def ordering(userInfo, data):
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

    return memberId, prime, amount, contactName, contactEmail, contactPhone, bookingIdList, firstImage, transactionTime, transactionDate, orderId

  @staticmethod
  def payment_details(prime, partner_key, merchant_id, amount, orderId, contactPhone, contactName, contactEmail):
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
    return payment_details

  @staticmethod
  def payment_result(result, orderId, r):
    result["data"] = {}
    result["data"]["number"] = orderId
    result["data"]["payment"] = {}
    result["data"]["payment"]["status"] = r["status"]

    rec_status = r["status"]
    rec_msg = r["msg"]
    rec_trade_id = r["rec_trade_id"]

    return result, rec_status, rec_msg, rec_trade_id

  @staticmethod
  def orders(result, data):
    result["data"] = []

    if len(data) == 0:
      result["data"] = None
    else:
      for i in range(len(data)):
        item = {}
        item["orderId"] = data[i][0]
        item["transactionDate"] = data[i][1]
        item["paymentStatus"] = data[i][2]
        item["amount"] = data[i][3]
        item["msg"] = data[i][4]
        item["firstImage"] = data[i][5]
        result["data"].append(item)

    return result

  @staticmethod
  def order(result, data, orderNumber):
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
    return result

  @staticmethod
  def booking_in_order(attraction):
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
    return item
