import pytest
import sys
import os

# Add the project root to sys.path
sys.path.append(r"C:\Users\TechTroniX\Desktop\435L_project")

from Ecommerce_Yassine_Nassereddine.app import app, db
from Ecommerce_Yassine_Nassereddine.models import Customer, Product, PurchaseHistory, Review


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory database for tests
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()

def test_register_customer(client):
    """Test the /customers/register POST endpoint."""

    # Ensure database setup for the test
    with app.app_context():
        db.create_all()

    try:
        # Successful customer registration
        response = client.post('/customers/register', json={
            "username": "new_user",
            "password": "securepassword",
            "full_name": "John Doe",
            "age": 30,
            "address": "123 Main St",
            "gender": "Male",
            "marital_status": "Single"
        })
        assert response.status_code == 201
        assert response.json["message"] == "Customer registered successfully"

        # Verify the customer is added to the database
        with app.app_context():
            customer = Customer.query.filter_by(username="new_user").first()
            assert customer is not None
            assert customer.username == "new_user"

        # Attempt to register a customer with an existing username
        response_duplicate = client.post('/customers/register', json={
            "username": "new_user",  # Duplicate username
            "password": "anotherpassword",
            "full_name": "Jane Smith",
            "age": 25,
            "address": "456 Another St",
            "gender": "Female",
            "marital_status": "Married"
        })
        assert response_duplicate.status_code == 400
        assert response_duplicate.json["error"] == "Username already exists"

        # Attempt to register a customer with missing fields
        response_missing_fields = client.post('/customers/register', json={
            "username": "incomplete_user",
            "password": "password123",
        })
        assert response_missing_fields.status_code == 400
        assert "is required" in response_missing_fields.json["error"]

    finally:
        # Clean up the database after the test
        with app.app_context():
            db.session.remove()
            db.drop_all()



def test_delete_customer(client):
    """Test the /customers/<int:id> DELETE endpoint."""
    
    # Add a sample customer to the database
    with app.app_context():
        customer = Customer(
            username="delete_user",
            password="test_pass123",
            full_name="Delete User",
            age=25,
            address="456 Test Ave",
            gender="Female",
            marital_status="Single",
            wallet=50.0
        )
        db.session.add(customer)
        db.session.commit()
        customer_id = customer.id

    # Successful deletion
    response = client.delete(f'/customers/{customer_id}')
    assert response.status_code == 200
    assert response.json['message'] == "Customer deleted successfully"

    # Attempt to delete a non-existent customer
    response_not_found = client.delete(f'/customers/{customer_id}')
    assert response_not_found.status_code == 404
    assert response_not_found.json['error'] == "Customer not found"

def test_update_customer(client):
    """Test the /customers/<int:id> PUT endpoint."""
    
    # Add a sample customer to the database
    with app.app_context():
        customer = Customer(
            username="update_user",
            password="test_pass123",
            full_name="Update User",
            age=28,
            address="789 Test Blvd",
            gender="Male",
            marital_status="Single",
            wallet=100.0
        )
        db.session.add(customer)
        db.session.commit()
        customer_id = customer.id

    # Successful update
    response = client.put(f'/customers/{customer_id}', json={
        "full_name": "Updated Name",
        "age": 30,
        "address": "Updated Address"
    })
    assert response.status_code == 200
    assert response.json['message'] == "Customer updated successfully"

    # Verify the changes in the database
    with app.app_context():
        updated_customer = Customer.query.get(customer_id)
        assert updated_customer.full_name == "Updated Name"
        assert updated_customer.age == 30
        assert updated_customer.address == "Updated Address"

    # Attempt to update a non-existent customer
    response_not_found = client.put(f'/customers/9999', json={
        "full_name": "Non Existent"
    })
    assert response_not_found.status_code == 404
    assert response_not_found.json['error'] == "Customer not found"

