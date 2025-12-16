import graphene
from graphene_django.types import DjangoObjectType
from django.db import transaction, IntegrityError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db.models import Sum

from .models import Customer, Product, Order





class CustomValidationError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

def validate_phone(phone):
    """Simple phone number format validation."""
    if phone and not (phone.startswith('+') or '-' in phone or phone.isdigit()):
        raise CustomValidationError("Invalid phone format. Use formats like +1234567890 or 123-456-7890.")
    
    
    








class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ('id', 'name', 'email', 'phone')

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'stock')

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ('id', 'customer', 'products', 'order_date', 'total_amount')



class CRMQuery(graphene.ObjectType):

    all_customers = graphene.List(CustomerType)
    all_products = graphene.List(ProductType)
    all_orders = graphene.List(OrderType)


    def resolve_all_customers(root, info):
        return Customer.objects.all()

    def resolve_all_products(root, info):
        return Product.objects.all()

    def resolve_all_orders(root, info):
        return Order.objects.all()
    
    
    
# crm/schema.py

class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()

    # Define return fields
    customer = graphene.Field(CustomerType)
    message = graphene.String()
    success = graphene.Boolean()

    @classmethod
    def mutate(cls, root, info, name, email, phone=None):
        try:
            # 1. Email and Phone Validation
            validate_email(email)
            validate_phone(phone)
            
            # 2. Uniqueness Check (handled by IntegrityError on save, but explicit check for better error message)
            if Customer.objects.filter(email=email).exists():
                raise CustomValidationError("Email already exists.")

            customer = Customer.objects.create(
                name=name,
                email=email,
                phone=phone
            )
            return CreateCustomer(
                customer=customer, 
                message="Customer created successfully.",
                success=True
            )
        
        except CustomValidationError as e:
            return CreateCustomer(
                customer=None, 
                message=f"Validation Error: {e.message}",
                success=False
            )
        except ValidationError as e:
            # For Django's built-in email validation errors
            return CreateCustomer(
                customer=None, 
                message=f"Validation Error: {', '.join(e.messages)}",
                success=False
            )
        except Exception as e:
            # General error
            return CreateCustomer(
                customer=None, 
                message=f"An unexpected error occurred: {e}",
                success=False
            )
            
            
######################
# crm/schema.py

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @classmethod
    def mutate(cls, root, info, input):
        created_customers = []
        error_list = []
        customers_to_create = []

        # 1. Pre-validation and preparation
        for i, data in enumerate(input):
            try:
                # Basic Django email validation
                validate_email(data.email)
                validate_phone(data.phone)
                
                # Uniqueness check (critical for bulk, check against existing DB and current batch)
                if Customer.objects.filter(email=data.email).exists():
                    raise CustomValidationError("Email already exists in the database.")
                
                # Check for duplicates within the current bulk list
                if data.email in [c['email'] for c in customers_to_create]:
                     raise CustomValidationError("Duplicate email in the bulk list.")

                customers_to_create.append({
                    'name': data.name,
                    'email': data.email,
                    'phone': data.phone
                })

            except (CustomValidationError, ValidationError) as e:
                # Store the error message for the failed record
                error_message = getattr(e, 'message', str(e))
                error_list.append(f"Record {i+1} ({data.email}): {error_message}")
            except Exception as e:
                error_list.append(f"Record {i+1} ({data.email}): Unexpected error - {e}")

        # 2. Atomic creation of valid customers
        if customers_to_create:
            try:
                # Use a transaction block to ensure all valid customers are created or none are (if an internal DB error occurs)
                with transaction.atomic():
                    # Bulk create the valid customer records
                    db_customers = Customer.objects.bulk_create(
                        [Customer(**c) for c in customers_to_create]
                    )
                    created_customers = list(db_customers)
            except IntegrityError as e:
                # This catches any low-level DB unique constraint errors that might slip through
                error_list.append(f"Database Integrity Error during creation: {e}")
            except Exception as e:
                error_list.append(f"Unexpected error during atomic bulk creation: {e}")

        return BulkCreateCustomers(
            customers=created_customers,
            errors=error_list
        )
        
        
