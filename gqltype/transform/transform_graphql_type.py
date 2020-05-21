import graphql


def transform(t, ctx):
    if graphql.is_type(t):
        return t

    return None


def can_transform(t, ctx):
    return graphql.is_type(t)
