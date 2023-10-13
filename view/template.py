from flask import *

template = Blueprint('template',__name__,
  static_folder="../public",
  static_url_path="/")

@template.route("/")
def index():
	return render_template("index.html")

@template.route("/attraction/<id>")
def attraction(id):
	return render_template("attraction.html")

@template.route("/booking")
def booking():
	return render_template("booking.html")

@template.route("/thankyou")
def thankyou():
	return render_template("thankyou.html")

@template.route("/orderlist")
def orderlist():
	return render_template("orderlist.html")

@template.route("/order")
def order():
	return render_template("order.html")
	
@template.route("/profile")
def profile():
	return render_template("profile.html")
