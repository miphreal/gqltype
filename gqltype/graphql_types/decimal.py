from decimal import Decimal as PyDecimal

import graphql
from graphql.language import ast


def serialize(value):
    if not isinstance(value, PyDecimal):
        value = PyDecimal(value)
    return str(value)


def coerce(value):
    return PyDecimal(value)


def parse_literal(ast_node, _variables=None):
    if isinstance(
        ast_node, (ast.FloatValueNode, ast.IntValueNode, ast.StringValueNode)
    ):
        return PyDecimal(ast_node.value)
    return graphql.INVALID


GraphQLDecimal = graphql.GraphQLScalarType(
    name="Decimal",
    description="The `Decimal` scalar type.",
    serialize=serialize,
    parse_value=coerce,
    parse_literal=parse_literal,
)
