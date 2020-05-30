from datetime import datetime as PyDateTime

import aniso8601
import graphql
from graphql.language import ast


def serialize(value: PyDateTime):
    if not isinstance(value, PyDateTime):
        value = aniso8601.parse_datetime(value)
    return value.isoformat()


def coerce(value: str):
    return aniso8601.parse_datetime(value)


def parse_literal(ast_node, _variables=None):
    if isinstance(ast_node, ast.StringValueNode):
        return aniso8601.parse_datetime(ast_node.value)
    return graphql.INVALID


GraphQLDateTime = graphql.GraphQLScalarType(
    name="DateTime",
    description="The `DateTime` scalar type represents ISO 8601 datetime.",
    serialize=serialize,
    parse_value=coerce,
    parse_literal=parse_literal,
)
