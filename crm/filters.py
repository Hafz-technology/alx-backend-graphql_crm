import django_filters
from django.db.models import Q
from .models import Customer, Product, Order

class CustomerFilter(django_filters.FilterSet):
    # Challenge: Custom filter for phone pattern (starts with +1)
    phone_pattern = django_filters.CharFilter(
        method='filter_by_phone_pattern',
        label='Phone pattern filter (e.g., +1)'
    )
    
    class Meta:
        model = Customer
        fields = {
            # Case-insensitive partial match
            'name': ['icontains'], 
            'email': ['icontains'],
            # Date range filter
            'created_at': ['gte', 'lte'], 
        }

    def filter_by_phone_pattern(self, queryset, name, value):
        """Custom method to filter by phone number starting pattern."""
        return queryset.filter(phone__startswith=value)

class ProductFilter(django_filters.FilterSet):
    # Challenge: Filter products with low stock (stock < N)
    low_stock_limit = django_filters.NumberFilter(
        field_name='stock', 
        lookup_expr='lt', 
        label='Stock less than'
    )

    class Meta:
        model = Product
        fields = {
            # Case-insensitive partial match
            'name': ['icontains'],
            # Range filter
            'price': ['gte', 'lte'],
            'stock': ['exact', 'gte', 'lte'],
        }

class OrderFilter(django_filters.FilterSet):
    # Related field lookups for customer and product names
    customer_name = django_filters.CharFilter(
        field_name='customer__name', 
        lookup_expr='icontains', 
        label='Customer Name (partial, case-insensitive)'
    )
    product_name = django_filters.CharFilter(
        field_name='products__name', 
        lookup_expr='icontains', 
        label='Product Name (partial, case-insensitive)'
    )
    
    # Challenge: Filter by specific product ID
    product_id = django_filters.NumberFilter(
        field_name='products__id', 
        lookup_expr='exact', 
        label='Filter by Product ID'
    )

    class Meta:
        model = Order
        fields = {
            # Range filter
            'total_amount': ['gte', 'lte'],
            # Date range filter
            'order_date': ['gte', 'lte'],
        }
        
        
        
        