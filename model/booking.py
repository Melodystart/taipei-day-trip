from config import conPool
from flask import *

class Booking:

	def get_booking(self, memberId):
		con = conPool.get_connection()
		cursor = con.cursor()
		
		sql = "SELECT booking.attractionId,main.name, main.address, (SELECT GROUP_CONCAT(image.images) FROM image WHERE image.attraction_id = main.id) AS imagescombined, booking.date, booking.time, booking.price, booking.id, booking.paymentStatus FROM booking LEFT JOIN main ON booking.attractionId = main.id LEFT JOIN image ON booking.attractionId = image.attraction_id WHERE booking.memberId = %s AND booking.paymentStatus = '未付款' GROUP BY booking.id"

		cursor.execute(sql,(memberId,))
		data = cursor.fetchall()

		cursor.close()
		con.close()
		return data


	def post_booking(self,memberId, attractionId, date, time, price):
		con = conPool.get_connection()
		cursor = con.cursor()

		cursor.execute("INSERT INTO booking (memberId, attractionId, date, time, price) VALUES (%s, %s, %s, %s, %s)",(memberId, attractionId, date, time, price))
		con.commit()

		cursor.close()
		con.close()


	def delete_booking(self, memberId,bookingId):
		con = conPool.get_connection()
		cursor = con.cursor()
		
		cursor.execute("DELETE FROM booking WHERE memberId=%s and id=%s",(memberId,bookingId))
		con.commit()

		cursor.close()
		con.close()

