from ..graphql_types.nothing import GraphQLNothing
from ..utils import UnwrappedType, NoneType


def transform(t, ctx):
    return UnwrappedType(final_type=GraphQLNothing)


def can_transform(t, ctx):
    return t is NoneType
