from ..graphql_types import SUPPORTED_TYPES


def transform(t, ctx):
    # Simple mapping of a registered type to GraphQL type
    if t in SUPPORTED_TYPES:
        return SUPPORTED_TYPES[t]

    return None


def can_transform(t, ctx):
    return t in SUPPORTED_TYPES
