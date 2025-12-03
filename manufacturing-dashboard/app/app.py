import os
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from .models import db, UserAccount, Orders, Parts
from .utils import login_required, admin_required

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///manufacturing.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Routes

    @app.route("/")
    def index():
        if "account_id" in session:
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    # Auth: login, logout, create_account

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("Account_Username", "").strip()
            password = request.form.get("Account_Password", "").strip()

            user = UserAccount.query.filter_by(Account_Username=username).first()
            if not user or not check_password_hash(user.Account_Password, password):
                flash("Invalid username or password.", "error")
                return render_template("login.html")

            session["account_id"] = user.Account_ID
            session["account_privilege"] = user.Account_Privilege
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Logged out.", "info")
        return redirect(url_for("login"))

    @app.route("/create_account", methods=["GET", "POST"])
    def create_account():
        if request.method == "POST":
            username = request.form.get("Account_Username", "").strip()
            password = request.form.get("Account_Password", "").strip()
            privilege = request.form.get("Account_Privilege", "standard").strip()
            company = request.form.get("Account_Company", "").strip()
            shipping = request.form.get("Account_Shipping_Address", "").strip()
            contact = request.form.get("Account_Contact_Info", "").strip()

            if not username or not password:
                flash("Username and password are required.", "error")
                return render_template("create_account.html")

            if UserAccount.query.filter_by(Account_Username=username).first():
                flash("Username already exists.", "error")
                return render_template("create_account.html")

            hashed = generate_password_hash(password)
            user = UserAccount(
                Account_Username=username,
                Account_Password=hashed,
                Account_Privilege="admin" if privilege.lower() == "admin" else "standard",
                Account_Company=company,
                Account_Shipping_Address=shipping,
                Account_Contact_Info=contact
            )
            db.session.add(user)
            db.session.commit()
            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))
        return render_template("create_account.html")

    # Dashboard

    @app.route("/dashboard")
    @login_required
    def dashboard():
        account_id = session.get("account_id")
        is_admin = session.get("account_privilege") == "admin"
        current_orders = Orders.query.filter_by(Account_ID=account_id).filter(Orders.Order_Status.in_(["Pending", "Processing", "Shipped"])).order_by(Orders.Order_Date.desc()).limit(10).all()
        previous_orders = Orders.query.filter_by(Account_ID=account_id).filter(Orders.Order_Status.in_(["Completed", "Cancelled"])).order_by(Orders.Order_Date.desc()).limit(10).all()
        parts_count = Parts.query.count()
        orders_count = Orders.query.count()
        return render_template("dashboard.html", is_admin=is_admin, current_orders=current_orders, previous_orders=previous_orders, parts_count=parts_count, orders_count=orders_count)

    # Account

    @app.route("/account")
    @login_required
    def account():
        user = UserAccount.query.get(session["account_id"])
        return render_template("account.html", user=user)

    # Orders: view_current_orders, view_previous_orders, order create/update, admin sort/update

    @app.route("/orders/current")
    @login_required
    def orders_current():
        account_id = session["account_id"]
        orders = Orders.query.filter_by(Account_ID=account_id).filter(Orders.Order_Status.in_(["Pending", "Processing", "Shipped"])).order_by(Orders.Order_Date.desc()).all()
        return render_template("orders_current.html", orders=orders)

    @app.route("/orders/previous")
    @login_required
    def orders_previous():
        account_id = session["account_id"]
        orders = Orders.query.filter_by(Account_ID=account_id).filter(Orders.Order_Status.in_(["Completed", "Cancelled"])).order_by(Orders.Order_Date.desc()).all()
        return render_template("orders_previous.html", orders=orders)

    @app.route("/orders/new", methods=["GET", "POST"])
    @login_required
    def order_new():
        parts = Parts.query.order_by(Parts.Part_Name.asc()).all()
        if request.method == "POST":
            account_id = session["account_id"]
            part_id = request.form.get("Part_ID")
            quantity = int(request.form.get("Order_Quantity", "1"))
            price = float(request.form.get("Order_Price", "0") or "0")
            status = request.form.get("Order_Status", "Pending")
            order_date_str = request.form.get("Order_Date") or date.today().isoformat()
            try:
                order_date = datetime.strptime(order_date_str, "%Y-%m-%d").date()
            except ValueError:
                order_date = date.today()

            if quantity <= 0:
                flash("Order quantity must be positive.", "error")
                return render_template("order_form.html", parts=parts, order=None)

            order = Orders(
                Account_ID=account_id,
                Part_ID=int(part_id) if part_id else None,
                Order_Quantity=quantity,
                Order_Price=price,
                Order_Status=status,
                Order_Date=order_date
            )
            db.session.add(order)
            db.session.commit()
            flash("Order created.", "success")
            return redirect(url_for("orders_current"))
        return render_template("order_form.html", parts=parts, order=None)

    @app.route("/orders/<int:order_id>/edit", methods=["GET", "POST"])
    @login_required
    def order_edit(order_id):
        order = Orders.query.get_or_404(order_id)
        # Only owner or admin can edit
        if order.Account_ID != session["account_id"] and session.get("account_privilege") != "admin":
            flash("Unauthorized to modify this order.", "error")
            return redirect(url_for("dashboard"))
        parts = Parts.query.order_by(Parts.Part_Name.asc()).all()
        if request.method == "POST":
            order.Part_ID = int(request.form.get("Part_ID")) if request.form.get("Part_ID") else None
            order.Order_Quantity = int(request.form.get("Order_Quantity", order.Order_Quantity))
            order.Order_Price = float(request.form.get("Order_Price", order.Order_Price))
            order.Order_Status = request.form.get("Order_Status", order.Order_Status)
            order_date_str = request.form.get("Order_Date", order.Order_Date.isoformat())
            try:
                order.Order_Date = datetime.strptime(order_date_str, "%Y-%m-%d").date()
            except ValueError:
                pass
            db.session.commit()
            flash("Order updated.", "success")
            # Redirect based on status
            if order.Order_Status in ["Completed", "Cancelled"]:
                return redirect(url_for("orders_previous"))
            else:
                return redirect(url_for("orders_current"))
        return render_template("order_form.html", parts=parts, order=order)

    # Admin operations: sort_orders, update_modify_orders

    @app.route("/admin/orders")
    @admin_required
    def admin_orders():
        sort = request.args.get("sort", "Order_Date")
        direction = request.args.get("dir", "desc")
        status = request.args.get("status", "")
        query = Orders.query
        if status:
            query = query.filter_by(Order_Status=status)
        # Sorting map
        mapping = {
            "Order_Date": Orders.Order_Date,
            "Order_Price": Orders.Order_Price,
            "Order_Quantity": Orders.Order_Quantity,
            "Order_Status": Orders.Order_Status,
            "Account_ID": Orders.Account_ID
        }
        col = mapping.get(sort, Orders.Order_Date)
        if direction == "asc":
            query = query.order_by(col.asc())
        else:
            query = query.order_by(col.desc())
        orders = query.all()
        # preload parts and users
        parts_by_id = {p.Part_ID: p for p in Parts.query.all()}
        users_by_id = {u.Account_ID: u for u in UserAccount.query.all()}
        return render_template("orders_admin.html", orders=orders, parts_by_id=parts_by_id, users_by_id=users_by_id, sort=sort, direction=direction, status=status)

    @app.route("/admin/orders/<int:order_id>/update", methods=["POST"])
    @admin_required
    def admin_order_update(order_id):
        order = Orders.query.get_or_404(order_id)
        # Admin modifies fields
        order.Order_Status = request.form.get("Order_Status", order.Order_Status)
        order.Order_Price = float(request.form.get("Order_Price", order.Order_Price))
        order.Order_Quantity = int(request.form.get("Order_Quantity", order.Order_Quantity))
        part_id = request.form.get("Part_ID")
        order.Part_ID = int(part_id) if part_id else None
        db.session.commit()
        flash(f"Order {order.Order_ID} updated by admin.", "success")
        return redirect(url_for("admin_orders"))

    # Parts: CRUD and linking

    @app.route("/parts")
    @login_required
    def parts_list():
        parts = Parts.query.order_by(Parts.Part_Name.asc()).all()
        return render_template("parts_list.html", parts=parts)

    @app.route("/parts/new", methods=["GET", "POST"])
    @admin_required
    def parts_new():
        if request.method == "POST":
            name = request.form.get("Part_Name", "").strip()
            size = request.form.get("Part_Size", "").strip()
            price = float(request.form.get("Part_Price", "0") or "0")
            if not name:
                flash("Part name is required.", "error")
                return render_template("part_form.html", part=None)
            part = Parts(Part_Name=name, Part_Size=size, Part_Price=price)
            db.session.add(part)
            db.session.commit()
            flash("Part created.", "success")
            return redirect(url_for("parts_list"))
        return render_template("part_form.html", part=None)

    @app.route("/parts/<int:part_id>/edit", methods=["GET", "POST"])
    @admin_required
    def parts_edit(part_id):
        part = Parts.query.get_or_404(part_id)
        if request.method == "POST":
            part.Part_Name = request.form.get("Part_Name", part.Part_Name).strip()
            part.Part_Size = request.form.get("Part_Size", part.Part_Size).strip()
            part.Part_Price = float(request.form.get("Part_Price", part.Part_Price))
            db.session.commit()
            flash("Part updated.", "success")
            return redirect(url_for("parts_list"))
        return render_template("part_form.html", part=part)

    # Seed route (optional, callable once)
    @app.route("/seed")
    def seed():
        from .seed import run_seed
        run_seed()
        flash("Database seeded.", "success")
        return redirect(url_for("login"))

    return app
