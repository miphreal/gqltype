from datetime import time as PyTime

import aniso8601
import graphql
from graphql.language import ast


def serialize(value: PyTime):
    return value.isoformat()


def coerce(value: str):
    return aniso8601.parse_time(value)


def parse_literal(ast_node, _variables=None):
    if isinstance(ast_node, ast.StringValueNode):
        return aniso8601.parse_time(ast_node.value)
    return graphql.INVALID


GraphQLTime = graphql.GraphQLScalarType(
    name="Time",
    description="The `Time` scalar type represents ISO 8601 time.",
    serialize=serialize,
    parse_value=coerce,
    parse_literal=parse_literal,
)
