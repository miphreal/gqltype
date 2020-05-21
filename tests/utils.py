from datetime import date, datetime
from dataclasses import dataclass, field, InitVar
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Union, ClassVar
from uuid import UUID

from hamcrest import *
from hamcrest.core.base_matcher import BaseMatcher
import graphql
import pytest

TYPES = {
    bool: "Boolean",
    int: "Int",
    str: "String",
    float: "Float",
    Decimal: "Decimal",
    UUID: "UUID",
}


class GraphQLTypeMatcher(BaseMatcher):
    def __init__(self, type_):
        self.type_ = type_

    def _matches(self, item):
        return graphql.is_type(item) and str(item) == str(self.type_)

    def describe_to(self, description):
        description.append_text(str(self.type_))


def is_graphql_type(type_):
    return GraphQLTypeMatcher(type_)


def is_graphql_object_type(*args, **fields):
    name, description, *_ = list(args) + [None, None]
    extra = {}
    if name:
        extra["name"] = equal_to(name)
    if description:
        extra["description"] = equal_to(description)

    return all_of(
        instance_of(graphql.GraphQLObjectType),
        has_properties(
            {
                "fields": has_entries(
                    {k: is_graphql_field(t) for k, t in fields.items()}
                ),
                **extra,
            }
        ),
    )


def is_graphql_field(type_, description=None, deprecation_reason=None):
    _matchers = {"type": is_graphql_type(type_)}

    if description is not None:
        _matchers["description"] = equal_to(description)
    if deprecation_reason is not None:
        _matchers["deprecation_reason"] = equal_to(deprecation_reason)

    matchers = [instance_of(graphql.GraphQLField), has_properties(**_matchers)]

    return all_of(*matchers)


def is_graphql_argument(
    type_, description=None, default_value=graphql.INVALID, out_name=None
):
    _matchers = {"type": is_graphql_type(type_)}

    if description is not None:
        _matchers["description"] = equal_to(description)
    if default_value is not graphql.INVALID:
        _matchers["default_value"] = equal_to(default_value)
    if out_name is not None:
        _matchers["out_name"] = equal_to(out_name)

    matchers = [instance_of(graphql.GraphQLArgument), has_properties(**_matchers)]

    return all_of(*matchers)
