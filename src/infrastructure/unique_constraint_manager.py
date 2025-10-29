"""
Unique Constraint Manager
Handles atomic ID generation, collision detection, and constraint validation
Provides thread-safe unique number generation for quotations and other entities
"""

import threading
import time
import random
import string
import hashlib
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass
from contextlib import contextmanager
from abc import ABC, abstractmethod

from .database_abstraction import DatabaseAbstraction, get_database

logger = logging.getLogger(__name__)

@dataclass
class ConstraintConfig:
    """Configuration for unique constraint generation"""
    prefix: str = ""
    suffix: str = ""
    length: int = 8
    use_timestamp: bool = True
    use_random: bool = True
    timestamp_format: str = "%Y%m%d"
    separator: str = "-"
    max_retries: int = 10
    check_unique: bool = True
    collision_backoff: float = 0.01

class UniqueIDGenerator:
    """Thread-safe unique ID generator with collision avoidance"""
    
    def __init__(self, db: DatabaseAbstraction = None):
        self.db = db or get_database()
        self._counters = {}
        self._locks = {}
        self._global_lock = threading.RLock()
        
    def generate_quotation_number(self, customer_id: Optional[str] = None) -> str:
        """Generate unique quotation number with collision detection"""
        config = ConstraintConfig(
            prefix="QT",
            length=6,
            use_timestamp=True,
            timestamp_format="%y%m%d",
            separator="-"
        )
        
        return self._generate_unique_id(
            id_type="quotation",
            table_name="quotations",
            column_name="quotation_number",
            config=config,
            context={"customer_id": customer_id}
        )
        
    def generate_customer_id(self, company_name: Optional[str] = None) -> str:
        """Generate unique customer ID"""
        config = ConstraintConfig(
            prefix="CUST",
            length=4,
            use_timestamp=False,
            use_random=True
        )
        
        # Use company initials if available
        if company_name:
            initials = ''.join([word[0].upper() for word in company_name.split()[:3]])
            config.prefix = f"CUST{initials}"
            
        return self._generate_unique_id(
            id_type="customer",
            table_name="customers",
            column_name="customer_id",
            config=config,
            context={"company_name": company_name}
        )
        
    def generate_document_id(self, document_type: str = "DOC") -> str:
        """Generate unique document ID"""
        config = ConstraintConfig(
            prefix=document_type.upper()[:3],
            length=8,
            use_timestamp=True,
            timestamp_format="%Y%m%d"
        )
        
        return self._generate_unique_id(
            id_type="document",
            table_name="documents",
            column_name="document_id",
            config=config
        )
        
    def _generate_unique_id(self, id_type: str, table_name: str, column_name: str,
                          config: ConstraintConfig, context: Dict = None) -> str:
        """Core unique ID generation with collision detection"""
        context = context or {}
        
        # Get or create lock for this ID type
        with self._global_lock:
            if id_type not in self._locks:
                self._locks[id_type] = threading.RLock()
                self._counters[id_type] = 0
                
        with self._locks[id_type]:
            for attempt in range(config.max_retries):
                try:
                    # Generate candidate ID
                    candidate_id = self._build_id(config, id_type, context)
                    
                    # Check uniqueness if required
                    if config.check_unique:
                        if self._is_unique(table_name, column_name, candidate_id):
                            logger.debug(f"Generated unique {id_type}: {candidate_id}")
                            return candidate_id
                        else:
                            logger.debug(f"Collision detected for {id_type}: {candidate_id}")
                            # Backoff before retry
                            time.sleep(config.collision_backoff * (attempt + 1))
                            continue
                    else:
                        return candidate_id
                        
                except Exception as e:
                    logger.error(f"Error generating {id_type} (attempt {attempt + 1}): {e}")
                    if attempt < config.max_retries - 1:
                        time.sleep(config.collision_backoff * (attempt + 1))
                        continue
                    else:
                        raise
                        
            # All attempts failed
            raise ValueError(f"Failed to generate unique {id_type} after {config.max_retries} attempts")
            
    def _build_id(self, config: ConstraintConfig, id_type: str, context: Dict) -> str:
        """Build ID according to configuration"""
        parts = []
        
        # Add prefix
        if config.prefix:
            parts.append(config.prefix)
            
        # Add timestamp component
        if config.use_timestamp:
            timestamp_str = datetime.now().strftime(config.timestamp_format)
            parts.append(timestamp_str)
            
        # Add sequential/random component
        if config.use_random:
            # Use combination of counter and random for better uniqueness
            with self._global_lock:
                self._counters[id_type] += 1
                counter = self._counters[id_type]
                
            # Combine counter with random for uniqueness
            random_part = random.randint(100, 999)
            sequence_part = f"{counter % 1000:03d}{random_part}"[-config.length:]
            parts.append(sequence_part)
        else:
            # Pure sequential
            with self._global_lock:
                self._counters[id_type] += 1
                counter = self._counters[id_type]
            parts.append(f"{counter:0{config.length}d}")
            
        # Add suffix
        if config.suffix:
            parts.append(config.suffix)
            
        return config.separator.join(parts)
        
    def _is_unique(self, table_name: str, column_name: str, value: str) -> bool:
        """Check if value is unique in the specified table/column"""
        try:
            query = f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} = ?"
            count = self.db.execute_with_retry(query, (value,), fetch_mode='scalar')
            return count == 0
        except Exception as e:
            logger.error(f"Uniqueness check failed: {e}")
            # Assume not unique on error to be safe
            return False

