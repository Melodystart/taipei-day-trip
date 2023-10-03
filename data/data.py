import json
import mysql.connector

with open('taipei-attractions.json',encoding="utf-8") as f:
    original_data = json.load(f)

data = original_data["result"]["results"]

con = mysql.connector.connect(
    host='localhost',           
    user='root',                
    password='password',
)
cursor = con.cursor()

# 建立資料庫、table
cursor.execute("DROP database IF EXISTS attractions;")
cursor.execute("CREATE database attractions;")
cursor.execute("USE attractions;")
cursor.execute("CREATE table main (id BIGINT PRIMARY KEY NOT NULL,name VARCHAR(255),category VARCHAR(255),description TEXT,address TEXT,transport TEXT,mrt VARCHAR(255),lat DECIMAL(8,6),lng DECIMAL(9,6));")
cursor.execute("CREATE table image (id BIGINT PRIMARY KEY auto_increment,attraction_id BIGINT NOT NULL,images TEXT);")
cursor.execute("CREATE table member (id BIGINT PRIMARY KEY auto_increment,name VARCHAR(255) NOT NULL,password VARCHAR(255) NOT NULL,email VARCHAR(255) NOT NULL,time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP());")
cursor.execute("CREATE table booking (id BIGINT PRIMARY KEY auto_increment,memberId BIGINT NOT NULL,attractionId BIGINT NOT NULL,date DATE NOT NULL,time VARCHAR(255) NOT NULL, price SMALLINT NOT NULL, orderId VARCHAR(255), paymentStatus VARCHAR(255) NOT NULL DEFAULT '未付款');")
cursor.execute("CREATE table orders (id BIGINT PRIMARY KEY auto_increment, orderId VARCHAR(255) NOT NULL, memberId BIGINT NOT NULL, paymentStatus VARCHAR(255) NOT NULL, amount BIGINT NOT NULL, contactName VARCHAR(255) NOT NULL, contactEmail VARCHAR(255) NOT NULL, contactPhone VARCHAR(255) NOT NULL, statusCode BIGINT, msg VARCHAR(255), rec_trade_id VARCHAR(255));")
# 將資料存入MySQL
for i in range(len(data)):
# 圖片以外的資料存放table main
  cursor.execute("INSERT INTO main (id, name, category, description, address, transport, mrt, lat, lng) VALUES (%s, %s,%s, %s,%s, %s,%s, %s,%s)",(data[i]["_id"], data[i]["name"],data[i]["CAT"],data[i]["description"],data[i]["address"],data[i]["direction"],data[i]["MRT"],data[i]["latitude"],data[i]["longitude"]))
  con.commit()
# 圖片資料存放table image
  arr = data[i]["file"].lower().split('https://')
  for item in arr:
    if 'jpg' in item.lower() or 'png' in item.lower():
      item = 'https://' + item
      cursor.execute("INSERT INTO image (attraction_id, images) VALUES (%s, %s)",(data[i]["_id"], item))
      con.commit()

cursor.close()
con.close()
