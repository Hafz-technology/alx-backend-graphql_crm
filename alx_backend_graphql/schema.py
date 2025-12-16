import graphene

class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")


# Create the root schema using the Query class
schema = graphene.Schema(query=Query)



# crm/schema.py

import graphene

class CRMQuery(graphene.ObjectType):
    # This class will be populated with fields like:
    # all_customers = graphene.List(CustomerType)
    # all_sales = graphene.List(SalesType)
    # in the next task. For now, it's just a placeholder.
    pass






class Query(CRMQuery, graphene.ObjectType):
    pass
# We usually export only the query class, as the root schema is in the main project folder