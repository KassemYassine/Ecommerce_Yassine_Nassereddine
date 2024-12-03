from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    """Represents a user in the system with various attributes, including a unique username and a role determining their permissions.
    
    :param id: Unique identifier for the user
    :type id: int
    :param username: Unique username for the user
    :type username: str
    :param password: Hashed password for the user
    :type password: str
    :param full_name: Full name of the user
    :type full_name: str
    :param age: Age of the user
    :type age: int
    :param address: Residential address of the user
    :type address: str
    :param gender: Gender of the user
    :type gender: str
    :param marital_status: Marital status of the user
    :type marital_status: str
    :param wallet: Current balance in the user's wallet, defaults to 0.0
    :type wallet: float
    :param role: Role of the user in the system (e.g., Admin, Customer)
    :type role: str
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    marital_status = db.Column(db.String(20), nullable=False)
    wallet = db.Column(db.Float, default=0.0, nullable=False)
    role = db.Column(db.String(20), nullable=False)

class Product(db.Model):
    """Represents a product available for purchase in the system.
    
    :param id: Unique identifier for the product
    :type id: int
    :param name: Name of the product
    :type name: str
    :param category: Category of the product
    :type category: str
    :param price: Price of the product
    :type price: float
    :param description: Description of the product, nullable
    :type description: str
    :param stock: Quantity of the product available in stock
    :type stock: int
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(300), nullable=True)
    stock = db.Column(db.Integer, nullable=False)

class Review(db.Model):
    """Represents a review written by a user for a product.
    
    :param id: Unique identifier for the review
    :type id: int
    :param product_id: Foreign key to the product being reviewed
    :type product_id: int
    :param customer_id: Foreign key to the user who wrote the review
    :type customer_id: int
    :param rating: Numerical rating given to the product
    :type rating: int
    :param comment: Optional text comment for the review
    :type comment: str
    :param flagged: Boolean indicating whether the review has been flagged for moderation, defaults to False
    :type flagged: bool
    """
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(300), nullable=True)
    flagged = db.Column(db.Boolean, default=False)

class PurchaseHistory(db.Model):
    """Tracks purchase history of users for products.
    
    :param id: Unique identifier for the purchase record
    :type id: int
    :param customer_id: Foreign key to the user who made the purchase
    :type customer_id: int
    :param product_id: Foreign key to the product that was purchased
    :type product_id: int
    :param purchase_time: Timestamp when the purchase was made, defaults to the current time
    :type purchase_time: datetime
    """
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    purchase_time = db.Column(db.DateTime, default=db.func.now())
