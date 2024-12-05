# Ecommerce_Yassine_Nassereddine

### Overview
This project is a backend implementation for an e-commerce platform using **Flask** and **SQLAlchemy**. The application provides user authentication, role-based access control (RBAC), and several APIs for managing users, products, reviews, and purchases.

---

### Features
- **User Authentication**:
  - Users can log in and log out.
  - Secure sessions are used to maintain user authentication.

- **Role-Based Access Control (RBAC)**:
  - **Admins** can manage customers, products, and flagged reviews.
  - **Customers** can manage their profiles, wallets, and reviews.

- **Customer Management**:
  - Admins can create, update, delete, and list customers.
  - Customers can update their profiles and manage their wallets.

- **Product Management**:
  - Admins can add, update, and deduct stock for products.
  - Customers can view available products and purchase items.

- **Review System**:
  - Customers can submit, update, and delete reviews for purchased products.
  - Reviews can be flagged for moderation by admins.

- **Purchase History**:
  - Customers can view their purchase history.
  - Admins can view purchase history for all customers.

---

### API Endpoints
1. **Authentication**:
   - `/login` - Log in a user.
   - `/logout` - Log out a user.

2. **Customer Management**:
   - `/customers/register` - Register a new customer.
   - `/customers/<int:id>` - Update or delete a customer (Admins only).
   - `/customers` - List all customers (Admins only).
   - `/customers/<username>` - View a customer's details.

3. **Product Management**:
   - `/inventory/add` - Add a new product (Admins only).
   - `/inventory/deduct/<int:product_id>` - Deduct stock (Admins only).
   - `/inventory/update/<int:product_id>` - Update product details (Admins only).
   - `/sales/available-goods` - List available goods.

4. **Purchases**:
   - `/sales/purchase` - Process a product purchase (Customers only).
   - `/sales/purchase-history/<int:customer_id>` - View purchase history.

5. **Reviews**:
   - `/reviews/submit` - Submit a new review (Customers only).
   - `/reviews/update/<int:review_id>` - Update an existing review (Customers only).
   - `/reviews/delete/<int:review_id>` - Delete a review (Customers only).
   - `/reviews/product/<int:product_id>` - Get all reviews for a product.
   - `/reviews/customer/<int:customer_id>` - Get all reviews by a customer.
   - `/reviews/flag/<int:review_id>` - Flag a review (Customers only).
   - `/reviews/flagged` - Get flagged reviews (Admins only).
   - `/reviews/moderate/<int:review_id>` - Approve or delete flagged reviews (Admins only).

---

### Technologies Used
- **Backend Framework**: Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask Sessions
- **Input Validation**: Custom validation and sanitization functions.

---

### Setup Instructions
1. **Clone the Repository**:
   ```
   git clone https://github.com/KassemYassine/Ecommerce_Yassine_Nassereddine.git
   cd <repository-directory>
   ```

2. **Install Dependencies**:
   ```
   pip install -r requirements.txt
   ```

3. **Initialize the Database**:
   ```
   python app.py
   ```
   - This will create the database and add a default admin user.

4. **Run the Application**:
   ```
   flask run
   ```

5. **Access the API**:
   - Default URL: `http://127.0.0.1:5000`

---

### Database Models
1. **User**:
   - Stores user details, roles (Admin or Customer), and wallet balances.

2. **Product**:
   - Represents the products available in the inventory.

3. **Review**:
   - Manages customer reviews for products with a flagging system for moderation.

4. **PurchaseHistory**:
   - Tracks all customer purchases.

---

### Security Measures
- **Authentication**: Session-based login ensures secure user access.
- **RBAC**: Role-based access ensures admins and customers have appropriate permissions.
- **Input Sanitization**: User inputs are sanitized to prevent XSS attacks.
- **Error Handling**: Generic error messages prevent information leakage.

---

### Contribution
Feel free to fork this repository and submit pull requests. Contributions are always welcome!
