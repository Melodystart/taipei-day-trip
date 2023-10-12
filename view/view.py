from flask import *

view = Blueprint('view',__name__,
  static_folder="../public",
  static_url_path="/")

@view.route("/")
def index():
	return render_template("index.html")

@view.route("/attraction/<id>")
def attraction(id):
	return render_template("attraction.html")

@view.route("/booking")
def booking():
	return render_template("booking.html")

@view.route("/thankyou")
def thankyou():
	return render_template("thankyou.html")

@view.route("/orderlist")
def orderlist():
	return render_template("orderlist.html")

@view.route("/order")
def order():
	return render_template("order.html")
	
@view.route("/profile")
def profile():
	return render_template("profile.html")
