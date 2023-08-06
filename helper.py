
from datetime import datetime, timedelta
from flask import redirect, render_template, session
from functools import wraps
from flask import make_response
import os
from flask_session import Session




WKHTMLTOPDF_PATH = '/usr/local/bin/wkhtmltopdf'

 
def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

# admin loging requirement
def login_admin_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") != 1:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function


def loadproduct(db, department):
    if department == "all":
        products = db.execute("select * from products")
    else:
        products = db.execute("select * from products where department = ?", department)
    return products


def loadorder(db, user_id):

    cart_id =db.execute("select * from carts where status != ?  and customer_id = ?",
                        "complete",
                        user_id)[0]["id"]
    orders = db.execute(
        "select * from orders join carts on carts.id = orders.cart_id join products on products.id = orders.product_id where status != ?  and (customer_id =? and cart_id = ?)",
        "complete",
        user_id,
        cart_id
    )
    total = db.execute(
        "select sum(cost)total , sum(units)total_units from orders join carts on carts.id=orders.cart_id where status != ? and customer_id = ?",
        "complete",
         user_id,
    )

    product_unit = db.execute(
        "select count(product_name)p_unit from orders join carts on carts.id = orders.cart_id where status != ? and customer_id = ? ",
        "complete",
        session["user_id"],
        )[0]["p_unit"]
    if len(orders) >= 1:
        orders[0]["total"] = total[0]["total"]
        orders[0]["total_units"] = total[0]["total_units"]
        orders[0]["product_units"] = product_unit
    else :
        orders={}

    return orders


def notification(db):
    notification = db.execute(
            "select  product_units from carts where customer_id = ? and id= ?",
             session["user_id"],
             session["cart_id"]
        )
    if len(notification) == 1:
        return notification[0]["product_units"]
    else:
        return 0



def createcart(db, user_id):
     customer = db.execute(
         "select * from customers where user_id = ? ",
         user_id)[0]
     cart = db.execute(
            "select * from carts where  status != ?  and customer_id = ?",
            "complete",
            user_id
            )
     if len(cart) == 0 :
          db.execute(
                "insert into carts (customer_id,customername,total_cost,product_units,total_units,address,date,status,comment) values (?,?,?,?,?,?,?,?,?)",
                user_id,
                customer["firstname"]+ " "+ customer["lastname"],
                0.00,
                0,
                0,
                customer["address"],
                datetime.today().date(),
                "pending",
                "open shoping cart"
                )
     return db.execute(
            "select * from carts where  status != ? and customer_id = ?",
            "complete",
            user_id
            )[0]["id"]


def usercart_id(db,user_id):
    cart_id = db.execute("select id from carts where status = ?  and customer_id = ?",
                        "submit",
                        user_id)[0]["id"]
    return cart_id



def updatecart(db,user_id):
      cart = loadorder(db,user_id)
      if len(cart) >= 1:
          db.execute(
            "update carts set total_cost = ?,total_units = ?, product_units =? where status = ? and customer_id =?",
            cart[0]["total"],
            cart[0]["total_units"],
            cart[0]["product_units"],
            "pending",
            user_id
                )
      else :
           db.execute(
            "update carts set total_cost = ?,total_units = ?, product_units =? where status = ? and customer_id =?",
            0,
            0,
            0,
            "pending",
            user_id
                )
      return 0


def customer_data(db,portal):
    data = db.execute("select * from  {}".format(portal))
    return data


def generate_delivery_date():
    date = datetime.today().date()
    day = datetime.today().weekday()
   
    if day <= 2 :
        delivery_day = "wenesday"
        due_date = date + timedelta(days=2-day)
    else:
        delivery_day = "sunday"
        due_date = date + timedelta(days=6-day)
    delivery_date = {}
    delivery_date["day"] = delivery_day
    delivery_date["date"] = due_date
    return delivery_date

def open_order_window():
    day = datetime.today().weekday()
    print(day)
    return ((day != 2) and (day != 6))



def add_recent_deliveries(db,date,day):

     carts_id = db.execute("select cart_id from deliveries join carts on deliveries.cart_id=carts.id  where (status =? or status= ?) and delivery_date =?","pending","submit",date)
     for cart_id in carts_id:
         db.execute("delete from deliveries where cart_id = ?", cart_id["cart_id"])

     carts = db.execute("select * from carts where (status = ? ) ", "submit")
     for cart in carts:
         db.execute(
                    "insert into deliveries (cart_id,customer_id,customername,delivery_address,delivery_date,delivery_day,note)VALUES(?,?,?,?,?,?,?)",
                    cart["id"],
                    cart["customer_id"],
                    cart["customername"],
                    cart["address"],
                    date,
                    day,
                    "due for delivery"
                    )
     return 0

def get_deliveries(db,date):
    return db.execute("select * from deliveries join carts on carts.id == deliveries.cart_id where delivery_date = ? ",date)

def get_delivery_dates(db):
    return db.execute("select delivery_date from deliveries group by delivery_date order by delivery_date DESC")

