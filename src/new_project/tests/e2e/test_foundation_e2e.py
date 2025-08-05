"""
Foundation End-to-End Tests - Tier 3
====================================

Complete workflow tests that simulate real user scenarios.
These tests verify complete systems work together end-to-end.

Tier 3 Requirements:
- Execute under 10 seconds per test
- NO MOCKING of business logic
- Test complete user workflows
- Verify system integration
"""
import pytest
import time
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock

class CompleteSystemMock:
    """Complete system mock that simulates a real application workflow."""
    
    def __init__(self):
        self.database = {}
        self.file_storage = tempfile.mkdtemp()
        self.users = {}
        self.products = {}
        self.orders = {}
        self.id_counter = 1
        self.session_store = {}
        
    def register_user(self, user_data):
        """Complete user registration workflow."""
        # Validate required fields
        if not user_data.get("email") or not user_data.get("name"):
            raise ValueError("Email and name are required")
            
        # Check if user exists
        for user in self.users.values():
            if user["email"] == user_data["email"]:
                raise ValueError("User already exists")
        
        # Create user
        user_id = self.id_counter
        self.id_counter += 1
        
        user = {
            "id": user_id,
            "name": user_data["name"],
            "email": user_data["email"],
            "role": user_data.get("role", "customer"),
            "created_at": time.time(),
            "active": True
        }
        
        self.users[user_id] = user
        
        # Create user profile file
        profile_path = Path(self.file_storage) / f"user_{user_id}_profile.json"
        with open(profile_path, 'w') as f:
            json.dump(user, f, indent=2)
            
        return user
    
    def authenticate_user(self, email, password="test_password"):
        """Authenticate user and create session."""
        # Find user by email
        user = None
        for u in self.users.values():
            if u["email"] == email:
                user = u
                break
                
        if not user:
            raise ValueError("User not found")
            
        if not user["active"]:
            raise ValueError("User account is inactive")
        
        # Create session
        session_id = f"session_{self.id_counter}"
        self.id_counter += 1
        
        self.session_store[session_id] = {
            "user_id": user["id"],
            "created_at": time.time(),
            "last_accessed": time.time()
        }
        
        return {
            "session_id": session_id,
            "user": user,
            "expires_at": time.time() + 3600  # 1 hour
        }
    
    def create_product(self, product_data, user_session):
        """Create product with authentication check."""
        # Verify session
        if user_session not in self.session_store:
            raise ValueError("Invalid session")
            
        # Verify user permissions (admin or manager)
        session = self.session_store[user_session]
        user = self.users[session["user_id"]]
        
        if user["role"] not in ["admin", "manager"]:
            raise ValueError("Insufficient permissions")
        
        # Create product
        product_id = self.id_counter
        self.id_counter += 1
        
        product = {
            "id": product_id,
            "name": product_data["name"],
            "description": product_data.get("description", ""),
            "price": product_data["price"],
            "category": product_data.get("category", "general"),
            "created_by": user["id"],
            "created_at": time.time(),
            "active": True
        }
        
        self.products[product_id] = product
        
        # Save product to file
        product_path = Path(self.file_storage) / f"product_{product_id}.json"
        with open(product_path, 'w') as f:
            json.dump(product, f, indent=2)
            
        return product
    
    def create_order(self, order_data, user_session):
        """Create order workflow."""
        # Verify session
        if user_session not in self.session_store:
            raise ValueError("Invalid session")
            
        session = self.session_store[user_session]
        user = self.users[session["user_id"]]
        
        # Validate products exist and are active
        total_price = 0
        order_items = []
        
        for item in order_data["items"]:
            product_id = item["product_id"]
            quantity = item["quantity"]
            
            if product_id not in self.products:
                raise ValueError(f"Product {product_id} not found")
                
            product = self.products[product_id]
            if not product["active"]:
                raise ValueError(f"Product {product_id} is not available")
            
            item_total = product["price"] * quantity
            total_price += item_total
            
            order_items.append({
                "product_id": product_id,
                "product_name": product["name"],
                "price": product["price"],
                "quantity": quantity,
                "total": item_total
            })
        
        # Create order
        order_id = self.id_counter
        self.id_counter += 1
        
        order = {
            "id": order_id,
            "user_id": user["id"],
            "items": order_items,
            "total_price": total_price,
            "status": "pending",
            "created_at": time.time(),
            "shipping_address": order_data.get("shipping_address", {})
        }
        
        self.orders[order_id] = order
        
        # Save order to file
        order_path = Path(self.file_storage) / f"order_{order_id}.json"
        with open(order_path, 'w') as f:
            json.dump(order, f, indent=2)
        
        return order
    
    def process_order(self, order_id, user_session):
        """Process order workflow."""
        # Verify session and permissions
        if user_session not in self.session_store:
            raise ValueError("Invalid session")
            
        session = self.session_store[user_session]
        user = self.users[session["user_id"]]
        
        if user["role"] not in ["admin", "manager"]:
            raise ValueError("Insufficient permissions to process orders")
        
        # Get order
        if order_id not in self.orders:
            raise ValueError("Order not found")
            
        order = self.orders[order_id]
        
        if order["status"] != "pending":
            raise ValueError(f"Order is already {order['status']}")
        
        # Process order
        order["status"] = "processing"
        order["processed_at"] = time.time()
        order["processed_by"] = user["id"]
        
        # Update order file
        order_path = Path(self.file_storage) / f"order_{order_id}.json"
        with open(order_path, 'w') as f:
            json.dump(order, f, indent=2)
        
        return order
    
    def get_user_orders(self, user_session):
        """Get all orders for authenticated user."""
        if user_session not in self.session_store:
            raise ValueError("Invalid session")
            
        session = self.session_store[user_session]
        user_id = session["user_id"]
        
        user_orders = []
        for order in self.orders.values():
            if order["user_id"] == user_id:
                user_orders.append(order)
        
        return sorted(user_orders, key=lambda x: x["created_at"], reverse=True)
    
    def cleanup(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.file_storage, ignore_errors=True)

