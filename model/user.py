from config import conPool
from flask import *

class UserModel:
	@staticmethod	
	def check_signup(email):
		con = conPool.get_connection()
		cursor = con.cursor()
		cursor.execute("SELECT email FROM member WHERE email=%s",(email,))
		data = cursor.fetchone()
		cursor.close()
		con.close()
		return data

	@staticmethod
	def signup(name, email, password):
		con = conPool.get_connection()
		cursor = con.cursor()			
		cursor.execute("INSERT INTO member (name, email, password) VALUES (%s, %s, %s)",(name, email, password))
		con.commit()
		cursor.close()
		con.close()

	@staticmethod
	def signin(email, password):
		con = conPool.get_connection()
		cursor = con.cursor()
		cursor.execute("SELECT id, name, email FROM member WHERE email=%s AND password=%s",(email, password))
		data = cursor.fetchone()
		cursor.close()
		con.close()
		return data

	@staticmethod
	def check_signin(userId):
		con = conPool.get_connection()
		cursor = con.cursor()
		sql = "SELECT name, email, filename from member WHERE id = %s"
		cursor.execute(sql,(userId,))
		data = cursor.fetchone()
		cursor.close()
		con.close()
		return data

	@staticmethod
	def update_profile(name, email, password, file, memberId):
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