class ConstraintValidator:
    """Validates database constraints and handles violations"""
    
    def __init__(self, db: DatabaseAbstraction = None):
        self.db = db or get_database()
        self.id_generator = UniqueIDGenerator(self.db)
        
    def ensure_unique_quotation_number(self, quotation_data: Dict) -> Dict:
        """Ensure quotation has unique quotation number"""
        if not quotation_data.get('quotation_number'):
            customer_id = quotation_data.get('customer_id')
            quotation_data['quotation_number'] = self.id_generator.generate_quotation_number(customer_id)
            
        return quotation_data
        
    def ensure_unique_customer_id(self, customer_data: Dict) -> Dict:
        """Ensure customer has unique customer ID"""
        if not customer_data.get('customer_id'):
            company_name = customer_data.get('company')
            customer_data['customer_id'] = self.id_generator.generate_customer_id(company_name)
            
        return customer_data
        
    def validate_quotation_constraints(self, quotation_data: Dict) -> Tuple[bool, List[str]]:
        """Validate all quotation constraints"""
        errors = []
        
        # Required fields
        required_fields = ['customer_id', 'total_amount']
        for field in required_fields:
            if not quotation_data.get(field):
                errors.append(f"Required field '{field}' is missing")
                
        # Business logic validations
        if quotation_data.get('total_amount', 0) < 0:
            errors.append("Total amount cannot be negative")
            
        if quotation_data.get('valid_until') and quotation_data.get('quote_date'):
            try:
                quote_date = datetime.strptime(str(quotation_data['quote_date']), '%Y-%m-%d').date()
                valid_until = datetime.strptime(str(quotation_data['valid_until']), '%Y-%m-%d').date()
                
                if valid_until <= quote_date:
                    errors.append("Valid until date must be after quote date")
            except ValueError:
                errors.append("Invalid date format")
                
        # Check customer exists
        if quotation_data.get('customer_id'):
            customer_exists = self._check_foreign_key('customers', 'id', quotation_data['customer_id'])
            if not customer_exists:
                errors.append(f"Customer ID {quotation_data['customer_id']} does not exist")
                
        return len(errors) == 0, errors
        
    def validate_customer_constraints(self, customer_data: Dict) -> Tuple[bool, List[str]]:
        """Validate all customer constraints"""
        errors = []
        
        # Required fields
        required_fields = ['name']
        for field in required_fields:
            if not customer_data.get(field):
                errors.append(f"Required field '{field}' is missing")
                
        # Email validation
        if customer_data.get('email'):
            email = customer_data['email']
            if '@' not in email or '.' not in email.split('@')[-1]:
                errors.append("Invalid email format")
                
        # Credit limit validation
        if customer_data.get('credit_limit', 0) < 0:
            errors.append("Credit limit cannot be negative")
            
        return len(errors) == 0, errors
        
    def _check_foreign_key(self, table: str, column: str, value: Any) -> bool:
        """Check if foreign key reference exists"""
        try:
            query = f"SELECT COUNT(*) FROM {table} WHERE {column} = ?"
            count = self.db.execute_with_retry(query, (value,), fetch_mode='scalar')
            return count > 0
        except Exception as e:
            logger.error(f"Foreign key check failed: {e}")
            return False

