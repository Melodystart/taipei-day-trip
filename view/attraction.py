from flask import *

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

class AttractionView:
  @staticmethod
  def attractions(result, data, page):
    if len(data) == 13:          #抓取資料為13筆，即下頁還有資料
      data.pop()                 #一頁為12筆，故去掉最後一個第13筆                    
      nextPage = page + 1
    else:
      nextPage = None            #抓取資料未達13筆，即下頁無資料
      
    result["nextPage"] = nextPage
    result["data"] = []
    for i in range(len(data)):
      result["data"].append(dataSetting(data[i]))

    return result

  @staticmethod
  def attraction(result, data):
    result["data"] = dataSetting(data)
    return result

  @staticmethod
  def mrts(result, data):
    result["data"] = []
    for i in range(len(data)):
      if (data[i][1] != None):
        result["data"].append(data[i][1])
    return result
