from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from config import Config

# Initialize app and API
app = Flask(__name__, static_folder='static')
app.config.from_object(Config)
db = SQLAlchemy(app)
api = Api(app)


# Database Model for Orders
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


# User Login Route
from flask import render_template
from .models import Product


@app.route("/")
def index():
    # Fetch all products from the database
    products = Product.query.all()

    # Group products by category
    categorized_products = {}
    for product in products:
        if product.category not in categorized_products:
            categorized_products[product.category] = []
        categorized_products[product.category].append(product)

    # Extract unique categories for tabs
    categories = categorized_products.keys()

    return render_template(
        "index.html",
        categories=categories,
        categorized_products=categorized_products
    )


# Dashboard Route (Only accessible if logged in)
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    orders = Order.query.all()  # Fetch all orders
    return render_template('dashboard.html', orders=orders)


# Logout Route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


# RESTful API for Orders
class OrderResource(Resource):
    def get(self, order_id):
        order = Order.query.get_or_404(order_id)
        return {"id": order.id, "item": order.item, "quantity": order.quantity}

    def put(self, order_id):z
        order = Order.query.get_or_404(order_id)
        order.item = request.json.get('item', order.item)
        order.quantity = request.json.get('quantity', order.quantity)
        db.session.commit()
        return {"message": "Order updated"}, 200

    def delete(self, order_id):
        order = Order.query.get_or_404(order_id)
        db.session.delete(order)
        db.session.commit()
        return {"message": "Order deleted"}, 200


api.add_resource(OrderResource, '/api/orders/<int:order_id>')

if __name__ == '__main__':
    db.create_all()  # Create tables
    app.run(debug=True)