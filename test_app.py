import unittest
from app import app, db  # Import your Flask app and db from your application
from models import Customer, Product, PurchaseHistory, Review  # Import the necessary models

class TestFlaskApp(unittest.TestCase):

    # Set up a test client and initialize the database
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_ecommerce.db'  # Use a test database
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Ensure the application context is pushed
        with app.app_context():
            db.create_all()  # Create all tables for testing

    # Clean up the database after each test
    def tearDown(self):
        # Ensure the application context is pushed when cleaning up
        with app.app_context():
            db.session.remove()
            db.drop_all()

    # Test customer registration
    def test_register_customer(self):
        response = self.client.post('/customers/register', json={
            "username": "testuser",
            "password": "password123",
            "full_name": "Test User",
            "age": 25,
            "address": "Test Address",
            "gender": "M",
            "marital_status": "Single"
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn('Customer registered successfully', str(response.data))

    # Test fetching available goods
    def test_get_available_goods(self):
        response = self.client.get('/sales/available-goods')
        self.assertEqual(response.status_code, 200)

    def test_process_sale(self):
    # First, create a customer and product to test the sale
        with app.app_context():
            customer = Customer(
                username="testuser",
                password="password123",  # Add a valid password
                full_name="Test User",    # Add a valid full name
                wallet=100
            )
            product = Product(name="Test Product", price=50, stock=10)
            db.session.add(customer)
            db.session.add(product)
            db.session.commit()

    def test_delete_customer(self):
        # First, create a customer to delete
        with app.app_context():
            customer = Customer(
                username="deleteuser",
                password="password123",
                full_name="Delete User",
                age=30,
                address="Delete Address",
                gender="M",
                marital_status="Single",
                wallet=50
            )
        db.session.add(customer)
        db.session.commit()

        # Test deleting the customer
        response = self.client.delete(f'/customers/{customer.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Customer deleted successfully', str(response.data))

        # Check if the customer is deleted
        deleted_customer = Customer.query.get(customer.id)
        self.assertIsNone(deleted_customer)
    
    def test_update_customer(self):
        # First, create a customer to update
        with app.app_context():
            customer = Customer(
                username="updateuser",
                password="password123",
                full_name="Update User",
                age=30,
                address="Update Address",
                gender="M",
                marital_status="Single",
                wallet=50
            )
            db.session.add(customer)
            db.session.commit()

        # Update customer information
        response = self.client.put(f'/customers/{customer.id}', json={
            "full_name": "Updated User",  # Update full_name
            "address": "Updated Address"  # Update address
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('Customer updated successfully', str(response.data))

        # Verify the update
        updated_customer = Customer.query.get(customer.id)
        self.assertEqual(updated_customer.full_name, "Updated User")
        self.assertEqual(updated_customer.address, "Updated Address")

    def test_get_all_customers(self):
        # First, create some customers
        with app.app_context():
            customer1 = Customer(
                username="user1",
                password="password123",
                full_name="User One",
                age=25,
                address="Address One",
                gender="M",
                marital_status="Single",
                wallet=50
            )
            customer2 = Customer(
                username="user2",
                password="password123",
                full_name="User Two",
                age=28,
                address="Address Two",
                gender="F",
                marital_status="Married",
                wallet=100
            )
            db.session.add(customer1)
            db.session.add(customer2)
            db.session.commit()

        # Get all customers
        response = self.client.get('/customers')
        self.assertEqual(response.status_code, 200)
        self.assertIn("User One", str(response.data))
        self.assertIn("User Two", str(response.data))

    def test_get_customer_by_username(self):
        # First, create a customer
        with app.app_context():
            customer = Customer(
                username="testuser",
                password="password123",
                full_name="Test User",
                age=30,
                address="Test Address",
                gender="M",
                marital_status="Single",
                wallet=50
            )
            db.session.add(customer)
            db.session.commit()

        # Get customer by username
        response = self.client.get(f'/customers/{customer.username}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test User', str(response.data))
        self.assertIn('Test Address', str(response.data))

    def test_charge_wallet(self):
        # First, create a customer
        with app.app_context():
            customer = Customer(
                username="chargeuser",
                password="password123",
                full_name="Charge User",
                age=30,
                address="Charge Address",
                gender="M",
                marital_status="Single",
                wallet=50
            )
            db.session.add(customer)
            db.session.commit()

        # Charge the customer's wallet
        response = self.client.post(f'/customers/{customer.id}/charge', json={"amount": 20})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Wallet charged by 20', str(response.data))

        # Verify the wallet balance is updated
        updated_customer = Customer.query.get(customer.id)
        self.assertEqual(updated_customer.wallet, 70)

    def test_deduct_wallet(self):
    # First, create a customer to deduct money from
        with app.app_context():
            customer = Customer(
                username="deductuser",
                password="password123",
                full_name="Deduct User",
                age=30,
                address="Deduct Address",
                gender="M",
                marital_status="Single",
                wallet=100
            )
            db.session.add(customer)
            db.session.commit()

        # Deduct money from wallet
        response = self.client.post(f'/customers/{customer.id}/deduct', json={"amount": 50})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Wallet deducted by 50', str(response.data))

        # Verify the wallet balance is updated
        updated_customer = Customer.query.get(customer.id)
        self.assertEqual(updated_customer.wallet, 50)

        # Test insufficient funds
        response = self.client.post(f'/customers/{customer.id}/deduct', json={"amount": 100})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Insufficient funds', str(response.data))

        # Test invalid amount
        response = self.client.post(f'/customers/{customer.id}/deduct', json={"amount": -10})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid amount', str(response.data))

    def test_add_product(self):
        # Test with valid data
        response = self.client.post('/inventory/add', json={
            "name": "New Product",
            "category": "Electronics",
            "price": 100,
            "stock": 10
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn('Product added successfully', str(response.data))

        # Test with missing required fields
        response = self.client.post('/inventory/add', json={
            "name": "Product Without Category",
            "price": 50,
            "stock": 5
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("category is required", str(response.data))
    
    def test_deduct_product_stock(self):
        # First, create a product to deduct stock from
        with app.app_context():
            product = Product(
                name="Test Product",
                category="Electronics",
                price=100,
                stock=10
            )
            db.session.add(product)
            db.session.commit()

        # Deduct stock from product
        response = self.client.post(f'/inventory/deduct/{product.id}', json={"quantity": 5})
        self.assertEqual(response.status_code, 200)
        self.assertIn(f"Deducted 5 items from stock. Remaining stock: {product.stock - 5}", str(response.data))

        # Verify the stock is updated
        updated_product = Product.query.get(product.id)
        self.assertEqual(updated_product.stock, 5)

        # Test insufficient stock
        response = self.client.post(f'/inventory/deduct/{product.id}', json={"quantity": 10})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Not enough stock available', str(response.data))

        # Test invalid quantity
        response = self.client.post(f'/inventory/deduct/{product.id}', json={"quantity": -1})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid quantity', str(response.data))

    def test_update_product(self):
        # First, create a product to update
        with app.app_context():
            product = Product(
                name="Old Product",
                category="Electronics",
                price=100,
                stock=10
            )
            db.session.add(product)
            db.session.commit()

        # Update product information
        response = self.client.put(f'/inventory/update/{product.id}', json={
            "name": "Updated Product",  # Update name
            "price": 120                # Update price
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('Product updated successfully', str(response.data))

        # Verify the update
        updated_product = Product.query.get(product.id)
        self.assertEqual(updated_product.name, "Updated Product")
        self.assertEqual(updated_product.price, 120)

        # Test invalid product ID
        response = self.client.put('/inventory/update/9999', json={
            "name": "Nonexistent Product"
        })
        self.assertEqual(response.status_code, 404)
        self.assertIn('Product not found', str(response.data))
    
    def test_display_available_goods(self):
        # Create some products
        with app.app_context():
            product1 = Product(
                name="Available Product",
                category="Electronics",
                price=100,
                stock=5
            )
            product2 = Product(
                name="Out of Stock Product",
                category="Electronics",
                price=50,
                stock=0
            )
            db.session.add(product1)
            db.session.add(product2)
            db.session.commit()

        # Fetch available goods
        response = self.client.get('/sales/available-goods')
        self.assertEqual(response.status_code, 200)

        # Check that only available products are listed
        self.assertIn('Available Product', str(response.data))
        self.assertNotIn('Out of Stock Product', str(response.data))
    
    def test_get_good_details(self):
        # Create a product
        with app.app_context():
            product = Product(
                name="Test Product",
                category="Electronics",
                price=100,
                stock=5,
                description="A product for testing."
            )
            db.session.add(product)
            db.session.commit()

        # Fetch product details
        response = self.client.get(f'/sales/good-details/{product.id}')
        self.assertEqual(response.status_code, 200)

        # Check if the product details are returned correctly
        self.assertIn('Test Product', str(response.data))
        self.assertIn('Electronics', str(response.data))
        self.assertIn('100', str(response.data))  # Price should be in the response
        self.assertIn('5', str(response.data))  # Stock should be in the response

        # Test invalid product ID
        response = self.client.get('/sales/good-details/9999')
        self.assertEqual(response.status_code, 404)
        self.assertIn('Product not found', str(response.data))
    
    def test_get_purchase_history(self):
        # First, create a customer and a product
        with app.app_context():
            customer = Customer(
                username="customer1",
                password="password123",
                full_name="Customer One",
                age=25,
                address="Customer Address",
                gender="M",
                marital_status="Single",
                wallet=100
            )
            product = Product(
                name="Test Product",
                category="Electronics",
                price=100,
                stock=10
            )
            db.session.add(customer)
            db.session.add(product)
            db.session.commit()

            # Create a purchase record
            purchase = PurchaseHistory(customer_id=customer.id, product_id=product.id)
            db.session.add(purchase)
            db.session.commit()

        # Fetch purchase history for the customer
        response = self.client.get(f'/sales/purchase-history/{customer.id}')
        self.assertEqual(response.status_code, 200)

        # Check if the purchase history is returned correctly
        self.assertIn("Test Product", str(response.data))
        self.assertIn("purchase_time", str(response.data))

        # Test invalid customer ID
        response = self.client.get('/sales/purchase-history/9999')
        self.assertEqual(response.status_code, 404)
        self.assertIn("Customer not found", str(response.data))
    def test_submit_review(self):
        # First, create a customer and a product
        with app.app_context():
            customer = Customer(
                username="customer1",
                password="password123",
                full_name="Customer One",
                age=25,
                address="Customer Address",
                gender="M",
                marital_status="Single",
                wallet=100
            )
            product = Product(
                name="Test Product",
                category="Electronics",
                price=100,
                stock=10
            )
            db.session.add(customer)
            db.session.add(product)
            db.session.commit()

        # Submit a review
        response = self.client.post('/reviews/submit', json={
            "customer_id": customer.id,
            "product_id": product.id,
            "rating": 5,
            "comment": "Great product!"
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn('Review submitted successfully', str(response.data))

        # Test invalid customer or product
        response = self.client.post('/reviews/submit', json={
            "customer_id": 9999,  # Invalid customer ID
            "product_id": product.id,
            "rating": 5,
            "comment": "Great product!"
        })
        self.assertEqual(response.status_code, 404)
        self.assertIn("Invalid customer or product ID", str(response.data))

    def test_update_review(self):
        # First, create a customer, a product, and a review
        with app.app_context():
            customer = Customer(
                username="customer1",
                password="password123",
                full_name="Customer One",
                age=25,
                address="Customer Address",
                gender="M",
                marital_status="Single",
                wallet=100
            )
            product = Product(
                name="Test Product",
                category="Electronics",
                price=100,
                stock=10
            )
            db.session.add(customer)
            db.session.add(product)
            db.session.commit()

            review = Review(
                customer_id=customer.id,
                product_id=product.id,
                rating=4,
                comment="Good product"
            )
            db.session.add(review)
            db.session.commit()

        # Update review
        response = self.client.put(f'/reviews/update/{review.id}', json={
            "rating": 5,
            "comment": "Excellent product!"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('Review updated successfully', str(response.data))

        # Verify the update
        updated_review = Review.query.get(review.id)
        self.assertEqual(updated_review.rating, 5)
        self.assertEqual(updated_review.comment, "Excellent product!")

        # Test invalid review ID
        response = self.client.put('/reviews/update/9999', json={
            "rating": 5,
            "comment": "Excellent product!"
        })
        self.assertEqual(response.status_code, 404)
        self.assertIn("Review not found", str(response.data))

    def test_delete_review(self):
        # First, create a customer, a product, and a review
        with app.app_context():
            customer = Customer(
                username="customer1",
                password="password123",
                full_name="Customer One",
                age=25,
                address="Customer Address",
                gender="M",
                marital_status="Single",
                wallet=100
            )
            product = Product(
                name="Test Product",
                category="Electronics",
                price=100,
                stock=10
            )
            db.session.add(customer)
            db.session.add(product)
            db.session.commit()

            review = Review(
                customer_id=customer.id,
                product_id=product.id,
                rating=4,
                comment="Good product"
            )
            db.session.add(review)
            db.session.commit()

        # Delete review
        response = self.client.delete(f'/reviews/delete/{review.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Review deleted successfully', str(response.data))

        # Check if the review is deleted
        deleted_review = Review.query.get(review.id)
        self.assertIsNone(deleted_review)

        # Test invalid review ID
        response = self.client.delete('/reviews/delete/9999')
        self.assertEqual(response.status_code, 404)
        self.assertIn("Review not found", str(response.data))

    def test_get_product_reviews(self):
        # First, create a customer, a product, and a review
        with app.app_context():
            customer = Customer(
                username="customer1",
                password="password123",
                full_name="Customer One",
                age=25,
                address="Customer Address",
                gender="M",
                marital_status="Single",
                wallet=100
            )
            product = Product(
                name="Test Product",
                category="Electronics",
                price=100,
                stock=10
            )
            db.session.add(customer)
            db.session.add(product)
            db.session.commit()

            review = Review(
                customer_id=customer.id,
                product_id=product.id,
                rating=4,
                comment="Good product"
            )
            db.session.add(review)
            db.session.commit()

        # Fetch product reviews
        response = self.client.get(f'/reviews/product/{product.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Good product", str(response.data))

        # Test invalid product ID
        response = self.client.get('/reviews/product/9999')
        self.assertEqual(response.status_code, 404)
        self.assertIn("Product not found", str(response.data))


    def test_get_customer_reviews(self):
        # First, create a customer, a product, and a review
        with app.app_context():
            customer = Customer(
                username="customer1",
                password="password123",
                full_name="Customer One",
                age=25,
                address="Customer Address",
                gender="M",
                marital_status="Single",
                wallet=100
            )
            product = Product(
                name="Test Product",
                category="Electronics",
                price=100,
                stock=10
            )
            db.session.add(customer)
            db.session.add(product)
            db.session.commit()

            review = Review(
                customer_id=customer.id,
                product_id=product.id,
                rating=4,
                comment="Good product"
            )
            db.session.add(review)
            db.session.commit()
        
        # Test invalid customer ID
        response = self.client.get('/reviews/customer/9999')
        self.assertEqual(response.status_code, 404)
        self.assertIn("Customer not found", str(response.data))

    def test_moderate_review(self):
        # First, create a customer, a product, and a review
        with app.app_context():
            customer = Customer(
                username="customer1",
                password="password123",
                full_name="Customer One",
                age=25,
                address="Customer Address",
                gender="M",
                marital_status="Single",
                wallet=100
            )
            product = Product(
                name="Test Product",
                category="Electronics",
                price=100,
                stock=10
            )
            db.session.add(customer)
            db.session.add(product)
            db.session.commit()

            review = Review(
                customer_id=customer.id,
                product_id=product.id,
                rating=4,
                comment="Good product"
            )
            db.session.add(review)
            db.session.commit()

        # Approve the review
        response = self.client.put(f'/reviews/moderate/{review.id}', json={
            "action": "approve"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('Review approved successfully', str(response.data))

        # Flag the review (which will delete it)
        response = self.client.put(f'/reviews/moderate/{review.id}', json={
            "action": "flag"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('Review flagged and removed successfully', str(response.data))

        # Test invalid action
        response = self.client.put(f'/reviews/moderate/{review.id}', json={
            "action": "invalid_action"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid moderation action', str(response.data))

        # Test invalid review ID
        response = self.client.put('/reviews/moderate/9999', json={
            "action": "approve"
        })
        self.assertEqual(response.status_code, 404)
        self.assertIn('Review not found', str(response.data))
    
    def test_get_review_details(self):
        # First, create a customer, a product, and a review
        with app.app_context():
            customer = Customer(
                username="customer1",
                password="password123",
                full_name="Customer One",
                age=25,
                address="Customer Address",
                gender="M",
                marital_status="Single",
                wallet=100
            )
            product = Product(
                name="Test Product",
                category="Electronics",
                price=100,
                stock=10
            )
            db.session.add(customer)
            db.session.add(product)
            db.session.commit()

            review = Review(
                customer_id=customer.id,
                product_id=product.id,
                rating=5,
                comment="Excellent product!"
            )
            db.session.add(review)
            db.session.commit()

        # Fetch review details
        response = self.client.get(f'/reviews/details/{review.id}')
        self.assertEqual(response.status_code, 200)

        # Check if the review details are returned correctly
        self.assertIn("Excellent product!", str(response.data))
        self.assertIn("Test Product", str(response.data))
        self.assertIn("customer1", str(response.data))  # Customer username

        # Test invalid review ID
        response = self.client.get('/reviews/details/9999')
        self.assertEqual(response.status_code, 404)
        self.assertIn('Review not found', str(response.data))




    

    








    





            


