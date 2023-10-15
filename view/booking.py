from flask import *

class BookingView:
  @staticmethod
  def attraction(data):
    attractionId = data['attractionId']
    date = data['date']
    time = data['time']
    price = data['price']
    return attractionId, date, time, price

  @staticmethod
  def booking(result, data):
    result["data"] = []
    if len(data) == 0:
      result["data"] = None

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
      
    return result

