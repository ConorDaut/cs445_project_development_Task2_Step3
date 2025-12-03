from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class UserAccount(db.Model):
    __tablename__ = "user_accounts"
    Account_ID = db.Column(db.Integer, primary_key=True)
    Account_Username = db.Column(db.String(150), unique=True, nullable=False)
    Account_Password = db.Column(db.String(255), nullable=False)
    Account_Privilege = db.Column(db.String(20), nullable=False, default="standard")
    Account_Company = db.Column(db.String(150), nullable=True)
    Account_Shipping_Address = db.Column(db.String(255), nullable=True)
    Account_Contact_Info = db.Column(db.String(255), nullable=True)

    # Relationships
    orders = db.relationship("Orders", backref="account", lazy=True)

class Parts(db.Model):
    __tablename__ = "parts"
    Part_ID = db.Column(db.Integer, primary_key=True)
    Part_Name = db.Column(db.String(150), nullable=False)
    Part_Size = db.Column(db.String(100), nullable=True)
    Part_Price = db.Column(db.Float, nullable=False, default=0.0)
    # Optional relationship to Orders by Order_ID (as per ER)
    Order_ID = db.Column(db.Integer, db.ForeignKey("orders.Order_ID"), nullable=True)

class Orders(db.Model):
    __tablename__ = "orders"
    Order_ID = db.Column(db.Integer, primary_key=True)
    Account_ID = db.Column(db.Integer, db.ForeignKey("user_accounts.Account_ID"), nullable=False)
    Order_Price = db.Column(db.Float, nullable=False, default=0.0)
    Order_Quantity = db.Column(db.Integer, nullable=False, default=1)
    Order_Date = db.Column(db.Date, nullable=False)
    Order_Status = db.Column(db.String(50), nullable=False, default="Pending")
    Part_ID = db.Column(db.Integer, db.ForeignKey("parts.Part_ID"), nullable=True)

    part = db.relationship("Parts", foreign_keys=[Part_ID], backref="orders", lazy=True)
