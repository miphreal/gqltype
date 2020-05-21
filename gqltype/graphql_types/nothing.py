import graphql
from graphql.language import ast

from ..utils import NoneType


def serialize(value: NoneType):
    return None


def coerce(value: NoneType):
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