def test_get_all_customers(client):
    """Test the /customers GET endpoint."""
    
    # Add sample customers to the database
    with app.app_context():
        customer1 = Customer(
            username="user1",
            password="pass1",
            full_name="User One",
            age=25,
            address="123 First St",
            gender="Male",
            marital_status="Single",
            wallet=100.0
        )
        customer2 = Customer(
            username="user2",
            password="pass2",
            full_name="User Two",
            age=30,
            address="456 Second St",
            gender="Female",
            marital_status="Married",
            wallet=200.0
        )
        db.session.add_all([customer1, customer2])
        db.session.commit()

    # Send GET request to fetch all customers
    response = client.get('/customers')
    assert response.status_code == 200

    # Verify the response contains both customers
    data = response.json
    assert len(data) == 2

    # Check the details of the first customer
    assert data[0]['username'] == "user1"
    assert data[0]['full_name'] == "User One"
    assert data[0]['wallet'] == 100.0

    # Check the details of the second customer
    assert data[1]['username'] == "user2"
    assert data[1]['full_name'] == "User Two"
    assert data[1]['wallet'] == 200.0

def test_get_customer_by_username(client):
    """Test the /customers/<username> GET endpoint."""
    
    # Add a sample customer to the database
    with app.app_context():
        customer = Customer(
            username="test_user",
            password="test_pass",
            full_name="Test User",
            age=30,
            address="123 Test St",
            gender="Male",
            marital_status="Single",
            wallet=100.0
        )
        db.session.add(customer)
        db.session.commit()

    # Successful retrieval of the customer
    response = client.get('/customers/test_user')
    assert response.status_code == 200

    data = response.json
    assert data['username'] == "test_user"
    assert data['full_name'] == "Test User"
    assert data['age'] == 30
    assert data['address'] == "123 Test St"
    assert data['gender'] == "Male"
    assert data['marital_status'] == "Single"
    assert data['wallet'] == 100.0

    # Attempt to retrieve a non-existent customer
    response_not_found = client.get('/customers/non_existent_user')
    assert response_not_found.status_code == 404
    assert response_not_found.json['error'] == "Customer not found"

def test_charge_customer_wallet(client):
    """Test the /customers/<int:id>/charge POST endpoint."""
    
    # Add a sample customer to the database
    with app.app_context():
        customer = Customer(
            username="wallet_user",
            password="test_pass",
            full_name="Wallet User",
            age=30,
            address="456 Wallet St",
            gender="Male",
            marital_status="Single",
            wallet=100.0
        )
        db.session.add(customer)
        db.session.commit()
        customer_id = customer.id

    # Successful wallet charging
    response = client.post(f'/customers/{customer_id}/charge', json={"amount": 50})
    assert response.status_code == 200
    assert response.json['message'] == "Wallet charged by 50. New balance: 150.0"

    # Verify the wallet amount in the database
    with app.app_context():
        updated_customer = Customer.query.get(customer_id)
        assert updated_customer.wallet == 150.0

    # Attempt to charge a non-existent customer
    response_not_found = client.post('/customers/9999/charge', json={"amount": 50})
    assert response_not_found.status_code == 404
    assert response_not_found.json['error'] == "Customer not found"

    # Attempt to charge with an invalid amount (negative value)
    response_invalid_amount = client.post(f'/customers/{customer_id}/charge', json={"amount": -10})
    assert response_invalid_amount.status_code == 400
    assert response_invalid_amount.json['error'] == "Invalid amount"

    # Attempt to charge with an invalid amount (zero)
    response_zero_amount = client.post(f'/customers/{customer_id}/charge', json={"amount": 0})
    assert response_zero_amount.status_code == 400
    assert response_zero_amount.json['error'] == "Invalid amount"