################################################

# crm/schema.py

class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Decimal(required=True)
        stock = graphene.Int()

    product = graphene.Field(ProductType)

    @classmethod
    def mutate(cls, root, info, name, price, stock=0):
        if price <= 0:
            raise Exception("Price must be a positive number.")
        if stock < 0:
            raise Exception("Stock cannot be negative.")

        product = Product.objects.create(
            name=name,
            price=price,
            stock=stock
        )
        return CreateProduct(product=product)
    
    
##############################################

# crm/schema.py

class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.DateTime() # Optional, will default to auto_now_add in model

    order = graphene.Field(OrderType)

    @classmethod
    @transaction.atomic # Ensure all DB operations succeed or fail together
    def mutate(cls, root, info, customer_id, product_ids, order_date=None):
        if not product_ids:
            raise Exception("Order must contain at least one product.")
        
        try:
            # 1. Validate Customer
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise Exception(f"Invalid customer ID: {customer_id}")

        # 2. Validate Products
        # Check if all provided IDs are valid and retrieve the Product objects
        products = Product.objects.filter(pk__in=product_ids)
        if products.count() != len(product_ids):
            # Identify which IDs are invalid (Challenge: custom error message)
            valid_ids = products.values_list('id', flat=True)
            invalid_ids = [pid for pid in product_ids if int(pid) not in valid_ids]
            raise Exception(f"Invalid product ID(s) found: {', '.join(map(str, invalid_ids))}")

        # 3. Calculate total_amount
        # Note: Sum() aggregates the DecimalField values correctly
        total_amount = products.aggregate(Sum('price'))['price__sum']

        # 4. Create Order
        order = Order.objects.create(
            customer=customer,
            total_amount=total_amount,
            # order_date is handled by auto_now_add, but if provided, can be set
            # For simplicity, we stick to the model's auto_now_add
        )

        # 5. Associate Products (Many-to-Many relationship)
        order.products.set(products)

        return CreateOrder(order=order)

############################################# 

# crm/schema.py (Final combined section)

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()




# crm/schema.py doesn't contain: ["save()"]

  
  
  
  
import graphene
from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField # NEW IMPORT
# ... other imports (from task 1: transaction, models, etc.)

from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter # NEW IMPORT

# --- 1. Define Graphene Types (Ensure they inherit from DjangoObjectType and have a Node) ---

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        # fields = ('id', 'name', 'email', 'phone', 'created_at') 
        # Use interfaces and connection for DjangoFilterConnectionField
        interfaces = (graphene.Node,) 
        filter_fields = '__all__' # Used by DjangoFilterConnectionField

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        # fields = ('id', 'name', 'price', 'stock')
        interfaces = (graphene.Node,)
        filter_fields = '__all__'

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        # fields = ('id', 'customer', 'products', 'order_date', 'total_amount')
        interfaces = (graphene.Node,)
        filter_fields = '__all__'

# --- 2. Define Query (Filtered and Sorted) ---

class CRMQuery(graphene.ObjectType):
    # The 'hello' field is kept here if it was defined in the previous task.
    # hello = graphene.String(default_value="Hello, GraphQL!")

    # Use DjangoFilterConnectionField for filtering and pagination (relay style)

    # 1. Customers
    all_customers = DjangoFilterConnectionField(
        CustomerType,
        filterset_class=CustomerFilter, # Use the custom filter class
        # order_by argument is automatically added by Graphene-Django's filter
    )

    # 2. Products
    all_products = DjangoFilterConnectionField(
        ProductType,
        filterset_class=ProductFilter
    )

    # 3. Orders
    all_orders = DjangoFilterConnectionField(
        OrderType,
        filterset_class=OrderFilter
    )
    
    # Note: When using DjangoFilterConnectionField, the resolvers (like resolve_all_customers) 
    # are automatically handled by Graphene-Django. You only define them if you need complex
    # pre-filtering logic, which is not required here.
    
# --- (Rest of schema.py remains the same: Mutation, etc.) ---


  
    