from flask import *
from controller.attraction import attraction
from controller.user import user
from controller.order import order
from controller.booking import booking
from view.template import template

app=Flask(__name__)
app.config["JSON_AS_ASCII"]=False
app.config["TEMPLATES_AUTO_RELOAD"]=True

# Controller
app.register_blueprint(booking, url_prefix="/api/booking")
app.register_blueprint(user, url_prefix="/api/user")
app.register_blueprint(attraction)
app.register_blueprint(order)

# Temeplate
app.register_blueprint(template)

app.run(host="0.0.0.0", port=3000)