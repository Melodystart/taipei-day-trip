from config import conPool
from flask import *

class OrderModel:
	@staticmethod
	def check_payment_status(bookingId):
		con = conPool.get_connection()
		cursor = con.cursor()
		cursor.execute("SELECT * FROM booking WHERE paymentStatus=%s AND id=%s",("已付款",bookingId))
		data = cursor.fetchone()
		cursor.close()
		con.close()
		return data

	@staticmethod
	def create(orderId, memberId, amount, contactName,contactEmail, contactPhone, bookingIds, transactionDate, firstImage):
		con = conPool.get_connection()
		cursor = con.cursor()
		cursor.execute("INSERT INTO orders (orderId,memberId, paymentStatus, amount, contactName, contactEmail, contactPhone, bookingIdList, transactionDate, firstImage) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",(orderId, memberId, "未付款", amount, contactName,contactEmail, contactPhone, bookingIds, transactionDate, firstImage))
		con.commit()
		cursor.close()
		con.close()

	@staticmethod
	def record_number_tobooking(orderId, bookingId, memberId):
		con = conPool.get_connection()
		cursor = con.cursor()				
		cursor.execute("UPDATE booking set orderId=%s WHERE id = %s and memberId= %s",(orderId, bookingId, memberId))
		con.commit()
		cursor.close()
		con.close()

	@staticmethod
	def record_payment_tobooking(bookingId, memberId):
		con = conPool.get_connection()
		cursor = con.cursor()
		cursor.execute("UPDATE booking set paymentStatus=%s WHERE id = %s and memberId= %s",('已付款', bookingId, memberId))
		con.commit()
		cursor.close()
		con.close()

	@staticmethod
	def record_payment(result ,rec_status, rec_msg, rec_trade_id, orderId, memberId):
		con = conPool.get_connection()
		cursor = con.cursor()
		cursor.execute("UPDATE orders set paymentStatus=%s, statusCode=%s, msg=%s, rec_trade_id =%s WHERE orderId = %s and memberId= %s",(result, rec_status, rec_msg, rec_trade_id, orderId, memberId))
		con.commit()				
		cursor.close()
		con.close()

	@staticmethod
	def record_payment_failure(rec_status, rec_msg, rec_trade_id, orderId, memberId):
		con = conPool.get_connection()
		cursor = con.cursor()
		cursor.execute("UPDATE orders set statusCode=%s, msg=%s, rec_trade_id =%s WHERE orderId = %s and memberId= %s",(rec_status, rec_msg, rec_trade_id, orderId, memberId))
		con.commit()
		cursor.close()
		con.close()

	@staticmethod	
	def get_orders(memberId):
		con = conPool.get_connection()
		cursor = con.cursor()
		sql = "SELECT orderId, transactionDate, paymentStatus, amount,  msg, firstImage from orders WHERE memberId = %s"
		cursor.execute(sql,(memberId,))
		data = cursor.fetchall()
		cursor.close()
		con.close()
		return data

	@staticmethod
	def get_order(memberId, orderNumber):
		con = conPool.get_connection()
		cursor = con.cursor()
		sql = "SELECT bookingIdList, amount, contactName, contactEmail, contactPhone, statusCode, msg from orders WHERE memberId = %s and orderId = %s;"
		cursor.execute(sql,(memberId, orderNumber))
		data = cursor.fetchone()
		cursor.close()
		con.close()
		return data

	@staticmethod	
	def get_order_booking(memberId, bookingId):
		con = conPool.get_connection()
		cursor = con.cursor()
		sql = "SELECT booking.price, booking.date, booking.time, booking.attractionId, main.name, main.address, (SELECT GROUP_CONCAT(image.images) FROM image WHERE image.attraction_id = main.id) AS imagescombined FROM booking LEFT JOIN main ON booking.attractionId = main.id LEFT JOIN image ON booking.attractionId = image.attraction_id WHERE booking.memberId = %s AND booking.id = %s GROUP BY booking.id;"
		cursor.execute(sql,(memberId, bookingId))
		attraction = cursor.fetchone()	
		cursor.close()
		con.close()
		return attraction