def test_deduct_customer_wallet(client):
    """Test the /customers/<int:id>/deduct POST endpoint."""
    
    # Add a sample customer to the database
    with app.app_context():
        customer = Customer(
            username="deduct_user",
            password="test_pass",
            full_name="Deduct User",
            age=30,
            address="123 Deduct St",
            gender="Male",
            marital_status="Single",
            wallet=100.0
        )
        db.session.add(customer)
        db.session.commit()
        customer_id = customer.id

    # Successful wallet deduction
    response = client.post(f'/customers/{customer_id}/deduct', json={"amount": 50})
    assert response.status_code == 200
    assert response.json['message'] == "Wallet deducted by 50. New balance: 50.0"

    # Verify the wallet amount in the database
    with app.app_context():
        updated_customer = Customer.query.get(customer_id)
        assert updated_customer.wallet == 50.0

    # Attempt to deduct money from a non-existent customer
    response_not_found = client.post('/customers/9999/deduct', json={"amount": 50})
    assert response_not_found.status_code == 404
    assert response_not_found.json['error'] == "Customer not found"

    # Attempt to deduct with an invalid amount (negative value)
    response_invalid_amount = client.post(f'/customers/{customer_id}/deduct', json={"amount": -10})
    assert response_invalid_amount.status_code == 400
    assert response_invalid_amount.json['error'] == "Invalid amount"

    # Attempt to deduct with an invalid amount (zero)
    response_zero_amount = client.post(f'/customers/{customer_id}/deduct', json={"amount": 0})
    assert response_zero_amount.status_code == 400
    assert response_zero_amount.json['error'] == "Invalid amount"

    # Attempt to deduct more than the available balance
    response_insufficient_funds = client.post(f'/customers/{customer_id}/deduct', json={"amount": 100})
    assert response_insufficient_funds.status_code == 400
    assert response_insufficient_funds.json['error'] == "Insufficient funds"


def test_add_product(client):
    """Test the /inventory/add POST endpoint."""
    
    # Successful product addition
    response = client.post('/inventory/add', json={
        "name": "Test Product",
        "category": "Electronics",
        "price": 99.99,
        "stock": 10,
        "description": "A test product"  # Optional field
    })
    assert response.status_code == 201
    assert response.json['message'] == "Product added successfully"
    assert "product_id" in response.json

    # Verify the product exists in the database
    with app.app_context():
        product_id = response.json['product_id']
        product = Product.query.get(product_id)
        assert product is not None
        assert product.name == "Test Product"
        assert product.category == "Electronics"
        assert product.price == 99.99
        assert product.stock == 10
        assert product.description == "A test product"

    # Attempt to add a product with missing required fields
    response_missing_fields = client.post('/inventory/add', json={
        "name": "Incomplete Product",
        # Missing 'category', 'price', 'stock'
    })
    assert response_missing_fields.status_code == 400
    assert response_missing_fields.json['error'] == "category is required"  # First missing field error

def test_deduct_product_stock(client):
    """Test the /inventory/deduct/<int:product_id> POST endpoint."""
    
    # Add a sample product to the database
    with app.app_context():
        product = Product(
            name="Test Product",
            category="Electronics",
            price=49.99,
            stock=10
        )
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    # Successful stock deduction
    response = client.post(f'/inventory/deduct/{product_id}', json={"quantity": 5})
    assert response.status_code == 200
    assert response.json['message'] == "Deducted 5 items from stock. Remaining stock: 5"

    # Verify the stock in the database
    with app.app_context():
        updated_product = Product.query.get(product_id)
        assert updated_product.stock == 5

    # Attempt to deduct stock for a non-existent product
    response_not_found = client.post('/inventory/deduct/9999', json={"quantity": 5})
    assert response_not_found.status_code == 404
    assert response_not_found.json['error'] == "Product not found"

    # Attempt to deduct with an invalid quantity (negative value)
    response_invalid_quantity = client.post(f'/inventory/deduct/{product_id}', json={"quantity": -3})
    assert response_invalid_quantity.status_code == 400
    assert response_invalid_quantity.json['error'] == "Invalid quantity"

    # Attempt to deduct with an invalid quantity (zero)
    response_zero_quantity = client.post(f'/inventory/deduct/{product_id}', json={"quantity": 0})
    assert response_zero_quantity.status_code == 400
    assert response_zero_quantity.json['error'] == "Invalid quantity"

    # Attempt to deduct more than the available stock
    response_insufficient_stock = client.post(f'/inventory/deduct/{product_id}', json={"quantity": 10})
    assert response_insufficient_stock.status_code == 400
    assert response_insufficient_stock.json['error'] == "Not enough stock available"

