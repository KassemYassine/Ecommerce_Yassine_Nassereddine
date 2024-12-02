from flask import Flask, request, jsonify,session
from models import *
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'  # Use SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_string_here'
db.init_app(app)
from functools import wraps
from flask import request, jsonify
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return func(*args, **kwargs)
    return wrapper

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')  # In production, use hashed passwords
    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        return jsonify({"message": "Logged in successfully"})
    return jsonify({"error": "Invalid username or password"}), 401

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    return jsonify({"message": "Logged out successfully"})

def roles_required(*allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Assume the username is obtained from a secure token or session
            username = request.headers.get('username')
            if not username:
                return jsonify({"error": "Authentication required"}), 401
            
            user = User.query.filter_by(username=username).first()
            if not user or user.role not in allowed_roles:
                return jsonify({"error": "Access denied. Insufficient privileges."}), 403
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


@app.route('/customers/register', methods=['POST'])
def register_customer():
    data = request.json
    # Check if username already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists"}), 400
    # Create a new user (role: Customer)
    new_user = User(
        username=data['username'],
        password=data['password'],
        full_name=data['full_name'],
        age=data['age'],
        address=data['address'],
        gender=data['gender'],
        marital_status=data['marital_status'],
        role="Customer"  # Explicitly set the role to 'Customer'
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Customer registered successfully"}), 201

@app.route('/customers/<int:id>', methods=['DELETE'])
@login_required  # Ensure the user is logged in
@roles_required("Admin")  # Ensure the user is an admin
def delete_customer(id):
    customer = User.query.get(id)
    if not customer or customer.role != "Customer":
        return jsonify({"error": "Customer not found"}), 404
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer deleted successfully"})

@app.route('/customers/<int:id>', methods=['PUT'])
@login_required  # Ensure the user is logged in
def update_customer(id):
    user = User.query.get(session['user_id'])
    if user.role == "Customer" and user.id != id:
        return jsonify({"error": "Unauthorized access"}), 403

    customer = User.query.get(id)
    if not customer or (user.role == "Admin" and customer.role != "Customer"):
        return jsonify({"error": "Customer not found"}), 404
    
    data = request.json
    for key, value in data.items():
        if hasattr(customer, key):
            setattr(customer, key, value)
    db.session.commit()
    return jsonify({"message": "Customer updated successfully"})

@app.route('/customers', methods=['GET'])
@login_required  # Ensure the user is logged in
@roles_required("Admin")  # Ensure the user has admin privileges
def get_all_customers():
    customers = User.query.filter_by(role="Customer").all()
    return jsonify([
        {
            "id": customer.id,
            "username": customer.username,
            "full_name": customer.full_name,
            "wallet": customer.wallet,
        }
        for customer in customers
    ])

@app.route('/customers/<username>', methods=['GET'])
@login_required  # Ensure the user is logged in
def get_customer(username):
    # Access the user session to identify the current user and their role
    current_username = session.get('username')
    current_role = session.get('role')

    # Query the user information based on the username provided in the path
    user = User.query.filter_by(username=username, role="Customer").first()

    # Ensure the user exists
    if not user:
        return jsonify({"error": "Customer not found"}), 404

    # Check if the current user is the same as the requested user or if the current user is an admin
    if user.username == current_username or current_role == "Admin":
        return jsonify({
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "wallet": user.wallet,
            "age": user.age,
            "address": user.address,
            "gender": user.gender,
            "marital_status": user.marital_status,
        })
    else:
        return jsonify({"error": "Access denied"}), 403



@app.route('/customers/<int:id>/charge', methods=['POST'])
@login_required  # Ensure the user is logged in
@roles_required("Customer")  # Ensure the user is a customer
def charge_wallet(id):
    # Access the current user's ID from the session to ensure they are only modifying their own account
    current_user_id = session.get('user_id')

    # Retrieve the customer to be charged
    customer = User.query.get(id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    # Check if the customer's ID matches the logged-in user's ID
    if customer.id != current_user_id:
        return jsonify({"error": "Access denied"}), 403

    # Get the amount to be charged from the request
    amount = request.json.get('amount')
    if amount is None or amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400

    # Update the wallet amount
    customer.wallet += amount
    db.session.commit()
    return jsonify({"message": f"Wallet charged by {amount}. New balance: {customer.wallet}"})

@app.route('/customers/<int:id>/deduct', methods=['POST'])
@login_required  # Ensure the user is logged in
@roles_required("Customer")  # Ensure the user is a customer
def deduct_wallet(id):
    # Access the current user's ID from the session to ensure they are only modifying their own account
    current_user_id = session.get('user_id')

    # Retrieve the customer whose wallet will be deducted
    customer = User.query.get(id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    # Check if the customer's ID matches the logged-in user's ID
    if customer.id != current_user_id:
        return jsonify({"error": "Access denied"}), 403

    # Get the amount to be deducted from the request
    amount = request.json.get('amount')
    if amount is None or amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400
    if customer.wallet < amount:
        return jsonify({"error": "Insufficient funds"}), 400

    # Update the wallet amount
    customer.wallet -= amount
    db.session.commit()
    return jsonify({"message": f"Wallet deducted by {amount}. New balance: {customer.wallet}"})

@app.route('/inventory/add', methods=['POST'])
@login_required  # Ensure the user is logged in
@roles_required("Admin")  # Ensure the user is an admin
def add_product():
    data = request.json
    # Validate input data
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
    return jsonify({"message": "Product added successfully", "product_id": new_product.id})


@app.route('/inventory/deduct/<int:product_id>', methods=['POST'])
@login_required  # Ensure the user is logged in
@roles_required("Admin")  # Ensure the user is an admin
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


@app.route('/inventory/update/<int:product_id>', methods=['PUT'])
@login_required  # Ensure the user is logged in
@roles_required("Admin")  # Ensure the user is an admin
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    data = request.json
    # Update only the fields provided in the request
    for key, value in data.items():
        if hasattr(product, key):  # Check if the field exists in the Product model
            setattr(product, key, value)
    db.session.commit()
    return jsonify({"message": "Product updated successfully"})

@app.route('/sales/available-goods', methods=['GET'])
@login_required  # Ensure the user is logged in
def display_available_goods():
    products = Product.query.filter(Product.stock > 0).all()
    return jsonify([
        {"name": product.name, "price": product.price}
        for product in products
    ])



# 2. Get Goods Details
@app.route('/sales/good-details/<int:product_id>', methods=['GET'])
@login_required  # Ensure the user is logged in
@roles_required("Admin", "Customer")  # Access limited to Admins and Customers
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

@app.route('/sales/purchase', methods=['POST'])
@login_required  # Ensure the user is logged in
@roles_required("Customer")  # Access limited to Customers
def process_sale():
    data = request.json
    # Use the session to retrieve the username instead of expecting it in the request
    username = session.get('username')

    product_name = data.get('product_name')

    # Validate user and product
    customer = User.query.filter_by(username=username, role="Customer").first()  # Ensure the user is a Customer
    product = Product.query.filter_by(name=product_name).first()

    if not customer:
        return jsonify({"error": "Customer not found or not authorized"}), 404
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


@app.route('/sales/purchase-history/<int:customer_id>', methods=['GET'])
@login_required  # Ensure the user is logged in
@roles_required("Admin", "Customer")  # Allow both roles, but apply additional checks inside
def get_purchase_history(customer_id):
    # Check if the logged-in user is an admin or the customer that matches the ID in the path
    if session['role'] == "Customer" and session['user_id'] != customer_id:
        return jsonify({"error": "Unauthorized access to purchase history"}), 403

    customer = User.query.get(customer_id)
    if not customer or customer.role != "Customer":  # Ensure it is a valid customer
        return jsonify({"error": "Customer not found"}), 404

    purchases = PurchaseHistory.query.filter_by(customer_id=customer_id).all()
    history = [
        {
            "product_name": Product.query.get(purchase.product_id).name,
            "purchase_time": purchase.purchase_time.strftime('%Y-%m-%d %H:%M:%S')  # Format datetime for readability
        }
        for purchase in purchases
    ]
    return jsonify(history)

# 1. Submit Review
@app.route('/reviews/submit', methods=['POST'])
@login_required  # Ensure the user is logged in
@roles_required("Customer")  # Ensure the user is a Customer
def submit_review():
    data = request.json
    # Fetch the user ID from the session to ensure the logged-in user is creating the review
    customer_id = session['user_id']
    product_id = data.get('product_id')
    
    # Validate product existence
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Invalid product ID"}), 404

    # Create a new review with the logged-in customer's ID
    new_review = Review(
        customer_id=customer_id,  # Use the session user_id instead of passing it in the request
        product_id=product_id,
        rating=data.get('rating'),
        comment=data.get('comment', "")
    )
    db.session.add(new_review)
    db.session.commit()
    return jsonify({"message": "Review submitted successfully", "review_id": new_review.id}), 201


@app.route('/reviews/update/<int:review_id>', methods=['PUT'])
@login_required  # Ensure the user is logged in
@roles_required("Customer")  # Ensure the user is a Customer
def update_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    # Check if the logged-in user is the owner of the review
    if review.customer_id != session['user_id']:
        return jsonify({"error": "Unauthorized access"}), 403

    data = request.json
    review.rating = data.get('rating', review.rating)
    review.comment = data.get('comment', review.comment)
    db.session.commit()
    return jsonify({"message": "Review updated successfully"})


@app.route('/reviews/delete/<int:review_id>', methods=['DELETE'])
@login_required  # Ensure the user is logged in
@roles_required("Customer")  # Ensure the user is a Customer
def delete_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    # Check if the logged-in user is the owner of the review
    if review.customer_id != session['user_id']:
        return jsonify({"error": "Unauthorized access"}), 403

    db.session.delete(review)
    db.session.commit()
    return jsonify({"message": "Review deleted successfully"})


@app.route('/reviews/product/<int:product_id>', methods=['GET'])
@roles_required("Customer", "Admin")
@login_required
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



@app.route('/reviews/customer/<int:customer_id>', methods=['GET'])
@roles_required("Customer", "Admin")
@login_required
def get_customer_reviews(customer_id):
    # Admins can access any customer's reviews, customers can only access their own
    if session['role'] == 'Admin' or session['user_id'] == customer_id:
        customer = User.query.get(customer_id)
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
    else:
        return jsonify({"error": "Unauthorized access"}), 403



@app.route('/reviews/moderate/<int:review_id>', methods=['PUT'])
@login_required  # Ensure the user is logged in
@roles_required("Admin")  # Ensure the user is an admin
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


@app.route('/reviews/details/<int:review_id>', methods=['GET'])
@login_required  # Ensure the user is logged in
@roles_required("Customer", "Admin")  # Ensure the user has the correct role
def get_review_details(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    # Ensure customers can only see their own reviews, while admins can see any review
    if session['role'] == 'Admin' or session['user_id'] == review.customer_id:
        product = Product.query.get(review.product_id)
        customer = User.query.get(review.customer_id)  # Use the User model
        return jsonify({
            "review_id": review.id,
            "product_name": product.name if product else "Unknown",
            "customer_username": customer.username,
            "rating": review.rating,
            "comment": review.comment
        })
    else:
        return jsonify({"error": "Unauthorized access"}), 403


# -------------------------------
# Main Entry Point
# -------------------------------
# FUNCTION FOR TESTING 
def add_admin_user():
    with app.app_context():
        # Create an admin user
        admin_user = User(
            username='adminuser',
            password='secureAdminPassword',  # You should hash this password in a real application
            full_name='Admin User',
            age=35,
            address='456 Admin St',
            gender='Male',
            marital_status='Married',
            wallet=500.0,  # Initial amount in the wallet for demonstration
            role='Admin'
        )
        
        # Check if the user already exists to avoid duplicates
        existing_user = User.query.filter_by(username='adminuser').first()
        if existing_user is None:
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user added successfully!")
        else:
            print("Admin user already exists.")
if __name__ == "__main__":
    with app.app_context():
        db.drop_all()#for testing
        db.create_all()
        add_admin_user()  # Ensure database tables are created
    app.run(debug=True)