import graphql


def transform(t, ctx):
    if graphql.is_type(t):
        return t

    gql_type = getattr(t, "__graphql_type__", None)

    return gql_type


def can_transform(t, ctx):
    return graphql.is_type(t) or hasattr(t, "__graphql_type__")
