from flask import *
from model.attraction import attraction
from model.user import user
from model.order import order
from model.booking import booking
from view.view import view

app=Flask(__name__)
app.config["JSON_AS_ASCII"]=False
app.config["TEMPLATES_AUTO_RELOAD"]=True

# Model
app.register_blueprint(booking, url_prefix="/api/booking")
app.register_blueprint(user, url_prefix="/api/user")
app.register_blueprint(attraction)
app.register_blueprint(order)

# View
app.register_blueprint(view)

app.run(host="0.0.0.0", port=3000)