def test_update_product(client):
    """Test the /inventory/update/<int:product_id> PUT endpoint."""
    
    # Add a sample product to the database
    with app.app_context():
        product = Product(
            name="Original Product",
            category="Electronics",
            price=99.99,
            stock=10
        )
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    # Successful product update
    response = client.put(f'/inventory/update/{product_id}', json={
        "name": "Updated Product",
        "price": 79.99,
        "stock": 15
    })
    assert response.status_code == 200
    assert response.json['message'] == "Product updated successfully"

    # Verify the changes in the database
    with app.app_context():
        updated_product = Product.query.get(product_id)
        assert updated_product.name == "Updated Product"
        assert updated_product.price == 79.99
        assert updated_product.stock == 15

    # Attempt to update a non-existent product
    response_not_found = client.put('/inventory/update/9999', json={
        "name": "Non-existent Product"
    })
    assert response_not_found.status_code == 404
    assert response_not_found.json['error'] == "Product not found"

def test_display_available_goods(client):
    """Test the /sales/available-goods GET endpoint."""
    
    # Add sample products to the database
    with app.app_context():
        product1 = Product(
            name="Available Product 1",
            category="Books",
            price=19.99,
            stock=5
        )
        product2 = Product(
            name="Available Product 2",
            category="Clothing",
            price=49.99,
            stock=0  # Out of stock
        )
        db.session.add_all([product1, product2])
        db.session.commit()

    # Send GET request to fetch available goods
    response = client.get('/sales/available-goods')
    assert response.status_code == 200

    # Verify the response contains only products with stock > 0
    data = response.json
    assert len(data) == 1
    assert data[0]['name'] == "Available Product 1"
    assert data[0]['price'] == 19.99

def test_display_available_goods(client):
    """Test the /sales/available-goods GET endpoint."""

    # Add sample products to the database
    with app.app_context():
        product1 = Product(
            name="Product 1",
            category="Electronics",
            price=99.99,
            stock=10
        )
        product2 = Product(
            name="Product 2",
            category="Books",
            price=20.00,
            stock=0  # Out of stock, should not appear in the results
        )
        product3 = Product(
            name="Product 3",
            category="Home Appliances",
            price=50.00,
            stock=5
        )
        db.session.add_all([product1, product2, product3])
        db.session.commit()

    # Call the endpoint
    response = client.get('/sales/available-goods')

    # Check response status code
    assert response.status_code == 200

    # Check response data
    data = response.json
    assert len(data) == 2  # Only products with stock > 0 should appear
    assert data[0]["name"] == "Product 1"
    assert data[0]["price"] == 99.99
    assert data[1]["name"] == "Product 3"
    assert data[1]["price"] == 50.00


def test_get_good_details(client):
    """Test the /sales/good-details/<int:product_id> GET endpoint."""
    
    # Add a sample product to the database
    with app.app_context():
        product = Product(
            name="Test Product",
            category="Electronics",
            price=99.99,
            description="A detailed description of the test product.",
            stock=10
        )
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    # Successful retrieval of product details
    response = client.get(f'/sales/good-details/{product_id}')
    assert response.status_code == 200

    data = response.json
    assert data['id'] == product_id
    assert data['name'] == "Test Product"
    assert data['category'] == "Electronics"
    assert data['price'] == 99.99
    assert data['description'] == "A detailed description of the test product."
    assert data['stock'] == 10

    # Attempt to retrieve a non-existent product
    response_not_found = client.get('/sales/good-details/9999')
    assert response_not_found.status_code == 404
    assert response_not_found.json['error'] == "Product not found"

