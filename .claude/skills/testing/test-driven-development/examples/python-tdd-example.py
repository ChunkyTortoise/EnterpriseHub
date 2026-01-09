"""
Complete TDD Example: Shopping Cart Implementation
Demonstrates RED → GREEN → REFACTOR cycle
"""

import pytest
from decimal import Decimal
from typing import List, Dict


# ============================================================================
# RED PHASE - Write Failing Tests
# ============================================================================

class TestShoppingCart:
    """Test suite following TDD principles"""

    def test_empty_cart_has_zero_total(self):
        """RED: Test that fails initially"""
        cart = ShoppingCart()

        total = cart.calculate_total()

        assert total == Decimal('0.00')

    def test_can_add_single_item(self):
        """RED: Test for adding items"""
        cart = ShoppingCart()

        cart.add_item("laptop", Decimal('999.99'))

        assert len(cart.items) == 1
        assert cart.items[0]['name'] == "laptop"
        assert cart.items[0]['price'] == Decimal('999.99')

    def test_calculate_total_with_single_item(self):
        """RED: Test total calculation"""
        cart = ShoppingCart()
        cart.add_item("laptop", Decimal('999.99'))

        total = cart.calculate_total()

        assert total == Decimal('999.99')

    def test_calculate_total_with_multiple_items(self):
        """RED: Test multiple items"""
        cart = ShoppingCart()
        cart.add_item("laptop", Decimal('999.99'))
        cart.add_item("mouse", Decimal('29.99'))

        total = cart.calculate_total()

        assert total == Decimal('1029.98')

    def test_apply_discount_percentage(self):
        """RED: Test discount functionality"""
        cart = ShoppingCart()
        cart.add_item("laptop", Decimal('1000.00'))

        discounted_total = cart.apply_discount(Decimal('10'))  # 10%

        assert discounted_total == Decimal('900.00')

    def test_cannot_apply_negative_discount(self):
        """RED: Test error handling"""
        cart = ShoppingCart()
        cart.add_item("laptop", Decimal('1000.00'))

        with pytest.raises(ValueError, match="Discount cannot be negative"):
            cart.apply_discount(Decimal('-5'))

    def test_cannot_add_item_with_negative_price(self):
        """RED: Test input validation"""
        cart = ShoppingCart()

        with pytest.raises(ValueError, match="Price cannot be negative"):
            cart.add_item("invalid_item", Decimal('-10.00'))


# ============================================================================
# GREEN PHASE - Minimal Implementation
# ============================================================================

class ShoppingCart:
    """Minimal implementation to make tests pass"""

    def __init__(self):
        # GREEN: Initialize empty cart
        self.items: List[Dict] = []

    def add_item(self, name: str, price: Decimal) -> None:
        """GREEN: Add item with validation"""
        if price < 0:
            raise ValueError("Price cannot be negative")

        self.items.append({
            'name': name,
            'price': price
        })

    def calculate_total(self) -> Decimal:
        """GREEN: Calculate total price"""
        return sum(item['price'] for item in self.items)

    def apply_discount(self, discount_percentage: Decimal) -> Decimal:
        """GREEN: Apply percentage discount"""
        if discount_percentage < 0:
            raise ValueError("Discount cannot be negative")

        total = self.calculate_total()
        discount_amount = total * (discount_percentage / Decimal('100'))
        return total - discount_amount


# ============================================================================
# REFACTOR PHASE - Improve Design
# ============================================================================

class CartItem:
    """REFACTOR: Extract item as separate class"""

    def __init__(self, name: str, price: Decimal, quantity: int = 1):
        self.name = self._validate_name(name)
        self.price = self._validate_price(price)
        self.quantity = self._validate_quantity(quantity)

    @staticmethod
    def _validate_name(name: str) -> str:
        if not name or not name.strip():
            raise ValueError("Item name cannot be empty")
        return name.strip()

    @staticmethod
    def _validate_price(price: Decimal) -> Decimal:
        if price < 0:
            raise ValueError("Price cannot be negative")
        return price

    @staticmethod
    def _validate_quantity(quantity: int) -> int:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        return quantity

    def subtotal(self) -> Decimal:
        """Calculate subtotal for this item"""
        return self.price * self.quantity


