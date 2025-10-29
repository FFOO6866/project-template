#!/usr/bin/env python3
"""
Password Utilities
Secure password hashing, validation, and policy enforcement
"""

import re
import secrets
import string
from typing import List, Dict
import bcrypt

class PasswordPolicy:
    """
    Password policy enforcement
    """
    
    def __init__(
        self,
        min_length: int = 8,
        max_length: int = 128,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digits: bool = True,
        require_special_chars: bool = True,
        min_special_chars: int = 1,
        forbidden_patterns: List[str] = None
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special_chars = require_special_chars
        self.min_special_chars = min_special_chars
        self.forbidden_patterns = forbidden_patterns or [
            r'(.)\1{2,}',  # No character repeated more than 2 times
            r'^(password|admin|user|test|123456)',  # Common weak passwords
        ]
    
    def validate_password(self, password: str) -> Dict[str, any]:
        """
        Validate password against policy
        
        Returns:
            dict: {"valid": bool, "errors": List[str], "strength": str}
        """
        errors = []
        
        # Length checks
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        
        if len(password) > self.max_length:
            errors.append(f"Password must be no more than {self.max_length} characters long")
        
        # Character type requirements
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.require_digits and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if self.require_special_chars:
            special_chars = re.findall(r'[!@#$%^&*(),.?":{}|<>]', password)
            if len(special_chars) < self.min_special_chars:
                errors.append(f"Password must contain at least {self.min_special_chars} special character(s)")
        
        # Forbidden patterns
        for pattern in self.forbidden_patterns:
            if re.search(pattern, password, re.IGNORECASE):
                errors.append("Password contains forbidden patterns")
                break
        
        # Calculate strength
        strength = self._calculate_strength(password)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength": strength
        }
    
    def _calculate_strength(self, password: str) -> str:
        """
        Calculate password strength
        """
        score = 0
        
        # Length bonus
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if len(password) >= 16:
            score += 1
        
        # Character variety
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'[A-Z]', password):
            score += 1
        if re.search(r'\d', password):
            score += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        
        # Unique characters
        if len(set(password)) >= len(password) * 0.7:
            score += 1
        
        if score <= 3:
            return "weak"
        elif score <= 6:
            return "medium"
        else:
            return "strong"

class PasswordHasher:
    """
    Secure password hashing using bcrypt
    """
    
    def __init__(self, rounds: int = 12):
        """
        Initialize with bcrypt rounds (cost factor)
        
        Args:
            rounds: Bcrypt cost factor (4-31, default 12)
        """
        if rounds < 4 or rounds > 31:
            raise ValueError("Bcrypt rounds must be between 4 and 31")
        
        self.rounds = rounds
    
    def hash_password(self, password: str) -> str:
        """
        Hash password with bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        if not isinstance(password, str):
            raise TypeError("Password must be a string")
        
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password against hash
        
        Args:
            password: Plain text password
            hashed: Hashed password
            
        Returns:
            bool: True if password matches hash
        """
        if not isinstance(password, str) or not isinstance(hashed, str):
            return False
        
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'), 
                hashed.encode('utf-8')
            )
        except (ValueError, TypeError):
            return False
    
    def needs_rehash(self, hashed: str) -> bool:
        """
        Check if password hash needs to be updated
        
        Args:
            hashed: Hashed password
            
        Returns:
            bool: True if hash should be updated
        """
        try:
            # Extract cost factor from hash
            cost_factor = int(hashed[4:6])
            return cost_factor < self.rounds
        except (ValueError, IndexError):
            return True

class PasswordGenerator:
    """
    Secure password generation
    """
    
    @staticmethod
    def generate_password(
        length: int = 16,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
        include_digits: bool = True,
        include_special: bool = True,
        exclude_ambiguous: bool = True
    ) -> str:
        """
        Generate secure random password
        
        Args:
            length: Password length
            include_uppercase: Include uppercase letters
            include_lowercase: Include lowercase letters
            include_digits: Include digits
            include_special: Include special characters
            exclude_ambiguous: Exclude ambiguous characters (0, O, l, I, etc.)
            
        Returns:
            str: Generated password
        """
        if length < 4:
            raise ValueError("Password length must be at least 4")
        
        # Build character set
        chars = ""
        
        if include_lowercase:
            chars += string.ascii_lowercase
            if exclude_ambiguous:
                chars = chars.replace('l', '').replace('o', '')
        
        if include_uppercase:
            chars += string.ascii_uppercase
            if exclude_ambiguous:
                chars = chars.replace('I', '').replace('O', '')
        
        if include_digits:
            chars += string.digits
            if exclude_ambiguous:
                chars = chars.replace('0', '').replace('1', '')
        
        if include_special:
            special = '!@#$%^&*()_+-=[]{}|;:,.<>?'
            chars += special
        
        if not chars:
            raise ValueError("At least one character type must be included")
        
        # Generate password ensuring at least one character from each selected type
        password = []
        
        if include_lowercase:
            password.append(secrets.choice(string.ascii_lowercase))
        if include_uppercase:
            password.append(secrets.choice(string.ascii_uppercase))
        if include_digits:
            password.append(secrets.choice(string.digits))
        if include_special:
            password.append(secrets.choice('!@#$%^&*()_+-=[]{}|;:,.<>?'))
        
        # Fill remaining length
        remaining_length = length - len(password)
        for _ in range(remaining_length):
            password.append(secrets.choice(chars))
        
        # Shuffle the password
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    @staticmethod
    def generate_passphrase(
        word_count: int = 4,
        separator: str = '-',
        include_number: bool = True,
        capitalize: bool = True
    ) -> str:
        """
        Generate memorable passphrase
        
        Args:
            word_count: Number of words
            separator: Word separator
            include_number: Include random number
            capitalize: Capitalize first letter of each word
            
        Returns:
            str: Generated passphrase
        """
        # Simple word list (in production, use a larger dictionary)
        words = [
            'apple', 'banana', 'cherry', 'dragon', 'eagle', 'forest',
            'garden', 'honey', 'island', 'jungle', 'kitten', 'lemon',
            'mountain', 'ocean', 'penguin', 'rainbow', 'sunset', 'tiger',
            'umbrella', 'volcano', 'waterfall', 'zebra', 'adventure',
            'butterfly', 'crystal', 'dolphin', 'elephant', 'firefly'
        ]
        
        selected_words = []
        for _ in range(word_count):
            word = secrets.choice(words)
            if capitalize:
                word = word.capitalize()
            selected_words.append(word)
        
        passphrase = separator.join(selected_words)
        
        if include_number:
            number = secrets.randbelow(100)
            passphrase += f"{separator}{number}"
        
        return passphrase

# Default instances
default_policy = PasswordPolicy()
default_hasher = PasswordHasher()
password_generator = PasswordGenerator()

# Convenience functions
def hash_password(password: str) -> str:
    """Hash password using default settings"""
    return default_hasher.hash_password(password)

def verify_password(password: str, hashed: str) -> bool:
    """Verify password using default settings"""
    return default_hasher.verify_password(password, hashed)

def validate_password(password: str) -> Dict[str, any]:
    """Validate password using default policy"""
    return default_policy.validate_password(password)

def generate_secure_password(length: int = 16) -> str:
    """Generate secure password"""
    return password_generator.generate_password(length)

# Export main components
__all__ = [
    'PasswordPolicy', 'PasswordHasher', 'PasswordGenerator',
    'default_policy', 'default_hasher', 'password_generator',
    'hash_password', 'verify_password', 'validate_password', 'generate_secure_password'
]