def test_process_sale(client):
    """Test the /sales/purchase POST endpoint."""
    
    # Add a sample customer and product to the database
    with app.app_context():
        customer = Customer(
            username="test_customer",
            password="test_pass",
            full_name="Test Customer",
            age=30,
            address="123 Test St",
            gender="Male",
            marital_status="Single",
            wallet=100.0
        )
        product = Product(
            name="Test Product",
            category="Electronics",
            price=49.99,
            stock=5
        )
        db.session.add(customer)
        db.session.add(product)
        db.session.commit()

        # Capture customer ID and product ID
        customer_id = customer.id
        product_id = product.id

    # Successful purchase
    response = client.post('/sales/purchase', json={
        "username": "test_customer",
        "product_name": "Test Product"
    })
    assert response.status_code == 200
    assert response.json['message'] == "Purchase successful"
    assert response.json['remaining_wallet_balance'] == 50.01  # Wallet balance after purchase
    assert response.json['remaining_stock'] == 4  # Stock after purchase

    # Verify purchase history
    with app.app_context():
        purchase_history = PurchaseHistory.query.filter_by(
            customer_id=customer_id, product_id=product_id
        ).all()
        assert len(purchase_history) == 1

    # Attempt to purchase with a non-existent customer
    response_no_customer = client.post('/sales/purchase', json={
        "username": "non_existent_customer",
        "product_name": "Test Product"
    })
    assert response_no_customer.status_code == 404
    assert response_no_customer.json['error'] == "Customer not found"

    # Attempt to purchase with a non-existent product
    response_no_product = client.post('/sales/purchase', json={
        "username": "test_customer",
        "product_name": "Non Existent Product"
    })
    assert response_no_product.status_code == 404
    assert response_no_product.json['error'] == "Product not found"

    # Attempt to purchase when the product is out of stock
    with app.app_context():
        product = Product.query.get(product_id)
        product.stock = 0
        db.session.commit()

    response_out_of_stock = client.post('/sales/purchase', json={
        "username": "test_customer",
        "product_name": "Test Product"
    })
    assert response_out_of_stock.status_code == 400
    assert response_out_of_stock.json['error'] == "Product out of stock"

    # Attempt to purchase with insufficient wallet balance
    with app.app_context():
        product = Product.query.get(product_id)
        product.stock = 5  # Restock the product
        db.session.commit()

        customer = Customer.query.get(customer_id)
        customer.wallet = 10.0  # Insufficient balance
        db.session.commit()

    response_insufficient_balance = client.post('/sales/purchase', json={
        "username": "test_customer",
        "product_name": "Test Product"
    })
    assert response_insufficient_balance.status_code == 400
    assert response_insufficient_balance.json['error'] == "Insufficient wallet balance"

def test_get_purchase_history(client):
    """Test the /sales/purchase-history/<int:customer_id> GET endpoint."""
    
    # Add a sample customer, product, and purchase history to the database
    with app.app_context():
        customer = Customer(
            username="history_user",
            password="test_pass",
            full_name="History User",
            age=30,
            address="123 History St",
            gender="Male",
            marital_status="Single",
            wallet=100.0
        )
        product = Product(
            name="History Product",
            category="Electronics",
            price=49.99,
            stock=5
        )
        db.session.add(customer)
        db.session.add(product)
        db.session.commit()

        # Store customer_id and product_id for later use
        customer_id = customer.id
        product_id = product.id

        # Add a purchase to the purchase history
        purchase = PurchaseHistory(customer_id=customer_id, product_id=product_id)
        db.session.add(purchase)
        db.session.commit()

    # Successful retrieval of purchase history
    response = client.get(f'/sales/purchase-history/{customer_id}')
    assert response.status_code == 200

    data = response.json
    assert len(data) == 1
    assert data[0]['product_name'] == "History Product"
    assert 'purchase_time' in data[0]  # Ensure the purchase time is included

    # Attempt to retrieve purchase history for a non-existent customer
    response_not_found = client.get('/sales/purchase-history/9999')
    assert response_not_found.status_code == 404
    assert response_not_found.json['error'] == "Customer not found"