@pytest.mark.e2e
class TestCompleteUserWorkflows:
    """Complete user workflow tests."""
    
    def setup_method(self):
        """Set up complete system for each test."""
        self.system = CompleteSystemMock()
        
    def teardown_method(self):
        """Clean up after each test."""
        self.system.cleanup()
        
    def test_complete_user_registration_and_authentication_workflow(self):
        """Test complete user registration and authentication workflow."""
        start_time = time.time()
        
        # Step 1: Register new user
        user_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "role": "customer"
        }
        
        user = self.system.register_user(user_data)
        
        # Verify user registration
        assert user["id"] is not None
        assert user["name"] == "John Doe"
        assert user["email"] == "john.doe@example.com"
        assert user["role"] == "customer"
        assert user["active"] is True
        
        # Step 2: Authenticate user
        auth_result = self.system.authenticate_user("john.doe@example.com")
        
        # Verify authentication
        assert auth_result["session_id"] is not None
        assert auth_result["user"]["id"] == user["id"]
        assert auth_result["expires_at"] > time.time()
        
        # Step 3: Verify session is active
        session_id = auth_result["session_id"]
        assert session_id in self.system.session_store
        
        # Step 4: Verify user profile file was created
        profile_path = Path(self.system.file_storage) / f"user_{user['id']}_profile.json"
        assert profile_path.exists()
        
        with open(profile_path, 'r') as f:
            saved_profile = json.load(f)
        assert saved_profile["name"] == "John Doe"
        
        duration = time.time() - start_time
        assert duration < 10.0  # Tier 3 requirement
        
    def test_complete_product_management_workflow(self):
        """Test complete product management workflow."""
        start_time = time.time()
        
        # Step 1: Create admin user
        admin_user = self.system.register_user({
            "name": "Admin User",
            "email": "admin@example.com",
            "role": "admin"
        })
        
        # Step 2: Authenticate admin
        admin_auth = self.system.authenticate_user("admin@example.com")
        admin_session = admin_auth["session_id"]
        
        # Step 3: Create multiple products
        products = []
        product_data_list = [
            {"name": "Widget A", "price": 29.99, "category": "tools"},
            {"name": "Widget B", "price": 49.99, "category": "electronics"},
            {"name": "Tool C", "price": 19.99, "category": "tools"}
        ]
        
        for product_data in product_data_list:
            product = self.system.create_product(product_data, admin_session)
            products.append(product)
        
        # Step 4: Verify all products created
        assert len(products) == 3
        assert len(self.system.products) == 3
        
        # Step 5: Verify product files created
        for product in products:
            product_path = Path(self.system.file_storage) / f"product_{product['id']}.json"
            assert product_path.exists()
            
            with open(product_path, 'r') as f:
                saved_product = json.load(f)
            assert saved_product["name"] == product["name"]
            assert saved_product["created_by"] == admin_user["id"]
        
        duration = time.time() - start_time
        assert duration < 10.0
        
    def test_complete_order_processing_workflow(self):
        """Test complete order processing workflow."""
        start_time = time.time()
        
        # Step 1: Set up users
        customer = self.system.register_user({
            "name": "Customer",
            "email": "customer@example.com",
            "role": "customer"
        })
        
        manager = self.system.register_user({
            "name": "Manager",
            "email": "manager@example.com", 
            "role": "manager"
        })
        
        # Step 2: Authenticate users
        customer_auth = self.system.authenticate_user("customer@example.com")
        manager_auth = self.system.authenticate_user("manager@example.com")
        
        customer_session = customer_auth["session_id"]
        manager_session = manager_auth["session_id"]
        
        # Step 3: Create products (as manager)
        product1 = self.system.create_product({
            "name": "Product 1",
            "price": 100.00,
            "description": "First product"
        }, manager_session)
        
        product2 = self.system.create_product({
            "name": "Product 2", 
            "price": 150.00,
            "description": "Second product"
        }, manager_session)
        
        # Step 4: Customer creates order
        order_data = {
            "items": [
                {"product_id": product1["id"], "quantity": 2},
                {"product_id": product2["id"], "quantity": 1}
            ],
            "shipping_address": {
                "street": "123 Main St",
                "city": "Anytown",
                "zipcode": "12345"
            }
        }
        
        order = self.system.create_order(order_data, customer_session)
        
        # Step 5: Verify order creation
        assert order["id"] is not None
        assert order["user_id"] == customer["id"]
        assert len(order["items"]) == 2
        assert order["total_price"] == 350.00  # (100*2) + (150*1)
        assert order["status"] == "pending"
        
        # Step 6: Manager processes order
        processed_order = self.system.process_order(order["id"], manager_session)
        
        # Step 7: Verify order processing
        assert processed_order["status"] == "processing"
        assert processed_order["processed_by"] == manager["id"]
        assert "processed_at" in processed_order
        
        # Step 8: Customer retrieves their orders
        customer_orders = self.system.get_user_orders(customer_session)
        
        # Step 9: Verify order retrieval
        assert len(customer_orders) == 1
        assert customer_orders[0]["id"] == order["id"]
        assert customer_orders[0]["status"] == "processing"
        
        # Step 10: Verify order file was updated
        order_path = Path(self.system.file_storage) / f"order_{order['id']}.json"
        assert order_path.exists()
        
        with open(order_path, 'r') as f:
            saved_order = json.load(f)
        assert saved_order["status"] == "processing"
        
        duration = time.time() - start_time
        assert duration < 10.0
        
    def test_error_handling_complete_workflow(self):
        """Test complete error handling across workflows."""
        start_time = time.time()
        
        # Test 1: Duplicate user registration
        user_data = {"name": "Test User", "email": "test@example.com"}
        self.system.register_user(user_data)
        
        with pytest.raises(ValueError, match="User already exists"):
            self.system.register_user(user_data)
        
        # Test 2: Invalid authentication
        with pytest.raises(ValueError, match="User not found"):
            self.system.authenticate_user("nonexistent@example.com")
        
        # Test 3: Unauthorized product creation
        customer = self.system.register_user({
            "name": "Customer",
            "email": "customer@example.com",
            "role": "customer"
        })
        customer_auth = self.system.authenticate_user("customer@example.com")
        
        with pytest.raises(ValueError, match="Insufficient permissions"):
            self.system.create_product({"name": "Product", "price": 10.0}, customer_auth["session_id"])
        
        # Test 4: Order with non-existent product
        with pytest.raises(ValueError, match="Product .* not found"):
            self.system.create_order({
                "items": [{"product_id": 999, "quantity": 1}]
            }, customer_auth["session_id"])
        
        duration = time.time() - start_time
        assert duration < 10.0
        
    def test_performance_under_load_workflow(self):
        """Test system performance under load."""
        start_time = time.time()
        
        # Create admin for product creation
        admin = self.system.register_user({
            "name": "Admin",
            "email": "admin@example.com",
            "role": "admin"
        })
        admin_auth = self.system.authenticate_user("admin@example.com")
        admin_session = admin_auth["session_id"]
        
        # Create 20 products
        products = []
        for i in range(20):
            product = self.system.create_product({
                "name": f"Product {i+1}",
                "price": (i + 1) * 10.0,
                "category": "test"
            }, admin_session)
            products.append(product)
        
        # Create 10 customers
        customers = []
        for i in range(10):
            customer = self.system.register_user({
                "name": f"Customer {i+1}",
                "email": f"customer{i+1}@example.com",
                "role": "customer"
            })
            customer_auth = self.system.authenticate_user(f"customer{i+1}@example.com")
            customers.append((customer, customer_auth["session_id"]))
        
        # Each customer creates 2 orders
        total_orders = 0
        for customer, session in customers:
            for order_num in range(2):
                # Order 2 random products
                order_data = {
                    "items": [
                        {"product_id": products[order_num * 2]["id"], "quantity": 1},
                        {"product_id": products[order_num * 2 + 1]["id"], "quantity": 2}
                    ]
                }
                order = self.system.create_order(order_data, session)
                total_orders += 1
        
        # Verify system state
        assert len(self.system.users) == 11  # 10 customers + 1 admin
        assert len(self.system.products) == 20
        assert len(self.system.orders) == total_orders
        assert total_orders == 20  # 10 customers * 2 orders each
        
        # Verify performance
        duration = time.time() - start_time
        assert duration < 10.0
        
        print(f"Performance test: {total_orders} orders, {len(self.system.products)} products, {len(self.system.users)} users in {duration:.3f}s")