from uuid import UUID as PyUUID

import graphql
from graphql.language import ast


def serialize(value: PyUUID):
    if not isinstance(value, PyUUID):
        value = PyUUID(value)
    return str(value)


def coerce(value):
    return PyUUID(value)


def parse_literal(ast_node, _variables=None):
    if isinstance(ast_node, ast.StringValueNode):
        return PyUUID(ast_node.value)
    return graphql.INVALID


GraphQLUUID = graphql.GraphQLScalarType(
    name="UUID",
    description="The `UUID` scalar type.",
    serialize=serialize,
    parse_value=coerce,
    parse_literal=parse_literal,
)