def test_submit_review(client):
    """Test the /reviews/submit POST endpoint."""

    # Add a sample customer and product to the database
    with app.app_context():
        customer = Customer(
            username="review_user",
            password="test_pass",
            full_name="Review User",
            age=30,
            address="123 Review St",
            gender="Male",
            marital_status="Single",
            wallet=100.0
        )
        product = Product(
            name="Review Product",
            category="Electronics",
            price=49.99,
            stock=5
        )
        db.session.add(customer)
        db.session.add(product)
        db.session.commit()

        # Capture the IDs after committing
        customer_id = customer.id
        product_id = product.id

    # Successful review submission
    response = client.post('/reviews/submit', json={
        "customer_id": customer_id,
        "product_id": product_id,
        "rating": 5,
        "comment": "Great product!"
    })
    assert response.status_code == 201
    assert response.json['message'] == "Review submitted successfully"
    assert "review_id" in response.json

    # Verify the review exists in the database
    with app.app_context():
        review_id = response.json['review_id']
        review = Review.query.get(review_id)
        assert review is not None
        assert review.customer_id == customer_id
        assert review.product_id == product_id
        assert review.rating == 5
        assert review.comment == "Great product!"

    # Attempt to submit a review with invalid customer or product ID
    response_invalid_ids = client.post('/reviews/submit', json={
        "customer_id": 9999,  # Invalid customer ID
        "product_id": 9999,  # Invalid product ID
        "rating": 4,
        "comment": "Invalid review!"
    })
    assert response_invalid_ids.status_code == 404
    assert response_invalid_ids.json['error'] == "Invalid customer or product ID"



def test_update_review(client):
    """Test the /reviews/update/<int:review_id> PUT endpoint."""
    
    # Add a sample customer, product, and review to the database
    with app.app_context():
        customer = Customer(
            username="update_review_user",
            password="test_pass",
            full_name="Update Review User",
            age=30,
            address="123 Update St",
            gender="Male",
            marital_status="Single",
            wallet=100.0
        )
        product = Product(
            name="Update Review Product",
            category="Electronics",
            price=49.99,
            stock=5
        )
        db.session.add(customer)
        db.session.add(product)
        db.session.commit()

        review = Review(
            customer_id=customer.id,
            product_id=product.id,
            rating=4,
            comment="Good product."
        )
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    # Successful review update
    response = client.put(f'/reviews/update/{review_id}', json={
        "rating": 5,
        "comment": "Excellent product!"
    })
    assert response.status_code == 200
    assert response.json['message'] == "Review updated successfully"

    # Verify the review was updated in the database
    with app.app_context():
        updated_review = Review.query.get(review_id)
        assert updated_review.rating == 5
        assert updated_review.comment == "Excellent product!"

    # Attempt to update a non-existent review
    response_not_found = client.put('/reviews/update/9999', json={
        "rating": 3,
        "comment": "Non-existent review"
    })
    assert response_not_found.status_code == 404
    assert response_not_found.json['error'] == "Review not found"


def test_delete_review(client):
    """Test the /reviews/delete/<int:review_id> DELETE endpoint."""
    
    # Add a sample customer, product, and review to the database
    with app.app_context():
        customer = Customer(
            username="delete_review_user",
            password="test_pass",
            full_name="Delete Review User",
            age=30,
            address="123 Delete St",
            gender="Male",
            marital_status="Single",
            wallet=100.0
        )
        product = Product(
            name="Delete Review Product",
            category="Electronics",
            price=49.99,
            stock=5
        )
        db.session.add(customer)
        db.session.add(product)
        db.session.commit()

        review = Review(
            customer_id=customer.id,
            product_id=product.id,
            rating=4,
            comment="Good product."
        )
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    # Successful review deletion
    response = client.delete(f'/reviews/delete/{review_id}')
    assert response.status_code == 200
    assert response.json['message'] == "Review deleted successfully"

    # Verify the review is deleted from the database
    with app.app_context():
        deleted_review = Review.query.get(review_id)
        assert deleted_review is None

    # Attempt to delete a non-existent review
    response_not_found = client.delete('/reviews/delete/9999')
    assert response_not_found.status_code == 404
    assert response_not_found.json['error'] == "Review not found"


