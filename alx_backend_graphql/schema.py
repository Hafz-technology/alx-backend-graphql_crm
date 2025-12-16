# import graphene

# class Query(graphene.ObjectType):
#     hello = graphene.String(default_value="Hello, GraphQL!")


# # Create the root schema using the Query class
# schema = graphene.Schema(query=Query)



# # crm/schema.py

# import graphene

# class CRMQuery(graphene.ObjectType):
#     # This class will be populated with fields like:
#     # all_customers = graphene.List(CustomerType)
#     # all_sales = graphene.List(SalesType)
#     # in the next task. For now, it's just a placeholder.
#     pass






# class Query(CRMQuery, graphene.ObjectType):
#     pass
# # We usually export only the query class, as the root schema is in the main project folder







import graphene
# Import Query and Mutation from the app's schema file
from crm.schema import CRMQuery, Mutation as CRMMutation

# Combine all Query classes
class Query(CRMQuery, graphene.ObjectType):
    # Keep the initial 'hello' field if required by Task 0
    hello = graphene.String(default_value="Hello, GraphQL!")

# Combine all Mutation classes
class Mutation(CRMMutation, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)




import graphene
from crm.schema import CRMQuery, Mutation as CRMMutation

# Combine all Query classes
class Query(CRMQuery, graphene.ObjectType):
    # Keep the initial 'hello' field if required by Task 0
    hello = graphene.String(default_value="Hello, GraphQL!")

# Combine all Mutation classes
class Mutation(CRMMutation, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)


