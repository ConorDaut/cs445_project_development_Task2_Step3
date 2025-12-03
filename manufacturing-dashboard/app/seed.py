from datetime import date
from werkzeug.security import generate_password_hash
from .models import db, UserAccount, Parts, Orders

def run_seed():
    # Create admin if not exists
    admin = UserAccount.query.filter_by(Account_Username="admin").first()
    if not admin:
        admin = UserAccount(
            Account_Username="admin",
            Account_Password=generate_password_hash("admin123"),
            Account_Privilege="admin",
            Account_Company="Acme Manufacturing",
            Account_Shipping_Address="100 Industrial Way",
            Account_Contact_Info="admin@acme.example"
        )
        db.session.add(admin)

    # Create standard user
    user = UserAccount.query.filter_by(Account_Username="user").first()
    if not user:
        user = UserAccount(
            Account_Username="user",
            Account_Password=generate_password_hash("user123"),
            Account_Privilege="standard",
            Account_Company="Beta Corp",
            Account_Shipping_Address="42 Supply Rd",
            Account_Contact_Info="ops@beta.example"
        )
        db.session.add(user)
    db.session.commit()

    # Parts
    if Parts.query.count() == 0:
        p1 = Parts(Part_Name="Gear A", Part_Size="M", Part_Price=12.50)
        p2 = Parts(Part_Name="Bolt B", Part_Size="S", Part_Price=0.35)
        p3 = Parts(Part_Name="Panel C", Part_Size="L", Part_Price=28.00)
        db.session.add_all([p1, p2, p3])
        db.session.commit()

    # Orders
    if Orders.query.count() == 0:
        parts = Parts.query.all()
        gear = next((p for p in parts if p.Part_Name == "Gear A"), None)
        bolt = next((p for p in parts if p.Part_Name == "Bolt B"), None)

        o1 = Orders(Account_ID=user.Account_ID, Part_ID=gear.Part_ID if gear else None,
                    Order_Price=125.00, Order_Quantity=10, Order_Date=date.today(), Order_Status="Pending")
        o2 = Orders(Account_ID=user.Account_ID, Part_ID=bolt.Part_ID if bolt else None,
                    Order_Price=7.00, Order_Quantity=20, Order_Date=date.today(), Order_Status="Completed")
        o3 = Orders(Account_ID=admin.Account_ID, Part_ID=gear.Part_ID if gear else None,
                    Order_Price=250.00, Order_Quantity=20, Order_Date=date.today(), Order_Status="Processing")
        db.session.add_all([o1, o2, o3])
        db.session.commit()
