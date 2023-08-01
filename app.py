from flask import Flask
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from cs50 import SQL
from datetime import datetime
from flask_login import login_manager,login_required, logout_user

from helper import loadproduct, login_required , loadorder , notification , login_admin_required, createcart,usercart_id ,updatecart,generatepdf,customer_data,\
generate_delivery_date,open_order_window,add_recent_deliveries,get_deliveries ,get_delivery_dates

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
        return render_template("layout.html", products=products,cart_notification = notification(db))
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
        address = request.form.get("street")+request.form.get("city")+request.form.get("state")+request.form.get("zip")
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
            email
        )
        session["user_id"] = db.execute(
            "select id from users where username = ? ", username
        )[0]["id"]
        # log in customers infos
        db.execute(
            "insert into customers (user_id,firstname,lastname,gender,phone_number,address,business_name, relation) values(?,?,?,?,?,?,?,?)",
            session["user_id"],
            firstname,
            lastname,
            gender,
            phonenumber,
            address,
            "My business",
            "new"
           )
        session["relation"] = "new"
        session["username"] = username
        session["firstname"] = firstname
        session["day"] = datetime.now().weekday()
        session["cart_id"] = createcart(db,session["user_id"])
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
        # create an empty cart for customer upon sign in if he doest have one and set status to pending
        createcart(db,session["user_id"])
        #get the status of the customer, is he new or already client
        if session["user_id"] == 1:
               #create delivery date if does't exist
               delivery_date = generate_delivery_date()["date"]
               delivery_day = generate_delivery_date()["day"]
               add_recent_deliveries(db,delivery_date,delivery_day)

        session["relation"] = db.execute("select relation from customers where user_id = ?", session["user_id"])[0]["relation"]
        session["cart_id"] = createcart(db,session["user_id"])
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
                            session["cart_id"])
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

        session["cart_id"] = createcart(db,session["user_id"])
        session["relation"] = db.execute("select relation from customers where user_id = ?", session["user_id"])[0]["relation"]
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

        status = db.execute("select status from carts where customer_id = ? and id = ? ",
                            session["user_id"],
                            session["cart_id"])[0]["status"]
        if status == "submit":
            flash("you have a pending items in the carts due for delivery")
            return redirect("/cart")

        # get the units number in stock of the product
        units_in_stock = db.execute("select (stock_units) from products where id = ?" , product_id)[0]["stock_units"]
        if units > units_in_stock:
            flash(" not anought units in stock ")
            return render_template("order.html", select=select[0])

        # we check if the product has been already added by the customer
        cart_id = db.execute(
            "select * from carts where status = ? and customer_id = ?",
            "pending",
            session["user_id"])[0]["id"]
        order =db.execute(
            "select * from orders join carts on carts.id = orders.cart_id where status = ? and (product_id = ? and customer_id = ?) "
            ,"pending",
            product_id,
            session["user_id"])

        if len(order) == 1 :
            db.execute(
                "update  orders  set units = ? , cost = ? where  product_id = ? and cart_id =?",
                units,
                round(float(total),2),
                product_id,
                session["cart_id"]
            )
        else:
            db.execute(
            "insert into orders (cart_id , product_id, product_name, units ,cost) VALUES(?,?,?,?,?)",
            session["cart_id"],
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
            delivery_date = generate_delivery_date(),
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
        method = request.form.get("method")
        print(method)
        session["relation"] = db.execute("select relation from customers where user_id = ?", session["user_id"])[0]["relation"]
        if action == "edit":
            if session["relation"]== "client":
                rows = db.execute(
                                    "select product_id , units , stock_units from orders join products on products.id = orders.product_id where cart_id = ? "
                                    ,session["cart_id"])
                for row in rows:
                                    db.execute(
                                    "update products set stock_units = ? where id =?" ,
                                    row["stock_units"] + row["units"],
                                    row["product_id"]
                                    )
            db.execute("update carts set status = ? ,comment= ? where id = ? and customer_id=?",
                       "pending",
                       "open shopping cart",
                       session["cart_id"],
                       session["user_id"])
            return redirect("/cart")

        if action == "cancel":
            db.execute(
                       "delete from orders where cart_id = ? ",
                       session["cart_id"]
                       )
            updatecart(db,session["user_id"])
            return redirect("/")

        if action == "finalize":
            if not open_order_window() :
                flash("order window closes on wednesdays and sundays")
                return redirect("/cart")

            rows = db.execute(
                "select * from orders join carts on carts.id = orders.cart_id join products on products.id=orders.product_id where status =? and cart_id =?" ,
                "pending",
                session["cart_id"]
                )
            for row in rows :
                if row["units"] > row["stock_units"]:
                    flash("not enought units in stocks for this product")
                    return render_template("order.html", select=row)

            # update products stocks, if the customer status is client and active customer ,
            if session["relation"] == "client":
                    rows = db.execute(
                        "select product_id , units , stock_units from orders join products on products.id = orders.product_id where cart_id = ? "
                        ,session["cart_id"])
                    for row in rows :
                        db.execute(
                        "update products set stock_units = ? where id =?",
                        row["stock_units"] - row["units"],
                        row["product_id"]
                        )
            #create receipt
            receipts = db.execute(
                "select * from carts join customers on customers.user_id=carts.customer_id join orders on orders.cart_id = carts.id  join products on products.id=orders.product_id where carts.status = ? and customer_id = ?",
                "pending",
                session["user_id"])

            #update the cart set status to submit
            db.execute("update carts set status =? , date = ? ,comment = ? where id = ? and status = ?",
                       "submit",
                        datetime.today().date(),
                        "waiting for admin approval",
                        session["cart_id"],
                       "pending")
            #create new cart for customer and set status to pending
            #createcart(db, session["user_id"])

            #html = render_template("receipt.html",receipts = receipts)
            #generatepdf("templates/test.html")
            return render_template("receipt.html", receipts = receipts)


    cart = db.execute("select * from carts  where id = ? and customer_id = ? ",
                      session["cart_id"],
                      session["user_id"]
                      )[0]
    delivery_date = generate_delivery_date()
    if cart["status"] == "submit":
        return render_template(
           "cart.html",
            cart = cart,
            items = loadorder(db,session["user_id"]),
            delivery_date = delivery_date,
            cart_notification = notification(db)
                  )
    if cart["status"] == "pending":
            return render_template(
                "cart.html",
                    carts=loadorder(db,session["user_id"]),
                    delivery_date = delivery_date,
                    cart_notification = notification(db)
                        )
    return render_template(
                "cart.html",
                    message = "cart is empty",
                    cart_notification = notification(db)
                        )

@app.route("/pdf")
def pdf():
    return 0


@app.route("/history", methods=["GET","POST"])
def historic():
    if request.method =="POST":

         date = request.form.get("date")
         print(date)
         history = db.execute("select * from carts join deliveries on deliveries.cart_id=carts.id  where (date = ? and status!=?) and carts.customer_id = ?" , date,"submit", session["user_id"])
         items = db.execute("select * from orders  join products on products.id=orders.product_id  where cart_id = ? ", history[0]["id"])
         carts_history = db.execute("select * from carts join customers on customers.user_id = carts.customer_id  where  comment=? and (customer_id = ? and status = ? )group by date order by date limit 5 ",
                      "delivered",
                      session["user_id"],
                      "complete"
                      )
         return render_template(
           "cart.html",
            history = history[0],
            items = items,
            carts_history = carts_history
                  )


    carts_history = db.execute("select * from carts join customers on customers.user_id = carts.customer_id  where  comment !=? and (customer_id = ? and status = ? )group by date  order by date limit 5 ",
                      "null",
                      session["user_id"],
                      "complete"
                      )
    print(carts_history)
    cart={}
    return render_template(
           "cart.html",
           cart=cart,
            carts_history = carts_history,
            cart_notification = notification(db)
                  )



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



@app.route("/mycustomer", methods=["GET","POST"])
@login_admin_required
def customer():
    if request.method == "POST" :
           portal = request.form.get("action").lower()
           if portal == "users":
               return render_template( "customer.html", users = customer_data(db,portal))
           if portal == "customers":
               return render_template( "customer.html", customers = customer_data(db,portal))
           if portal == "carts":
               return render_template( "customer.html", carts = customer_data(db,portal))
           if portal == "client":
               clients = db.execute(
                   "select * from customers where relation = ? ",
                     "client"
                     )
               return render_template( "customer.html", customers = clients)
           if portal == "deliveries":
               delivery_date = generate_delivery_date()["date"]
               delivery_day = generate_delivery_date()["day"]
               add_recent_deliveries(db,delivery_date,delivery_day)
               return redirect("/delivery")

    customers = db.execute("select * from customers join users on users.id = customers.user_id ")
    return render_template( "customer.html", customers = customers )



@app.route("/delivery", methods=["GET","POST"])
@login_admin_required
def delivery():
       if request.method == "POST":
            cart_id = request.form.get("cart_id")
            action = request.form.get("action")
            customer_id = request.form.get("customer_id")
            customername = request.form.get("customername")
            date = request.form.get("date")
            if date :
                 delivery_day = generate_delivery_date()["day"]
                 delivery_date = generate_delivery_date()["date"]
                 add_recent_deliveries(db,delivery_date,delivery_day)
                 return render_template("customer.html",deliveries=get_deliveries(db,date),delivery_dates=get_delivery_dates(db),delivery_date = generate_delivery_date(),open_delivery_window = not open_order_window(),selected_date = date)
            # set the cart status to complete

            if action == "details":
                 orders = db.execute("select * from orders join carts on carts.id=orders.cart_id join products on products.id=orders.product_id where cart_id = ?", cart_id)
                 return render_template("customer.html",orders=orders)

            relation = db.execute("select relation from customers join carts on customers.user_id = carts.customer_id where id =?",cart_id)[0]["relation"]
            if action == "valider":
                # we update the product stocks if we deliver for new customer
                if relation == "new":
                    rows = db.execute(
                                    "select product_id , units , stock_units from orders join products on products.id = orders.product_id where cart_id = ? "
                                    ,cart_id)
                    for row in rows:
                        db.execute(
                        "update products set stock_units = ? where id =?",
                        row["stock_units"] - row["units"],
                        row["product_id"]
                                )
                    # set customer relation to client
                    db.execute(
                    "update customers set relation = ? where user_id = ?",
                    "client",
                    customer_id)

                # set cart status to complete after delivery
                db.execute(
                    "update carts set status =? , comment =? where status = ? and (id = ? and customer_id =?)",
                    "complete",
                    "delivered",
                    "submit",
                    cart_id,
                    customer_id)

            if action == "annuler":
                if relation == "client":
                    rows = db.execute(
                                    "select product_id , units , stock_units from orders join products on products.id = orders.product_id where cart_id = ? "
                                    ,cart_id)
                    for row in rows:
                        db.execute(
                        "update products set stock_units = ? where id =?",
                        row["stock_units"] + row["units"],
                        row["product_id"]
                                )
                db.execute(
                    "update carts set status =? , comment =? where status = ? and (id = ? and customer_id =?)",
                    "complete",
                    "canceled",
                    "submit",
                    cart_id,
                    customer_id)


            #set delivery note to action valider ou annuler
            db.execute(
                    "update deliveries set note = ? where cart_id = ?",
                    action,
                    cart_id
                    )
            # create new cart id for the same customer
            createcart(db,customer_id)
            return redirect("/delivery")


       delivery_dates = db.execute( "select delivery_date from deliveries group by delivery_date order by delivery_date DESC ")
       return render_template("customer.html",delivery_date = generate_delivery_date(),deliveries = get_deliveries(db,delivery_dates[0]["delivery_date"]),open_delivery_window = not open_order_window(), delivery_dates = get_delivery_dates(db))


@app.route("/customercart", methods=["GET","POST"])
def customercart():
    if request.method == "POST":
        select = request.form.get("detail")
        status = request.form.get("status")
        customer_id = request.form.get("customer_id")

        if select == "carts":
            carts = db.execute(
                "select * from carts join customers on customers.user_id=carts.customer_id where customer_id =? ",
                customer_id)
            if len(carts)!= 0:
                carts[0]["filter"] = "yes"
            return render_template("customer.html", carts=carts)

        status = status.lower()
        if customer_id:
            if status=="all carts":
                carts = db.execute(
                "select * from carts join customers on customers.user_id=carts.customer_id where customer_id =?  ",
                customer_id
                )
            else:
                carts = db.execute(
                "select * from carts join customers on customers.user_id=carts.customer_id where customer_id =? and status =? ",
                customer_id,
                status)
            if len(carts)!= 0:
                carts[0]["filter"] = "yes"
            else:
                cart={}
                cart["customer_id"] = customer_id
                return render_template("customer.html", cart=cart)

        else:
            if status=="all carts":
                carts =db.execute(
                "select * from carts join customers on customers.user_id=carts.customer_id ")
            else:
                carts =db.execute(
                "select * from carts join customers on customers.user_id=carts.customer_id where status = ?",
                status)
            if len(carts)!= 0:
                carts[0]["filter"] = "no"
            else:
                cart={}
                cart["customer_id"] = ""
                return render_template("customer.html", cart=cart)
        return render_template("customer.html", carts=carts)


    return 0


@app.route("/company")
@login_admin_required
def company():
    return render_template("decoration.html", products=loadproduct(db,"snack"))
