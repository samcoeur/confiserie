from flask import Flask
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from cs50 import SQL
from datetime import datetime
from helper import loadproduct, login_required , loadorder , notification , login_admin_required, createcart,usercart_id ,updatecart

# db
app = Flask(__name__)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///product.db")



app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

Session(app)



@app.route("/", methods=["GET","POST"])
def index():
    session["day"] = datetime.now().strftime('%A') + " "
    session["today"] = datetime.today().date()
    if request.method == "POST":
        department = request.form.get("department").lower()
        products=loadproduct(db,department)
        return render_template("layout.html", products=products,  message="Select a product")
    products = db.execute("select * from products")
    if session.get("user_id") != 1:
        return render_template("layout.html", products=products)
    else :
        return render_template("layout.html", products=products, cart_notification = notification(db))




@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        phonenumber = request.form.get("phone_number")
        email = request.form.get("email")
        gender = request.form.get("gender")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if password != confirmation:
            flash("password and confirmation dont match")
            return redirect("/register")
        if (db.execute("select username from users where username = ?", username)) == 1:
            flash("username exists already")
            return redirect("/register")
        db.execute(
            "insert into users (username,hash,email) values(?,?,?)",
            username,
            generate_password_hash(password),
            email,
        )
        session["user_id"] = db.execute(
            "select id from users where username = ? ", username
        )[0]["id"]
        # log in customers infos
        db.execute(
            "insert into customers (user_id,firstname,lastname,gender,phone_number,address,business_name) values(?,?,?,?,?,?,?)",
            session["user_id"],
            firstname,
            lastname,
            gender,
            phonenumber,
            "home address",
            "My business"
           )
        session["username"] = username
        session["firstname"] = firstname
        session["day"] = datetime.now().weekday()
        createcart(db,session["user_id"],datetime.today())
        flash("successfully registered")
        return redirect("/")
    else:
        return render_template("form.html", register="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        rows = db.execute("select * from users where username = ?", username)
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            flash("invalid username or password")
            return redirect("/login")
        session["user_id"] = db.execute(
            "select id from users where username = ?", username
        )[0]["id"]
        session["username"] = username
        session["firstname"] = db.execute(
            "select firstname from customers where user_id = ?", session["user_id"]
        )[0]["firstname"]
        # create an empty cart for customer upon sign in if he doest have one
        createcart(db,session["user_id"],datetime.today())

        flash("sucessfully logged in Welcome")
        return redirect("/")
    else:
        flash("must have an account to place your order !!!")
        return render_template("form.html", login="go")


@app.route("/logout")
def logout():
    session.clear()
    flash("thanks for your visit")
    return redirect("/login")


@app.route("/select", methods=["GET", "POST"])
@login_required
def select():
    if request.method == "POST":
        action = request.form.get("action")
        product_id = request.form.get("product_id")
        units = request.form.get("units")
        cost = request.form.get("cost")
        select = db.execute("select * from products where id = ? " , product_id)
        select[0]["units"] = units
        select[0]["cost"] = cost
        if action == "remove" :
            db.execute("delete from orders  where  product_id = ? and cart_id =? " ,
                            product_id,
                            usercart_id(db,session["user_id"]))
            updatecart(db,session["user_id"])
            return redirect("/cart")


        order = db.execute("select * from orders join carts on carts.id = orders.cart_id where status = ? and (product_id = ? and customer_id = ?) " ,
                            "pending",
                            product_id,
                            session["user_id"])
        if len(order) == 0:
                return render_template("order.html",cart_notification = notification(db), select = select[0])
        else:
                order[0]["img_name"] = select[0]["img_name"]
                order[0]["price"] = select[0]["price"]
                order[0]["id"] = select[0]["id"]
                order[0]["name"] = select[0]["name"]
                return render_template("order.html",cart_notification = notification(db), select = order[0])

    else:
        return redirect("/")



@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        product_id = request.form.get("product_id")
        print(product_id)
        total = request.form.get("total")
        units = request.form.get("units")
        department= request.form.get("department")
        select = db.execute("select * from products where id = ?", product_id)
        select[0]["units"] = units
        try:
            units = int(units)
        except ValueError:
            flash("wrong entry")
            return redirect("/")
        if units <= 0 or units > 20:
            if units > 20:
                flash("order exceeds the 20 units limits")
            else:
                flash("wrong entery units")
            select[0]["units"] = 0 ;
            return render_template("order.html", select=select[0])
        # get the units in stock of the product
        units_in_stock = db.execute("select (stock_units) from products where id = ?" , product_id)[0]["stock_units"]
        if units > units_in_stock:
            flash(" not anought units in stock ")
            return render_template("order.html", select=select[0])

        # we check if the product has been already added by the customer
        cart_id = db.execute(
            "select * from carts where status = ? and customer_id = ?",
            "pending",
            session["user_id"])[0]["id"]
        order =db.execute("select * from orders join carts on carts.id = orders.cart_id where status = ? and (product_id = ? and customer_id = ?) ","pending", product_id, session["user_id"])
        if len(order) == 1 :
            db.execute(
                "update  orders  set units = ? , cost = ? where  product_id = ? and cart_id =?",
                units,
                round(float(total),2),
                product_id,
                cart_id
            )
        else:
            db.execute(
            "insert into orders (cart_id , product_id, product_name, units ,cost) VALUES(?,?,?,?,?)",
            cart_id,
            product_id,
            select[0]["name"],
            units,
            round(float(total),2)
        )

        updatecart(db,session["user_id"])
        flash("successfully added !!!")
        return render_template(
            "cart.html",
            carts=loadorder(db,session["user_id"]),
            cart_notification = notification(db)
             )
    else:
        return redirect("/")




@app.route("/cart", methods =["GET","POST"])
def cart():
    if request.method == "POST" :
        action = request.form.get("action")
        address = request.form.get("address")
        customername = request.form.get("customername")
        total_cost = request.form.get("total_cost")
        total_units = request.form.get("total_units")
        product_units = request.form.get("product_units")
        today = datetime.today()
        if action == "cancel":
            db.execute(
                       "delete from orders where cart_id = ? ",
                       usercart_id(db,session["user_id"])
                       )
            updatecart(db,session["user_id"])
            return redirect("/")

        if action == "finalize":
            rows = db.execute(
                "select * from orders join carts on carts.id = orders.cart_id join products on products.id=orders.product_id where status =? and cart_id =?" ,
                "pending",
                usercart_id(db,session["user_id"])
                )
            for row in rows :
                if row["units"] > row["stock_units"]:
                    flash("not enought units in stocks for this product")
                    return render_template("order.html", select=row)


            # update products stocks
            rows = db.execute(
                "select product_id , units , stock_units from orders join products on products.id = orders.product_id where cart_id = ? "
                ,usercart_id(db, session["user_id"]))
            for row in rows :
                 db.execute(
                "update products set stock_units = ? where id =?",
                row["stock_units"] - row["units"],
                row["product_id"]
                   )
            #create receipt
            receipts = db.execute(
                "select * from carts join orders on orders.cart_id = carts.id join products on products.id=orders.product_id where status = ? and customer_id = ?",
                "pending",
                session["user_id"])

            #update the cart set status to submit
            db.execute("update carts set status =? , date = ? where id = ? and status = ?",
                       "submit",
                        datetime.today(),
                        usercart_id(db,session["user_id"]),
                       "pending")
            #create new cart for customer and set status to pending
            createcart(db, session["user_id"],datetime.today())
            return render_template("receipt.html", receipts = receipts)

    return render_template(
           "cart.html",
            carts=loadorder(db,session["user_id"]),
            cart_notification = notification(db)
                  )

@app.route("/historic")
def historic():
    carts = db.execute("select * from carts where customer_id = ?" , session["user_id"])
    orders = db.execute(" select * from orders join products on products.id = orders.product_id where status= ? and customer_id =?",
                        "complete",
                        session["user_id"])
    counts = []
    if len(carts) != 0 :
        for row in carts :
            counts.append(row["product_units"])

    return render_template("cart.html" , orders = orders ,counts = counts)


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        search = request.form.get("search")
        if not search:
            return redirect("/")
        else:
            search = "%" + search + "%"
            products = db.execute("select * from products where name like ? ", search)
            if len(products) == 0:
                flash("no item found!!!")
                return redirect("/")
            else:
                message = str(len(products))
                flash(message + " items found !!!")
                return render_template("layout.html", products=products, cart_notification = notification(db))
    else:
        return redirect("/")

@app.route("/contact")
def contact():
    return render_template("contact.html", contact= "go")

@app.route("/about")
def about():
    return render_template("about.html", about= "go")



@app.route("/newproduct", methods=["GET","POST"])
@login_admin_required
def newproduct():
    if request.method == "POST" :
           action = request.form.get("action")
           product_id = request.form.get("product_id")
           name = request.form.get("name")
           price = request.form.get("price")
           uom_id = request.form.get("uom_id")
           img_name = request.form.get("img_name")
           print(img_name)
           department = request.form.get("department").lower()
           stock_units = request.form.get("stock_units")
           print("product_id =:" , product_id)
           if action =="submit":
               db.execute(
               "insert into products (name,price,uom_id,img_name,department,stock_units) VALUES(?,?,?,?,?,?)",
               name,
               price,
               uom_id,
               img_name,
               department,
               stock_units
               )
               return redirect("/myproduct")
           if action == "update":
               db.execute(
               "update products set name =?,price =?,uom_id =?,img_name =?,department =?,stock_units = ? where id = ?",
               name,
               price,
               uom_id,
               img_name,
               department,
               stock_units,
               product_id
               )
               return redirect("/myproduct")
           if action== "delete":
                db.execute(
               "delete from products where id = ?",
               product_id
               )
                return redirect("/myproduct")

    return render_template("product.html", message="new product")


@app.route("/myproduct", methods=["GET","POST"])
@login_admin_required
def Myproduct():
    if request.method == "POST" :
           department = request.form.get("department")
           if department == "new" :
               return redirect("/newproduct")
           return render_template("product.html", products=loadproduct(db,department))
    return render_template("product.html", products=loadproduct(db,"all"), message="my product")


@app.route("/customer")
@login_admin_required
def customer():
    customers = db.execute("select * from customers join users on users.id = customers.user_id ")
    return render_template("product.html", customers=customers)

@app.route("/company")
@login_admin_required
def company():
    return render_template("decoration.html", products=loadproduct(db,"snack"))