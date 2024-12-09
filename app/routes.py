from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from . import db
from .models import Product, Order, OrderDetail, Category, Table
from werkzeug.utils import secure_filename
import os
from flask import current_app
from functools import wraps

bp = Blueprint('main', __name__)

# Allowed extensions for image uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# --- Helper Functions and Decorators ---
def allowed_file(filename):
    """Check if the uploaded file is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(view):
    """Decorator to restrict access to authenticated users."""
    @wraps(view)
    def wrapped_view(**kwargs):
        if not session.get('user_id'):
            flash("You must log in to access this page.", "danger")
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

def admin_required(view):
    """Decorator to restrict access to admin users only."""
    @wraps(view)
    def wrapped_view(**kwargs):
        if not session.get('is_admin'):
            flash("You do not have the necessary permissions to access this page.", "danger")
            return redirect(url_for('main.index'))
        return view(**kwargs)
    return wrapped_view

# --- Public Routes ---
@bp.route('/')
def index():
    categories = Category.query.all()
    categorized_products = {
        category.name: Product.query.filter_by(category_id=category.id).all()
        for category in categories
    }
    return render_template(
        'products.html',
        categories=[category.name for category in categories],
        categorized_products=categorized_products
    )

@bp.route('/api/orders', methods=['POST'])
def store_order():
    """
    Creates a new order and its details based on the provided data.
    """
    data = request.json
    try:
        # Calculate order totals
        subtotal = sum(item['price'] * item['quantity'] for item in data['items'])
        tax = subtotal * 0.1
        total_price = subtotal + tax

        # Create the order
        order = Order(total_price=total_price, tax=tax)
        db.session.add(order)
        db.session.commit()

        # Add order details
        for item in data['items']:
            order_detail = OrderDetail(
                order_id=order.id,
                product_id=item['product_id'],
                sugar_level=item.get('sugar_level', 'default'),
                quantity=item['quantity'],
                price=item['price']
            )
            db.session.add(order_detail)

        db.session.commit()
        return jsonify({'message': 'Order created successfully!', 'order_id': order.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@bp.route('/api/hold-orders/process/<int:table_id>', methods=['POST'])
def process_held_order(table_id):
    """
    Processes a held order for a specific table.
    """
    try:
        # Get the payload from the frontend
        data = request.json.get('items', [])
        if not data:
            return jsonify({'error': 'No items provided for processing'}), 400

        # Calculate totals
        subtotal = sum(item['price'] * item['quantity'] for item in data)
        tax = subtotal * 0.1
        total_price = subtotal + tax

        # Create a new order
        order = Order(total_price=total_price, tax=tax)
        db.session.add(order)
        db.session.commit()

        # Add order details
        for item in data:
            order_detail = OrderDetail(
                order_id=order.id,
                product_id=item['id'],
                sugar_level=item.get('sugarPercentage', 'default'),
                quantity=item['quantity'],
                price=item['price']
            )
            db.session.add(order_detail)

        db.session.commit()
        return jsonify({'message': f'Order for Table {table_id} processed successfully!', 'order_id': order.id}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# Route to retrieve all orders
@bp.route('/api/orders', methods=['GET'])
def get_orders():
    try:
        orders = Order.query.all()
        response = []
        for order in orders:
            order_details = [
                {
                    'product_id': detail.product_id,
                    'product_name': detail.product.name,
                    'quantity': detail.quantity,
                    'sugar_level': detail.sugar_level,
                    'price': detail.price
                }
                for detail in order.details
            ]
            response.append({
                'order_id': order.id,
                'total_price': order.total_price,
                'tax': order.tax,
                'details': order_details
            })
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400



# Route to render order display page
@bp.route('/orders', methods=['GET'])
def display_orders():
    return render_template('orders.html')




@bp.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([
        {
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'image': p.image,
            'category': p.category.name if p.category else None
        } for p in products
    ])


# Allowed extensions for images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Upload image route
@bp.route('/api/upload-image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.root_path, 'static/images')
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))
        return jsonify({'message': 'Image uploaded successfully', 'filename': filename}), 201

    return jsonify({'error': 'Invalid file type'}), 400

# Manage products view
@bp.route('/manage-products', methods=['GET'])
def manage_products():
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('manage_products.html', products=products, categories=categories)

# Add product route
@bp.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    try:
        new_product = Product(
            name=data['name'],
            price=data['price'],
            image=data['image'],
            category_id=data['category_id']
        )
        db.session.add(new_product)
        db.session.commit()
        return jsonify({'message': 'Product added successfully!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Update product route
@bp.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.json
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        product.name = data.get('name', product.name)
        product.price = data.get('price', product.price)
        product.image = data.get('image', product.image)
        product.category_id = data.get('category_id', product.category_id)

        db.session.commit()
        return jsonify({'message': 'Product updated successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Delete product route
@bp.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# Manage categories view
@bp.route('/manage-categories', methods=['GET'])
def manage_categories():
    categories = Category.query.all()
    return render_template('manage_categories.html', categories=categories)

# Add category route
@bp.route('/api/categories', methods=['POST'])
def add_category():
    data = request.json
    try:
        new_category = Category(name=data['name'])
        db.session.add(new_category)
        db.session.commit()
        return jsonify({'message': 'Category added successfully!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Update category route
@bp.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    data = request.json
    try:
        category = Category.query.get(category_id)
        if not category:
            return jsonify({'error': 'Category not found'}), 404

        category.name = data['name']
        db.session.commit()
        return jsonify({'message': 'Category updated successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Delete category route
@bp.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    try:
        category = Category.query.get(category_id)
        if not category:
            return jsonify({'error': 'Category not found'}), 404

        db.session.delete(category)
        db.session.commit()
        return jsonify({'message': 'Category deleted successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# Manage tables view
@bp.route('/manage-tables', methods=['GET'])
def manage_tables():
    tables = Table.query.all()
    return render_template('manage_tables.html', tables=tables)

@bp.route('/api/tables', methods=['GET'])
def get_tables():
    try:
        tables = Table.query.all()  # Assuming you have a Table model
        return jsonify([{'id': t.id, 'name': t.name} for t in tables]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add table route
@bp.route('/api/tables', methods=['POST'])
def add_table():
    data = request.json
    try:
        new_table = Table(name=data['name'], description=data.get('description', ''))
        db.session.add(new_table)
        db.session.commit()
        return jsonify({'message': 'Table added successfully!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Update table route
@bp.route('/api/tables/<int:table_id>', methods=['PUT'])
def update_table(table_id):
    data = request.json
    try:
        table = Table.query.get(table_id)
        if not table:
            return jsonify({'error': 'Table not found'}), 404

        table.name = data.get('name', table.name)
        table.description = data.get('description', table.description)
        db.session.commit()
        return jsonify({'message': 'Table updated successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Delete table route
@bp.route('/api/tables/<int:table_id>', methods=['DELETE'])
def delete_table(table_id):
    try:
        table = Table.query.get(table_id)
        if not table:
            return jsonify({'error': 'Table not found'}), 404

        db.session.delete(table)
        db.session.commit()
        return jsonify({'message': 'Table deleted successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    
@bp.route('/manage-hold-orders', methods=['GET'])
def manage_hold_orders():

    return render_template('manage_hold_orders.html')