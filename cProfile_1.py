import cProfile
from flask import Flask, request, jsonify
from models import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'  # Use SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Profiling function to wrap the app
def profile_app():
    profiler = cProfile.Profile()
    profiler.enable()  # Start profiling

    app.run(debug=True)

    profiler.disable()  # Stop profiling
    profiler.dump_stats('flask_profile.prof')  # Save the profiling results to a file

@app.route('/customers/register', methods=['POST'])
def register_customer():
    data = request.json

    # Validate required fields
    required_fields = ["username", "password", "full_name", "age", "address", "gender", "marital_status"]
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"{field} is required"}), 400

    # Check if username already exists
    if Customer.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists"}), 400

    # Create a new customer
    new_customer = Customer(
        username=data['username'],
        password=data['password'],
        full_name=data['full_name'],
        age=data['age'],
        address=data['address'],
        gender=data['gender'],
        marital_status=data['marital_status'],
    )
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({"message": "Customer registered successfully"}), 201


# Delete Customer
@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get(id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer deleted successfully"})

# Update Customer Information
@app.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    customer = Customer.query.get(id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    data = request.json
    for key, value in data.items():
        if hasattr(customer, key):  # Check if the attribute exists on the model
            setattr(customer, key, value)
    db.session.commit()
    return jsonify({"message": "Customer updated successfully"})


# Get All Customers
@app.route('/customers', methods=['GET'])
def get_all_customers():
    customers = Customer.query.all()
    return jsonify([
        {
            "id": customer.id,
            "username": customer.username,
            "full_name": customer.full_name,
            "wallet": customer.wallet,
        }
        for customer in customers
    ])


# Get Customer by Username
@app.route('/customers/<username>', methods=['GET'])
def get_customer(username):
    customer = Customer.query.filter_by(username=username).first()
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify({
        "id": customer.id,
        "username": customer.username,
        "full_name": customer.full_name,
        "wallet": customer.wallet,
        "age": customer.age,
        "address": customer.address,
        "gender": customer.gender,
        "marital_status": customer.marital_status,
    })


# Charge Customer Wallet
@app.route('/customers/<int:id>/charge', methods=['POST'])
def charge_wallet(id):
    customer = Customer.query.get(id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    amount = request.json.get('amount')
    if amount is None or amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400
    customer.wallet += amount
    db.session.commit()
    return jsonify({"message": f"Wallet charged by {amount}. New balance: {customer.wallet}"})


# Deduct Money from Wallet
@app.route('/customers/<int:id>/deduct', methods=['POST'])
def deduct_wallet(id):
    customer = Customer.query.get(id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    amount = request.json.get('amount')
    if amount is None or amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400
    if customer.wallet < amount:
        return jsonify({"error": "Insufficient funds"}), 400
    customer.wallet -= amount
    db.session.commit()
    return jsonify({"message": f"Wallet deducted by {amount}. New balance: {customer.wallet}"})


# Add Product to Inventory
@app.route('/inventory/add', methods=['POST'])
def add_product():
    data = request.json
    required_fields = ['name', 'category', 'price', 'stock']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    new_product = Product(
        name=data['name'],
        category=data['category'],
        price=data['price'],
        description=data.get('description', ""),  # Optional field
        stock=data['stock']
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"message": "Product added successfully", "product_id": new_product.id}), 201


# Deduct Goods from Inventory
@app.route('/inventory/deduct/<int:product_id>', methods=['POST'])
def deduct_product_stock(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    quantity = request.json.get('quantity')
    if quantity is None or quantity <= 0:
        return jsonify({"error": "Invalid quantity"}), 400

    if product.stock < quantity:
        return jsonify({"error": "Not enough stock available"}), 400

    product.stock -= quantity
    db.session.commit()
    return jsonify({"message": f"Deducted {quantity} items from stock. Remaining stock: {product.stock}"})


# Update Product Information
@app.route('/inventory/update/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    data = request.json
    for key, value in data.items():
        if hasattr(product, key):  # Check if the field exists in the Product model
            setattr(product, key, value)
    db.session.commit()
    return jsonify({"message": "Product updated successfully"})


# Display Available Goods
@app.route('/sales/available-goods', methods=['GET'])
def display_available_goods():
    products = Product.query.filter(Product.stock > 0).all()
    return jsonify([
        {"name": product.name, "price": product.price}
        for product in products
    ])

# 2. Get Goods Details
@app.route('/sales/good-details/<int:product_id>', methods=['GET'])
def get_good_details(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({
        "id": product.id,
        "name": product.name,
        "category": product.category,
        "price": product.price,
        "description": product.description,
        "stock": product.stock
    })


# 3. Sale: Process a Sale
@app.route('/sales/purchase', methods=['POST'])
def process_sale():
    data = request.json
    username = data.get('username')
    product_name = data.get('product_name')

    # Validate user and product
    customer = Customer.query.filter_by(username=username).first()
    product = Product.query.filter_by(name=product_name).first()

    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    if not product:
        return jsonify({"error": "Product not found"}), 404
    if product.stock <= 0:
        return jsonify({"error": "Product out of stock"}), 400
    if customer.wallet < product.price:
        return jsonify({"error": "Insufficient wallet balance"}), 400

    # Process the sale
    customer.wallet -= product.price
    product.stock -= 1
    db.session.commit()

    # Save purchase history
    new_purchase = PurchaseHistory(customer_id=customer.id, product_id=product.id)
    db.session.add(new_purchase)
    db.session.commit()

    return jsonify({
        "message": "Purchase successful",
        "remaining_wallet_balance": customer.wallet,
        "remaining_stock": product.stock
    })


# 4. Get Purchase History (Optional API)
@app.route('/sales/purchase-history/<int:customer_id>', methods=['GET'])
def get_purchase_history(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    purchases = PurchaseHistory.query.filter_by(customer_id=customer_id).all()
    history = [
        {
            "product_name": Product.query.get(purchase.product_id).name,
            "purchase_time": purchase.purchase_time
        }
        for purchase in purchases
    ]
    return jsonify(history)


# 1. Submit Review
@app.route('/reviews/submit', methods=['POST'])
def submit_review():
    data = request.json
    # Validate customer and product
    customer = Customer.query.get(data['customer_id'])
    product = Product.query.get(data['product_id'])
    if not customer or not product:
        return jsonify({"error": "Invalid customer or product ID"}), 404

    # Create a new review
    new_review = Review(
        customer_id=data['customer_id'],
        product_id=data['product_id'],
        rating=data['rating'],
        comment=data.get('comment', "")
    )
    db.session.add(new_review)
    db.session.commit()
    return jsonify({"message": "Review submitted successfully", "review_id": new_review.id}), 201

# 2. Update Review
@app.route('/reviews/update/<int:review_id>', methods=['PUT'])
def update_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    data = request.json
    review.rating = data.get('rating', review.rating)
    review.comment = data.get('comment', review.comment)
    db.session.commit()
    return jsonify({"message": "Review updated successfully"})


# 3. Delete Review
@app.route('/reviews/delete/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    db.session.delete(review)
    db.session.commit()
    return jsonify({"message": "Review deleted successfully"})


# 4. Get Product Reviews
@app.route('/reviews/product/<int:product_id>', methods=['GET'])
def get_product_reviews(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    reviews = Review.query.filter_by(product_id=product_id).all()
    return jsonify([
        {
            "review_id": review.id,
            "customer_id": review.customer_id,
            "rating": review.rating,
            "comment": review.comment
        }
        for review in reviews
    ])


# 5. Get Customer Reviews
@app.route('/reviews/customer/<int:customer_id>', methods=['GET'])
def get_customer_reviews(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    reviews = Review.query.filter_by(customer_id=customer_id).all()
    return jsonify([
        {
            "review_id": review.id,
            "product_id": review.product_id,
            "rating": review.rating,
            "comment": review.comment
        }
        for review in reviews
    ])


# 6. Moderate Review
@app.route('/reviews/moderate/<int:review_id>', methods=['PUT'])
def moderate_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    # Simulate moderation logic (e.g., flagging or approving the review)
    data = request.json
    action = data.get('action')  # Expected values: "approve", "flag"
    if action == "approve":
        return jsonify({"message": "Review approved successfully"})
    elif action == "flag":
        db.session.delete(review)  # Example: flagging removes the review
        db.session.commit()
        return jsonify({"message": "Review flagged and removed successfully"})
    else:
        return jsonify({"error": "Invalid moderation action"}), 400


# 7. Get Review Details
@app.route('/reviews/details/<int:review_id>', methods=['GET'])
def get_review_details(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    product = Product.query.get(review.product_id)
    customer = Customer.query.get(review.customer_id)
    return jsonify({
        "review_id": review.id,
        "product_name": product.name if product else "Unknown",
        "customer_username": customer.username if customer else "Unknown",
        "rating": review.rating,
        "comment": review.comment
    })

if __name__ == "__main__":
    profile_app()  # Use the profiling function to run the app