def test_get_product_reviews(client):
    """Test the /reviews/product/<int:product_id> GET endpoint."""

    # Add a sample product and reviews to the database
    with app.app_context():
        product = Product(
            name="Product with Reviews",
            category="Electronics",
            price=99.99,
            stock=10
        )
        customer1 = Customer(
            username="user1",
            password="pass1",
            full_name="User One",
            age=25,
            address="123 Main St",
            gender="Male",
            marital_status="Single",
            wallet=50.0
        )
        customer2 = Customer(
            username="user2",
            password="pass2",
            full_name="User Two",
            age=30,
            address="456 Elm St",
            gender="Female",
            marital_status="Married",
            wallet=100.0
        )
        db.session.add(product)
        db.session.add_all([customer1, customer2])
        db.session.commit()

        # Capture IDs after commit
        product_id = product.id
        customer1_id = customer1.id
        customer2_id = customer2.id

        review1 = Review(
            customer_id=customer1_id,
            product_id=product_id,
            rating=5,
            comment="Amazing product!"
        )
        review2 = Review(
            customer_id=customer2_id,
            product_id=product_id,
            rating=3,
            comment="It's okay."
        )
        db.session.add_all([review1, review2])
        db.session.commit()

    # Successful retrieval of product reviews
    response = client.get(f'/reviews/product/{product_id}')
    assert response.status_code == 200

    data = response.json
    assert len(data) == 2

    # Validate first review
    assert data[0]['rating'] == 5
    assert data[0]['comment'] == "Amazing product!"
    assert data[0]['customer_id'] == customer1_id

    # Validate second review
    assert data[1]['rating'] == 3
    assert data[1]['comment'] == "It's okay."
    assert data[1]['customer_id'] == customer2_id

    # Attempt to retrieve reviews for a non-existent product
    response_not_found = client.get('/reviews/product/9999')
    assert response_not_found.status_code == 404
    assert response_not_found.json['error'] == "Product not found"

def test_get_customer_reviews(client):
    """Test the /reviews/customer/<int:customer_id> GET endpoint."""

    # Add a sample customer, products, and reviews to the database
    with app.app_context():
        customer = Customer(
            username="customer_reviews_user",
            password="test_pass",
            full_name="Customer Reviews User",
            age=30,
            address="123 Reviews St",
            gender="Male",
            marital_status="Single",
            wallet=100.0
        )
        product1 = Product(
            name="Product 1",
            category="Electronics",
            price=50.0,
            stock=10
        )
        product2 = Product(
            name="Product 2",
            category="Books",
            price=20.0,
            stock=5
        )
        db.session.add(customer)
        db.session.add_all([product1, product2])
        db.session.commit()

        # Capture IDs after commit
        customer_id = customer.id
        product1_id = product1.id
        product2_id = product2.id

        review1 = Review(
            customer_id=customer_id,
            product_id=product1_id,
            rating=5,
            comment="Great product!"
        )
        review2 = Review(
            customer_id=customer_id,
            product_id=product2_id,
            rating=3,
            comment="Average product."
        )
        db.session.add_all([review1, review2])
        db.session.commit()

    # Successful retrieval of customer reviews
    response = client.get(f'/reviews/customer/{customer_id}')
    assert response.status_code == 200

    data = response.json
    assert len(data) == 2

    # Validate the first review
    assert data[0]['product_id'] == product1_id
    assert data[0]['rating'] == 5
    assert data[0]['comment'] == "Great product!"

    # Validate the second review
    assert data[1]['product_id'] == product2_id
    assert data[1]['rating'] == 3
    assert data[1]['comment'] == "Average product."

    # Attempt to retrieve reviews for a non-existent customer
    response_not_found = client.get('/reviews/customer/9999')
    assert response_not_found.status_code == 404
    assert response_not_found.json['error'] == "Customer not found"


