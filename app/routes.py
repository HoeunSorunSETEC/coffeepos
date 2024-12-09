from flask import Blueprint, render_template, request, jsonify
from . import db
from .models import Product, Order, OrderDetail, db,Category
from werkzeug.utils import secure_filename
import os
from flask import current_app


bp = Blueprint('main', __name__)

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

# Route to store an order
@bp.route('/api/orders', methods=['POST'])
def store_order():
    data = request.json
    try:
        # Create a new order
        subtotal = sum(item['price'] * item['quantity'] for item in data['items'])
        tax = subtotal * 0.1
        total_price = subtotal + tax

        order = Order(total_price=total_price, tax=tax)
        db.session.add(order)
        db.session.commit()

        # Add order details
        for item in data['items']:
            order_detail = OrderDetail(
                order_id=order.id,
                product_id=item['product_id'],
                sugar_level=item['sugar_level'],
                quantity=item['quantity'],
                price=item['price']
            )
            db.session.add(order_detail)

        db.session.commit()
        return jsonify({'message': 'Order created successfully!', 'order_id': order.id}), 201
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
