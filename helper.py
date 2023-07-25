import csv
import datetime
import pytz
import requests
import subprocess
import urllib
import uuid


from flask import redirect, render_template, session
from functools import wraps


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

    cart_id =db.execute("select * from carts where status= ? and customer_id = ?",
                        "pending",
                        user_id)[0]["id"]
    orders = db.execute(
        "select * from orders join carts on carts.id = orders.cart_id join products on products.id = orders.product_id where status= ? and (customer_id =? and cart_id = ?)",
        "pending",
        user_id,
        cart_id
    )
    total = db.execute(
        "select sum(cost)total , sum(units)total_units from orders join carts on carts.id=orders.cart_id where status = ? and customer_id = ?",
        "pending",
         user_id,
    )

    product_unit = db.execute(
        "select count(product_name)p_unit from orders join carts on carts.id = orders.cart_id where status= ? and customer_id = ? ",
        "pending",
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
            "select  product_units from carts where customer_id = ? and status= ?",
             session["user_id"],
             "pending"
        )
    if len(notification) == 1:
        return notification[0]["product_units"]
    else:
        return 0



def createcart(db, user_id,date):
     customer = db.execute(
         "select * from customers where user_id = ? ",
         user_id)[0]
     cart = db.execute(
            "select * from carts where  status = ?  and customer_id = ?",
            "pending",
            user_id
            )
     if len(cart) == 0 :
          db.execute(
                "insert into carts (customer_id,customername,total_cost,product_units,total_units,address,date,status) values (?,?,?,?,?,?,?,?)",
                session["user_id"],
                customer["firstname"]+ " "+ customer["lastname"],
                0.00,
                0,
                0,
                customer["address"],
                date,
                "pending"
                )
     return 0


def usercart_id(db,user_id):
    cart_id =db.execute("select * from carts where status= ? and customer_id = ?",
                        "pending",
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