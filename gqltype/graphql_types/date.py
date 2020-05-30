from datetime import date as PyDate

import aniso8601
import graphql
from graphql.language import ast


def serialize(value: PyDate):
    if not isinstance(value, PyDate):
        value = aniso8601.parse_date(value)
    return value.isoformat()


def coerce(value: str):
    return aniso8601.parse_date(value)


def parse_literal(ast_node, _variables=None):
    if isinstance(ast_node, ast.StringValueNode):
        return aniso8601.parse_date(ast_node.value)
    return graphql.INVALID


GraphQLDate = graphql.GraphQLScalarType(
    name="Date",
    description="The `Date` scalar type represents ISO 8601 date.",
    serialize=serialize,
    parse_value=coerce,
    parse_literal=parse_literal,
)
