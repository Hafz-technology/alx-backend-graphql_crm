import graphene

class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")


# Create the root schema using the Query class
schema = graphene.Schema(query=Query)

