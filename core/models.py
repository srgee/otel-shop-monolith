import uuid

from django.conf import settings
from django.db import models


class Category(models.Model):
    """Categories used to group products and target advertisements."""
    name = models.CharField(max_length=50, unique=True)
    
    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Product(models.Model):
    """Core entity of the store."""
    id = models.CharField(
        max_length=50, 
        primary_key=True, 
        help_text="Product ID (e.g. OLJCESPC7Z)"
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    picture_url = models.CharField(max_length=255)
    
    # Base system currency USD
    price_usd_units = models.IntegerField(default=0)
    price_usd_nanos = models.IntegerField(default=0)
    
    categories = models.ManyToManyField(Category, related_name='products')

    def get_price_float(self):
        return self.price_usd_units + (self.price_usd_nanos / 1_000_000_000)

    def __str__(self):
        return self.name


class Advertisement(models.Model):
    """Contextual advertisements based on categories."""
    redirect_url = models.CharField(max_length=255)
    text = models.CharField(max_length=255)
    target_category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='ads'
    )

    def __str__(self):
        return f"Ad: {self.text[:30]}..."


class Cart(models.Model):
    """Purchase status of current user (user_id for logged-in users or session_key otherwise)."""  # noqa: E501
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Asegura que no haya carritos duplicados activos
        constraints = [
            models.UniqueConstraint(
                fields=['user'], 
                condition=models.Q(user__isnull=False), 
                name='unique_user_cart'
            ),
            models.UniqueConstraint(
                fields=['session_key'], 
                condition=models.Q(user__isnull=True), 
                name='unique_session_cart'
            ),
        ]

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"



class Order(models.Model):
    """Order history."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
      )
    
    email = models.EmailField()
    shipping_address_street = models.CharField(max_length=255)
    shipping_address_city = models.CharField(max_length=100)
    shipping_address_state = models.CharField(max_length=50, blank=True)
    shipping_address_country = models.CharField(max_length=50)
    shipping_zip_code = models.CharField(max_length=20)

    total_cost_usd = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost_usd = models.DecimalField(max_digits=10, decimal_places=2)
    
    transaction_id = models.CharField(max_length=100)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PAID')

    def __str__(self):
        return f"Order {self.id} - {self.email}"

class OrderItem(models.Model):
    """Immutable copy of purchased items."""
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    
    quantity = models.PositiveIntegerField()

    unit_price_usd = models.DecimalField(max_digits=10, decimal_places=2)

    def get_total_price(self):
        return self.quantity * self.unit_price_usd

# -----------------------------------------------------------------------------
# 5. MONEDA (Opcional, reemplaza CurrencyService)
# -----------------------------------------------------------------------------

class CurrencyConversion(models.Model):
    """Cache table for currency exchange rates."""
    code = models.CharField(max_length=3, primary_key=True)  # EUR, JPY
    rate_relative_to_usd = models.DecimalField(max_digits=20, decimal_places=10)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"1 USD = {self.rate_relative_to_usd} {self.code}"