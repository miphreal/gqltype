from datetime import timedelta as PyDuration

import aniso8601
import graphql
from graphql.language import ast


def format_simple_iso8601_duration(value: PyDuration) -> str:
    seconds = value.total_seconds()
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    seconds = round(seconds, 6)

    parts = []

    if days:
        parts.append(f"P{days:.0f}D")

    if any((hours, minutes, seconds)):
        parts.append("T")

    if hours:
        parts.append(f"{hours:.0f}H")
    if minutes:
        parts.append(f"{minutes:.0f}M")
    if seconds:
        if seconds.is_integer():
            seconds = int(seconds)
        parts.append(f"{seconds}S")

    return "".join(parts)


def serialize(value: PyDuration):
    return format_simple_iso8601_duration(value)


def coerce(value: str):
    return aniso8601.parse_duration(value)


def parse_literal(ast_node, _variables=None):
    if isinstance(ast_node, ast.StringValueNode):
        return aniso8601.parse_duration(ast_node.value)
    return graphql.INVALID


GraphQLDuration = graphql.GraphQLScalarType(
    name="Duration",
    description="The `Duration` scalar type represents ISO8601 duration.",
    serialize=serialize,
    parse_value=coerce,
    parse_literal=parse_literal,
)