class AtomicOperations:
    """Atomic database operations with constraint handling"""
    
    def __init__(self, db: DatabaseAbstraction = None):
        self.db = db or get_database()
        self.validator = ConstraintValidator(self.db)
        
    def create_quotation_atomic(self, quotation_data: Dict, items: List[Dict] = None) -> Tuple[bool, str, Any]:
        """Atomically create quotation with items"""
        try:
            # Validate and ensure constraints
            quotation_data = self.validator.ensure_unique_quotation_number(quotation_data)
            is_valid, errors = self.validator.validate_quotation_constraints(quotation_data)
            
            if not is_valid:
                return False, f"Validation errors: {'; '.join(errors)}", None
                
            # Prepare transaction operations
            operations = []
            
            # Insert quotation
            quotation_fields = [
                'quotation_number', 'customer_id', 'status', 'priority',
                'subtotal', 'tax_amount', 'discount_amount', 'total_amount',
                'currency', 'quote_date', 'valid_until', 'delivery_date',
                'title', 'description', 'notes', 'terms_and_conditions',
                'created_by'
            ]
            
            values = []
            placeholders = []
            for field in quotation_fields:
                if field in quotation_data:
                    values.append(quotation_data[field])
                    placeholders.append('?')
                    
            if not placeholders:
                return False, "No valid quotation fields provided", None
                
            quotation_query = f"""
                INSERT INTO quotations ({', '.join(quotation_fields[:len(values)])})
                VALUES ({', '.join(placeholders)})
            """
            operations.append((quotation_query, tuple(values)))
            
            # Execute transaction
            success = self.db.execute_transaction(operations)
            
            if success:
                # Get the created quotation ID
                quotation_id = self.db.execute_with_retry(
                    "SELECT id FROM quotations WHERE quotation_number = ?",
                    (quotation_data['quotation_number'],),
                    fetch_mode='scalar'
                )
                
                # Add items if provided
                if items and quotation_id:
                    self._add_quotation_items(quotation_id, items)
                    
                return True, "Quotation created successfully", quotation_id
            else:
                return False, "Failed to create quotation", None
                
        except Exception as e:
            logger.error(f"Atomic quotation creation failed: {e}")
            return False, f"Creation failed: {str(e)}", None
            
    def _add_quotation_items(self, quotation_id: int, items: List[Dict]) -> bool:
        """Add items to quotation"""
        try:
            item_operations = []
            
            for item in items:
                # Validate item
                if not item.get('item_name') or not item.get('quantity') or not item.get('unit_price'):
                    continue
                    
                # Calculate line total
                quantity = float(item.get('quantity', 0))
                unit_price = float(item.get('unit_price', 0))
                discount_amount = float(item.get('discount_amount', 0))
                line_total = (quantity * unit_price) - discount_amount
                
                item_query = """
                    INSERT INTO quotation_items (
                        quotation_id, product_id, item_code, item_name, item_description,
                        quantity, unit_of_measure, unit_price, discount_amount, line_total
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                item_values = (
                    quotation_id,
                    item.get('product_id'),
                    item.get('item_code'),
                    item['item_name'],
                    item.get('item_description'),
                    quantity,
                    item.get('unit_of_measure', 'each'),
                    unit_price,
                    discount_amount,
                    line_total
                )
                
                item_operations.append((item_query, item_values))
                
            if item_operations:
                return self.db.execute_transaction(item_operations)
            return True
            
        except Exception as e:
            logger.error(f"Failed to add quotation items: {e}")
            return False
            
    def create_customer_atomic(self, customer_data: Dict) -> Tuple[bool, str, Any]:
        """Atomically create customer with validation"""
        try:
            # Validate and ensure constraints
            customer_data = self.validator.ensure_unique_customer_id(customer_data)
            is_valid, errors = self.validator.validate_customer_constraints(customer_data)
            
            if not is_valid:
                return False, f"Validation errors: {'; '.join(errors)}", None
                
            # Insert customer
            fields = [
                'customer_id', 'name', 'email', 'phone', 'company',
                'tax_number', 'credit_limit', 'payment_terms'
            ]
            
            values = []
            placeholders = []
            for field in fields:
                if field in customer_data:
                    values.append(customer_data[field])
                    placeholders.append('?')
                    
            query = f"""
                INSERT INTO customers ({', '.join(fields[:len(values)])})
                VALUES ({', '.join(placeholders)})
            """
            
            operations = [(query, tuple(values))]
            success = self.db.execute_transaction(operations)
            
            if success:
                customer_id = self.db.execute_with_retry(
                    "SELECT id FROM customers WHERE customer_id = ?",
                    (customer_data['customer_id'],),
                    fetch_mode='scalar'
                )
                return True, "Customer created successfully", customer_id
            else:
                return False, "Failed to create customer", None
                
        except Exception as e:
            logger.error(f"Atomic customer creation failed: {e}")
            return False, f"Creation failed: {str(e)}", None

# Global instances
_id_generator: Optional[UniqueIDGenerator] = None
_constraint_validator: Optional[ConstraintValidator] = None
_atomic_operations: Optional[AtomicOperations] = None

def get_id_generator() -> UniqueIDGenerator:
    """Get global ID generator instance"""
    global _id_generator
    if _id_generator is None:
        _id_generator = UniqueIDGenerator()
    return _id_generator

def get_constraint_validator() -> ConstraintValidator:
    """Get global constraint validator instance"""
    global _constraint_validator
    if _constraint_validator is None:
        _constraint_validator = ConstraintValidator()
    return _constraint_validator

def get_atomic_operations() -> AtomicOperations:
    """Get global atomic operations instance"""
    global _atomic_operations
    if _atomic_operations is None:
        _atomic_operations = AtomicOperations()
    return _atomic_operations