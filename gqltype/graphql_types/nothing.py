import graphql

from ..utils import NoneType as PyNoneType


def serialize(value: PyNoneType):
    return None


def coerce(value: PyNoneType):
    return None


def parse_literal(ast_node, _variables=None):
    return graphql.INVALID


GraphQLNothing = graphql.GraphQLScalarType(
    name="Nothing",
    description="The `Nothing` scalar type represents NoneType.",
    serialize=serialize,
    parse_value=coerce,
    parse_literal=parse_literal,
)
