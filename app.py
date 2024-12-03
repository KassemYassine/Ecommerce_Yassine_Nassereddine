from flask import Flask, request, jsonify, session
from models import *
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'  # Configuration for SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_string_here'  # Secret key for session encryption
db.init_app(app)

def login_required(func):
    """Decorator to enforce authentication.
    
    :param func: The function to decorate
    :type func: function
    :return: Decorated function that checks if user is logged in
    :rtype: function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return func(*args, **kwargs)
    return wrapper

import html

def sanitize_string(input_string):
    """Escapes special characters in input string to prevent XSS attacks.
    
    :param input_string: String to sanitize
    :type input_string: str, optional
    :return: Sanitized string or None if input is None
    :rtype: str or None
    """
    if input_string is not None:
        return html.escape(input_string)
    return None

@app.route('/login', methods=['POST'])
def login():
    """Handles user login with username and password.
    
    :return: JSON response indicating success or failure of login
    :rtype: tuple (json, int)
    """
    username = sanitize_string(request.json.get('username'))
    password = sanitize_string(request.json.get('password'))

    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"error": "Invalid input types for username or password"}), 400

    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        return jsonify({"message": "Logged in successfully"})
    return jsonify({"error": "Invalid username or password"}), 401

@app.route('/logout', methods=['GET'])
def logout():
    """Logs out the user by clearing the session.
    
    :return: JSON message indicating successful logout
    :rtype: json
    """
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    return jsonify({"message": "Logged out successfully"})

def roles_required(*allowed_roles):
    """Decorator to enforce role-based access control.
    
    :param allowed_roles: Allowed roles that can access the decorated function
    :type allowed_roles: tuple
    :return: Decorated function that checks user's role before allowing access
    :rtype: function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
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
    """Registers a new customer with provided details.
    
    :return: JSON response indicating success or failure of registration
    :rtype: tuple (json, int)
    """
    data = request.json
    username = sanitize_string(data.get('username'))
    password = sanitize_string(data.get('password'))
    full_name = sanitize_string(data.get('full_name'))
    address = sanitize_string(data.get('address'))
    gender = sanitize_string(data.get('gender'))
    marital_status = sanitize_string(data.get('marital_status'))

    if not isinstance(username, str) or not username:
        return jsonify({"error": "Invalid or missing username"}), 400
    if not isinstance(password, str) or not password:
        return jsonify({"error": "Invalid or missing password"}), 400

    try:
        age = int(data.get('age'))
        if age < 0 or age > 120:
            return jsonify({"error": "Invalid age"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid age"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400

    new_user = User(
        username=username,
        password=password,
        full_name=full_name,
        age=age,
        address=address,
        gender=gender,
        marital_status=marital_status,
        role="Customer"
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Customer registered successfully"}), 201



@app.route('/customers/<int:id>', methods=['DELETE'])
@login_required
@roles_required("Admin")
def delete_customer(id):
    """Deletes a customer record from the database.
    
    :param id: The unique identifier of the customer to be deleted
    :type id: int
    :return: JSON response indicating success or failure
    :rtype: tuple (json, int)
    """
    customer = User.query.get(id)
    if not customer or customer.role != "Customer":
        return jsonify({"error": "Customer not found"}), 404
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer deleted successfully"})

@app.route('/customers/<int:id>', methods=['PUT'])
@login_required
def update_customer(id):
    """Updates a customer record with provided details.
    
    :param id: The unique identifier of the customer to be updated
    :type id: int
    :return: JSON response indicating success or failure of the update
    :rtype: tuple (json, int)
    """
    user = User.query.get(session['user_id'])
    if user.role == "Customer" and user.id != id:
        return jsonify({"error": "Unauthorized access"}), 403

    customer = User.query.get(id)
    if not customer or (user.role == "Admin" and customer.role != "Customer"):
        return jsonify({"error": "Customer not found"}), 404

    data = request.json
    allowed_keys = ["full_name", "age", "address", "gender", "marital_status"]
    sanitized_data = {key: sanitize_string(data[key]) if key == "address" else data[key] for key in data if key in allowed_keys}

    if 'age' in sanitized_data:
        if not isinstance(sanitized_data['age'], int) or not (0 < sanitized_data['age'] < 150):
            return jsonify({"error": "Invalid age"}), 400

    for key, value in sanitized_data.items():
        setattr(customer, key, value)
    db.session.commit()
    return jsonify({"message": "Customer updated successfully"})

@app.route('/customers', methods=['GET'])
@login_required
@roles_required("Admin")
def get_all_customers():
    """Retrieves all customers from the database.
    
    :return: JSON list of all customers with select details
    :rtype: json
    """
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
@login_required
def get_customer(username):
    """Retrieves a single customer by username.
    
    :param username: Username of the customer to retrieve
    :type username: str
    :return: JSON object containing details of the customer or error message
    :rtype: json
    """
    current_username = session.get('username')
    current_role = session.get('role')

    user = User.query.filter_by(username=username, role="Customer").first()
    if not user:
        return jsonify({"error": "Customer not found"}), 404

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
@login_required
@roles_required("Customer")
def charge_wallet(id):
    """Credits a specified amount to the customer's wallet.
    
    :param id: The unique identifier of the customer whose wallet will be charged
    :type id: int
    :return: JSON response indicating the transaction's success and new balance
    :rtype: tuple (json, int)
    """
    current_user_id = session.get('user_id')
    customer = User.query.get(id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    if customer.id != current_user_id:
        return jsonify({"error": "Access denied"}), 403

    try:
        amount = float(request.json.get('amount'))
        if amount <= 0:
            return jsonify({"error": "Invalid amount"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount format"}), 400

    customer.wallet += amount
    db.session.commit()
    return jsonify({"message": f"Wallet charged by {amount}. New balance: {customer.wallet}"})

@app.route('/customers/<int:id>/deduct', methods=['POST'])
@login_required
@roles_required("Customer")
def deduct_wallet(id):
    """Deducts a specified amount from the customer's wallet.
    
    :param id: The unique identifier of the customer whose wallet will be deducted
    :type id: int
    :return: JSON response indicating the transaction's success and new balance
    :rtype: tuple (json, int)
    """
    current_user_id = session.get('user_id')
    customer = User.query.get(id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    if customer.id != current_user_id:
        return jsonify({"error": "Access denied"}), 403

    try:
        amount = float(request.json.get('amount'))
        if amount <= 0 or customer.wallet < amount:
            return jsonify({"error": "Invalid or insufficient amount"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount format"}), 400

    customer.wallet -= amount
    db.session.commit()
    return jsonify({"message": f"Wallet deducted by {amount}. New balance: {customer.wallet}"})

@app.route('/inventory/add', methods=['POST'])
@login_required
@roles_required("Admin")
def add_product():
    """Adds a new product to the inventory.
    
    :return: JSON response indicating the success of product addition with new product ID
    :rtype: tuple (json, int)
    """
    data = request.json
    required_fields = ['name', 'category', 'price', 'stock']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    try:
        price = float(data['price'])
        if price < 0:
            return jsonify({"error": "Price must be a positive number"}), 400
        stock = int(data['stock'])
        if stock < 0:
            return jsonify({"error": "Stock must be a non-negative integer"}), 400
    except ValueError:
        return jsonify({"error": "Invalid data format for price or stock"}), 400

    name = sanitize_string(data['name'])
    description = sanitize_string(data.get('description', ""))

    new_product = Product(
        name=name,
        category=data['category'],
        price=price,
        description=description,  
        stock=stock
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"message": "Product added successfully", "product_id": new_product.id})


@app.route('/inventory/deduct/<int:product_id>', methods=['POST'])
@login_required
@roles_required("Admin")
def deduct_product_stock(product_id):
    """Deducts a specified quantity from a product's stock.
    
    :param product_id: The unique identifier of the product
    :type product_id: int
    :return: JSON response indicating the transaction's success and new stock level
    :rtype: tuple (json, int)
    """
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    try:
        quantity = int(request.json.get('quantity'))
        if quantity <= 0:
            return jsonify({"error": "Quantity must be a positive integer"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid data format for quantity"}), 400

    if product.stock < quantity:
        return jsonify({"error": "Not enough stock available"}), 400

    product.stock -= quantity
    db.session.commit()
    return jsonify({"message": f"Deducted {quantity} items from stock. Remaining stock: {product.stock}"})


@app.route('/inventory/update/<int:product_id>', methods=['PUT'])
@login_required
@roles_required("Admin")
def update_product(product_id):
    """Updates product details based on the provided JSON data.
    
    :param product_id: The unique identifier of the product
    :type product_id: int
    :return: JSON response indicating success or failure of the update
    :rtype: tuple (json, int)
    """
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    data = request.json
    try:
        for key, value in data.items():
            if hasattr(product, key):
                if key in ['price', 'stock'] and (isinstance(value, int) or isinstance(value, float)):
                    if key == 'stock' and value < 0:
                        raise ValueError("Stock cannot be negative")
                    if key == 'price' and value < 0:
                        raise ValueError("Price cannot be negative")
                elif key in ['name', 'category', 'description']:
                    value = sanitize_string(value)
                setattr(product, key, value)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    db.session.commit()
    return jsonify({"message": "Product updated successfully"})

@app.route('/sales/available-goods', methods=['GET'])
@login_required
def display_available_goods():
    """Displays all products with available stock.
    
    :return: JSON list of products with positive stock levels
    :rtype: json
    """
    products = Product.query.filter(Product.stock > 0).all()
    return jsonify([
        {"name": product.name, "price": product.price}
        for product in products
    ])

@app.route('/sales/good-details/<int:product_id>', methods=['GET'])
@login_required
@roles_required("Admin", "Customer")
def get_good_details(product_id):
    """Fetches details of a specific product by its ID.
    
    :param product_id: The unique identifier of the product
    :type product_id: int
    :return: JSON object containing the product's details
    :rtype: json
    """
    if product_id < 1:
        return jsonify({"error": "Invalid product ID"}), 400

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
@login_required
@roles_required("Customer")
def process_sale():
    """Processes a product purchase by a customer, deducting the price from their wallet and reducing the product stock.
    
    :return: JSON response indicating success of the purchase along with remaining wallet balance and product stock
    :rtype: tuple (json, int)
    """
    data = request.json
    username = session.get('username')
    product_name = sanitize_string(data.get('product_name'))
    if not product_name:
        return jsonify({"error": "Product name is required"}), 400

    customer = User.query.filter_by(username=username, role="Customer").first()
    product = Product.query.filter_by(name=product_name).first()

    if not customer:
        return jsonify({"error": "Customer not found or not authorized"}), 404
    if not product:
        return jsonify({"error": "Product not found"}), 404
    if product.stock <= 0:
        return jsonify({"error": "Product out of stock"}), 400
    if customer.wallet < product.price:
        return jsonify({"error": "Insufficient wallet balance"}), 400

    customer.wallet -= product.price
    product.stock -= 1
    db.session.commit()

    new_purchase = PurchaseHistory(customer_id=customer.id, product_id=product.id)
    db.session.add(new_purchase)
    db.session.commit()

    return jsonify({
        "message": "Purchase successful",
        "remaining_wallet_balance": customer.wallet,
        "remaining_stock": product.stock
    })

@app.route('/sales/purchase-history/<int:customer_id>', methods=['GET'])
@login_required
@roles_required("Admin", "Customer")
def get_purchase_history(customer_id):
    """Retrieves the purchase history of a customer.
    
    :param customer_id: The unique identifier of the customer
    :type customer_id: int
    :return: JSON array of purchase history records
    :rtype: json
    """
    if session['role'] == "Customer" and session['user_id'] != customer_id:
        return jsonify({"error": "Unauthorized access to purchase history"}), 403

    customer = User.query.get(customer_id)
    if not customer or customer.role != "Customer":
        return jsonify({"error": "Customer not found"}), 404

    purchases = PurchaseHistory.query.filter_by(customer_id=customer_id).all()
    history = [
        {
            "product_name": Product.query.get(purchase.product_id).name,
            "purchase_time": purchase.purchase_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        for purchase in purchases
    ]
    return jsonify(history)

@app.route('/reviews/submit', methods=['POST'])
@login_required
@roles_required("Customer")
def submit_review():
    """Submits a product review by a customer.
    
    :return: JSON response indicating success of the review submission and the review ID
    :rtype: tuple (json, int)
    """
    data = request.json
    customer_id = session['user_id']

    try:
        product_id = int(data.get('product_id'))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid product ID. It must be an integer."}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Invalid product ID"}), 404

    try:
        rating = int(data.get('rating'))
        if not (1 <= rating <= 5):
            return jsonify({"error": "Invalid rating. Must be an integer from 1 to 5."}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid rating. It must be an integer."}), 400

    comment = sanitize_string(data.get('comment', ""))

    new_review = Review(
        customer_id=customer_id,
        product_id=product_id,
        rating=rating,
        comment=comment
    )
    db.session.add(new_review)
    db.session.commit()

    return jsonify({"message": "Review submitted successfully", "review_id": new_review.id})

@app.route('/reviews/update/<int:review_id>', methods=['PUT'])
@login_required
@roles_required("Customer")
def update_review(review_id):
    """Updates an existing review by a customer.
    
    :param review_id: The unique identifier of the review to update
    :type review_id: int
    :return: JSON response indicating success or failure of the update
    :rtype: tuple (json, int)
    """
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    if review.customer_id != session['user_id']:
        return jsonify({"error": "Unauthorized access"}), 403

    data = request.json
    rating = data.get('rating', type=int)
    if rating is not None:
        if not (1 <= rating <= 5):
            return jsonify({"error": "Invalid rating. Must be an integer from 1 to 5."}), 400
        review.rating = rating

    comment = data.get('comment')
    if comment is not None:
        review.comment = sanitize_string(comment)

    db.session.commit()
    return jsonify({"message": "Review updated successfully"})

@app.route('/reviews/delete/<int:review_id>', methods=['DELETE'])
@login_required
@roles_required("Customer")
def delete_review(review_id):
    """Deletes a review by its ID.
    
    :param review_id: The unique identifier of the review to delete
    :type review_id: int
    :return: JSON response indicating success or failure of the deletion
    :rtype: tuple (json, int)
    """
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    if review.customer_id != session['user_id']:
        return jsonify({"error": "Unauthorized access"}), 403

    db.session.delete(review)
    db.session.commit()
    return jsonify({"message": "Review deleted successfully"})

@app.route('/reviews/product/<int:product_id>', methods=['GET'])
@login_required
@roles_required("Customer", "Admin")
def get_product_reviews(product_id):
    """Fetches all reviews for a specific product.
    
    :param product_id: The unique identifier of the product
    :type product_id: int
    :return: JSON list of reviews for the product
    :rtype: json
    """
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
@login_required
@roles_required("Customer", "Admin")
def get_customer_reviews(customer_id):
    """Retrieves all reviews made by a specific customer.
    
    :param customer_id: The unique identifier of the customer
    :type customer_id: int
    :return: JSON array of reviews made by the customer
    :rtype: json
    """
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

@app.route('/reviews/flag/<int:review_id>', methods=['POST'])
@login_required
def flag_review(review_id):
    """Flags a review for moderation.
    
    :param review_id: The unique identifier of the review to flag
    :type review_id: int
    :return: JSON response indicating success or failure of the flagging
    :rtype: tuple (json, int)
    """
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    if session['user_id'] == review.customer_id:
        return jsonify({"error": "You cannot flag your own review"}), 403

    review.flagged = True
    db.session.commit()
    return jsonify({"message": "Review flagged successfully"})

@app.route('/reviews/flagged', methods=['GET'])
@login_required
@roles_required("Admin")
def get_flagged_reviews():
    """Retrieves all flagged reviews for moderation by an admin.
    
    :return: JSON array of flagged reviews
    :rtype: json
    """
    flagged_reviews = Review.query.filter_by(flagged=True).all()
    return jsonify([
        {
            "review_id": review.id,
            "product_id": review.product_id,
            "rating": review.rating,
            "comment": review.comment
        }
        for review in flagged_reviews
    ])

@app.route('/reviews/moderate/<int:review_id>', methods=['PUT'])
@login_required
@roles_required("Admin")
def moderate_review(review_id):
    """Moderates a review based on the specified action ('approve' or 'delete').
    
    :param review_id: The unique identifier of the review to moderate
    :type review_id: int
    :return: JSON response indicating the outcome of the moderation action
    :rtype: tuple (json, int)
    """
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    data = request.json
    action = data.get('action')
    if not isinstance(action, str):
        return jsonify({"error": "Invalid action type. Must be a string."}), 400

    if action == "approve":
        review.flagged = False
        db.session.commit()
        return jsonify({"message": "Review approved successfully"})
    elif action == "delete":
        db.session.delete(review)
        db.session.commit()
        return jsonify({"message": "Review deleted successfully"})
    else:
        return jsonify({"error": "Invalid moderation action"}), 400

@app.route('/reviews/details/<int:review_id>', methods=['GET'])
@login_required
@roles_required("Customer", "Admin")
def get_review_details(review_id):
    """Retrieves details of a specific review.
    
    :param review_id: The unique identifier of the review
    :type review_id: int
    :return: JSON object containing detailed information about the review
    :rtype: json
    """
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    if session['role'] == 'Admin' or session['user_id'] == review.customer_id:
        product = Product.query.get(review.product_id)
        customer = User.query.get(review.customer_id)
        return jsonify({
            "review_id": review.id,
            "product_name": product.name if product else "Unknown",
            "customer_username": customer.username,
            "rating": review.rating,
            "comment": review.comment
        })
    else:
        return jsonify({"error": "Unauthorized access"}), 403


def add_admin_user():
    """Adds an administrative user to the database if not already present.

    This function is used for initial setup or testing purposes, ensuring an admin user exists in the system.
    """
    with app.app_context():
        # Create an admin user
        admin_user = User(
            username='adminuser',
            password='secureAdminPassword',  # In a real application, you should hash this password
            full_name='Admin User',
            age=35,
            address='456 Admin St',
            gender='Male',
            marital_status='Married',
            wallet=500.0,  # Initial amount in the wallet for demonstration purposes
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
    """Main entry point of the Flask application for local development and testing.

    Sets up the database, adds an admin user, and starts the application with debug information.
    """
    with app.app_context():
        db.drop_all()  # Drops all tables in the database for a clean slate for testing
        db.create_all()  # Creates all database tables according to the defined models
        add_admin_user()  # Adds an administrative user to the database for testing
    app.run(debug=True)  # Starts the Flask application in debug mode