def test_moderate_review(client):
    """Test the /reviews/moderate/<int:review_id> PUT endpoint."""

    # Use a single app context for consistent session handling
    with app.app_context():
        # Add a sample customer, product, and review to the database
        customer = Customer(
            username="moderate_user",
            password="test_pass",
            full_name="Moderate User",
            age=30,
            address="123 Moderate St",
            gender="Male",
            marital_status="Single",
            wallet=100.0
        )
        product = Product(
            name="Moderate Product",
            category="Electronics",
            price=50.0,
            stock=10
        )
        db.session.add(customer)
        db.session.add(product)
        db.session.commit()

        # Refresh objects from the database to ensure they are attached to the session
        customer = Customer.query.filter_by(username="moderate_user").first()
        product = Product.query.filter_by(name="Moderate Product").first()

        review = Review(
            customer_id=customer.id,
            product_id=product.id,
            rating=4,
            comment="Good product."
        )
        db.session.add(review)
        db.session.commit()
        review_id = review.id

        # Successful review approval
        response_approve = client.put(f'/reviews/moderate/{review_id}', json={"action": "approve"})
        assert response_approve.status_code == 200
        assert response_approve.json['message'] == "Review approved successfully"

        # Recreate the review for flagging test
        review = Review(
            customer_id=customer.id,
            product_id=product.id,
            rating=4,
            comment="Good product."
        )
        db.session.add(review)
        db.session.commit()
        review_id = review.id

        # Successful review flagging (deletes the review)
        response_flag = client.put(f'/reviews/moderate/{review_id}', json={"action": "flag"})
        assert response_flag.status_code == 200
        assert response_flag.json['message'] == "Review flagged and removed successfully"

        # Verify the review is deleted from the database
        flagged_review = Review.query.get(review_id)
        assert flagged_review is None

        # Attempt to moderate a non-existent review
        response_not_found = client.put('/reviews/moderate/9999', json={"action": "approve"})
        assert response_not_found.status_code == 404
        assert response_not_found.json['error'] == "Review not found"

        # Recreate the review for invalid action test
        review = Review(
            customer_id=customer.id,
            product_id=product.id,
            rating=4,
            comment="Good product."
        )
        db.session.add(review)
        db.session.commit()
        review_id = review.id

        # Attempt to moderate with an invalid action
        response_invalid_action = client.put(f'/reviews/moderate/{review_id}', json={"action": "invalid_action"})
        assert response_invalid_action.status_code == 400
        assert response_invalid_action.json['error'] == "Invalid moderation action"



def test_get_review_details(client):
    """Test the /reviews/details/<int:review_id> GET endpoint."""
    
    # Add a sample customer, product, and review to the database
    with app.app_context():
        customer = Customer(
            username="review_details_user",
            password="test_pass",
            full_name="Review Details User",
            age=30,
            address="123 Details St",
            gender="Male",
            marital_status="Single",
            wallet=100.0
        )
        product = Product(
            name="Details Product",
            category="Electronics",
            price=49.99,
            stock=5
        )
        db.session.add(customer)
        db.session.add(product)
        db.session.commit()

        review = Review(
            customer_id=customer.id,
            product_id=product.id,
            rating=5,
            comment="Amazing product!"
        )
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    # Successful retrieval of review details
    response = client.get(f'/reviews/details/{review_id}')
    assert response.status_code == 200

    data = response.json
    assert data['review_id'] == review_id
    assert data['product_name'] == "Details Product"
    assert data['customer_username'] == "review_details_user"
    assert data['rating'] == 5
    assert data['comment'] == "Amazing product!"

    # Attempt to retrieve details for a non-existent review
    response_not_found = client.get('/reviews/details/9999')
    assert response_not_found.status_code == 404
    assert response_not_found.json['error'] == "Review not found"
