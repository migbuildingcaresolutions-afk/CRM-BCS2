from app import db

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))

class WorkOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    description = db.Column(db.String(200))
    status = db.Column(db.String(50))
    due_date = db.Column(db.Date)
    client = db.relationship('Client')

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    items = db.Column(db.Text)
    subtotal = db.Column(db.Float)
    tax = db.Column(db.Float)
    total = db.Column(db.Float)
    paid = db.Column(db.Boolean)
    date_created = db.Column(db.DateTime)
    client = db.relationship('Client')

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    items = db.Column(db.Text)
    total = db.Column(db.Float)
    converted_to_invoice = db.Column(db.Boolean)
    date_created = db.Column(db.DateTime)
    client = db.relationship('Client')

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100))
    name = db.Column(db.String(100))
    unit_price = db.Column(db.Float)