class ShoppingCartRefactored:
    """REFACTOR: Improved design with better structure"""

    def __init__(self):
        self._items: List[CartItem] = []

    @property
    def items(self) -> List[CartItem]:
        """Read-only access to items"""
        return self._items.copy()

    def add_item(self, name: str, price: Decimal, quantity: int = 1) -> None:
        """Add item to cart with quantity support"""
        item = CartItem(name, price, quantity)
        self._items.append(item)

    def remove_item(self, name: str) -> bool:
        """Remove first matching item from cart"""
        for i, item in enumerate(self._items):
            if item.name == name:
                del self._items[i]
                return True
        return False

    def calculate_total(self) -> Decimal:
        """Calculate total price of all items"""
        return sum(item.subtotal() for item in self._items)

    def apply_discount(self, discount_percentage: Decimal) -> Decimal:
        """Apply percentage discount to total"""
        if discount_percentage < 0:
            raise ValueError("Discount cannot be negative")
        if discount_percentage > 100:
            raise ValueError("Discount cannot exceed 100%")

        total = self.calculate_total()
        discount_amount = total * (discount_percentage / Decimal('100'))
        return total - discount_amount

    def is_empty(self) -> bool:
        """Check if cart is empty"""
        return len(self._items) == 0

    def item_count(self) -> int:
        """Get total quantity of items"""
        return sum(item.quantity for item in self._items)


# ============================================================================
# ADDITIONAL TESTS FOR REFACTORED VERSION
# ============================================================================

class TestShoppingCartRefactored:
    """Tests for refactored implementation"""

    def test_add_item_with_quantity(self):
        cart = ShoppingCartRefactored()

        cart.add_item("pen", Decimal('2.00'), 5)

        assert cart.item_count() == 5
        assert cart.calculate_total() == Decimal('10.00')

    def test_remove_item_from_cart(self):
        cart = ShoppingCartRefactored()
        cart.add_item("laptop", Decimal('999.99'))

        removed = cart.remove_item("laptop")

        assert removed is True
        assert cart.is_empty() is True

    def test_remove_nonexistent_item(self):
        cart = ShoppingCartRefactored()

        removed = cart.remove_item("nonexistent")

        assert removed is False

    def test_discount_cannot_exceed_100_percent(self):
        cart = ShoppingCartRefactored()
        cart.add_item("item", Decimal('100.00'))

        with pytest.raises(ValueError, match="Discount cannot exceed 100%"):
            cart.apply_discount(Decimal('150'))


# ============================================================================
# TDD CYCLE DEMONSTRATION
# ============================================================================

def demonstrate_tdd_cycle():
    """
    Demonstration of complete TDD cycle:

    1. RED: Write failing test
    2. GREEN: Make test pass with minimal code
    3. REFACTOR: Improve design while keeping tests green

    This example shows:
    - Starting with simple failing tests
    - Writing minimal implementation
    - Gradually adding features through more tests
    - Refactoring to improve design
    - Maintaining test coverage throughout
    """

    # Step 1: RED - Test fails (no implementation yet)
    print("🔴 RED: Writing failing test...")

    # Step 2: GREEN - Minimal implementation
    print("🟢 GREEN: Writing minimal code to pass test...")

    # Step 3: REFACTOR - Improve design
    print("🔵 REFACTOR: Improving design while keeping tests green...")

    # Step 4: Repeat cycle for next feature
    print("🔄 REPEAT: Next feature, next cycle...")


if __name__ == "__main__":
    # Run the TDD demonstration
    demonstrate_tdd_cycle()

    # Run tests to verify implementation
    print("\n" + "="*50)
    print("Running TDD Example Tests")
    print("="*50)

    # Example usage of refactored cart
    cart = ShoppingCartRefactored()
    cart.add_item("MacBook Pro", Decimal('2499.00'))
    cart.add_item("Magic Mouse", Decimal('79.00'), 2)

    print(f"Cart total: ${cart.calculate_total()}")
    print(f"With 10% discount: ${cart.apply_discount(Decimal('10'))}")
    print(f"Total items: {cart.item_count()}")