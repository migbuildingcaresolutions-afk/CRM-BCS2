from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import json
from weasyprint import HTML
import tempfile

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your-secret-key'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Models defined directly in app.py
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(100))

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    items = db.Column(db.Text)  # JSON string
    subtotal = db.Column(db.Float)
    tax = db.Column(db.Float)
    total = db.Column(db.Float)
    paid = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

class WorkOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    description = db.Column(db.String(200))
    status = db.Column(db.String(50))  # e.g., Open, Closed
    due_date = db.Column(db.DateTime)

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    items = db.Column(db.Text)  # JSON string
    total = db.Column(db.Float)
    converted_to_invoice = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(100))

# Dashboard route
@app.route('/')
def dashboard():
    client_count = Client.query.count()
    open_work_orders = WorkOrder.query.filter_by(status='Open').count()
    unpaid_invoices = Invoice.query.filter_by(paid=False).count()
    pending_quotes = Quote.query.filter_by(converted_to_invoice=False).count()
    upcoming_orders = WorkOrder.query.filter(WorkOrder.due_date >= datetime.today()).order_by(WorkOrder.due_date).limit(5).all()
    return render_template('dashboard.html', client_count=client_count, open_work_orders=open_work_orders, unpaid_invoices=unpaid_invoices, pending_quotes=pending_quotes, upcoming_orders=upcoming_orders)

# Clients route
@app.route('/clients', methods=['GET', 'POST'])
def clients():
    if request.method == 'POST':
        client = Client(
            name=request.form['name'],
            address=request.form['address'],
            phone=request.form['phone'],
            email=request.form['email']
        )
        db.session.add(client)
        db.session.commit()
        flash("Client added successfully!", "success")
        return redirect(url_for('clients'))
    clients = Client.query.all()
    return render_template('clients.html', clients=clients)

# Work Orders route
@app.route('/work-orders', methods=['GET', 'POST'])
def work_orders():
    clients = Client.query.all()
    if request.method == 'POST':
        order = WorkOrder(
            client_id=request.form['client_id'],
            description=request.form['description'],
            status=request.form['status'],
            due_date=datetime.strptime(request.form['due_date'], '%Y-%m-%d')
        )
        db.session.add(order)
        db.session.commit()
        flash("Work order created!", "success")
        return redirect(url_for('work_orders'))
    orders = WorkOrder.query.all()
    return render_template('work_orders.html', orders=orders, clients=clients)

# Invoices route
@app.route('/invoices', methods=['GET', 'POST'])
def invoices():
    clients = Client.query.all()
    if request.method == 'POST':
        items = json.dumps([{'description': request.form['description'], 'amount': float(request.form['amount'])}])
        subtotal = float(request.form['amount'])
        tax = subtotal * 0.1
        total = subtotal + tax
        invoice = Invoice(
            client_id=request.form['client_id'],
            items=items,
            subtotal=subtotal,
            tax=tax,
            total=total,
            paid=False,
            date_created=datetime.now()
        )
        db.session.add(invoice)
        db.session.commit()
        flash("Invoice created!", "success")
        return redirect(url_for('invoices'))

    query = Invoice.query.join(Client)
    search = request.args.get('search')
    status = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    if search:
        query = query.filter(Client.name.ilike(f'%{search}%'))
    if status == 'paid':
        query = query.filter(Invoice.paid == True)
    elif status == 'unpaid':
        query = query.filter(Invoice.paid == False)
    if date_from:
        query = query.filter(Invoice.date_created >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(Invoice.date_created <= datetime.strptime(date_to, '%Y-%m-%d'))

    invoices = query.order_by(Invoice.date_created.desc()).all()
    return render_template('invoices.html', invoices=invoices, clients=clients, search=search, status=status, date_from=date_from, date_to=date_to)

@app.route('/invoice/<int:id>/mark-paid', methods=['POST'])
def mark_invoice_paid(id):
    invoice = Invoice.query.get_or_404(id)
    invoice.paid = True
    db.session.commit()
    flash("Invoice marked as paid.", "success")
    return redirect(url_for('invoices'))

@app.route('/invoice/<int:id>/pdf')
def invoice_pdf(id):
    invoice = Invoice.query.get_or_404(id)
    client = Client.query.get(invoice.client_id)
    settings = Settings.query.first()
    items = json.loads(invoice.items)
    rendered = render_template('invoice_pdf.html', invoice=invoice, client=client, settings=settings, items=items)
    pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    HTML(string=rendered).write_pdf(pdf_file.name)
    return send_file(pdf_file.name, as_attachment=True, download_name=f'invoice_{invoice.id}.pdf')

# Quotes route
@app.route('/quotes', methods=['GET', 'POST'])
def quotes():
    clients = Client.query.all()
    if request.method == 'POST':
        items = json.dumps([{'description': request.form['description'], 'amount': float(request.form['amount'])}])
        total = float(request.form['amount'])
        quote = Quote(client_id=request.form['client_id'], items=items, total=total, converted_to_invoice=False, date_created=datetime.now())
        db.session.add(quote)
        db.session.commit()
        flash("Quote created!", "success")
        return redirect(url_for('quotes'))

    query = Quote.query.join(Client)
    search = request.args.get('search')
    status = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    if search:
        query = query.filter(Client.name.ilike(f'%{search}%'))
    if status == 'converted':
        query = query.filter(Quote.converted_to_invoice == True)
    elif status == 'pending':
        query = query.filter(Quote.converted_to_invoice == False)
    if date_from:
        query = query.filter(Quote.date_created >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(Quote.date_created <= datetime.strptime(date_to, '%Y-%m-%d'))

    quotes = query.order_by(Quote.date_created.desc()).all()
    return render_template('quotes.html', quotes=quotes, clients=clients, search=search, status=status, date_from=date_from, date_to=date_to)

# Settings route
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    settings = Settings.query.first()
    if not settings:
        settings = Settings(business_name="Building Care Solutions", address="8889 Caminito Plaza Centro Unit 7117, San Diego, CA 92122", phone="858-737-8499", email="mig.buildincaresolutions@gmail.com")
        db.session.add(settings)
        db.session.commit()
    if request.method == 'POST':
        settings.business_name = request.form['business_name']
        settings.address = request.form['address']
        settings.phone = request.form['phone']
        settings.email = request.form['email']
        db.session.commit()
        flash("Settings updated!", "success")
        return redirect(url_for('settings'))
    return render_template('settings.html', settings=settings)

if __name__ == "__main__":
    app.run(debug=True)