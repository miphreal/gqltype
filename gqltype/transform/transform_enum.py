import enum
from typing import List, Type

import graphql
from graphql.type.definition import GraphQLEnumValue

from ..utils import (
    cache_type,
    get_annotations,
    get_doc,
    get_name,
    is_class,
    is_type_container,
    unwrap_type_container,
)


class GraphQLEnumType(graphql.GraphQLEnumType):
    def __init__(self, enum_cls, *args, **kwargs):
        self.enum_cls = enum_cls
        super().__init__(*args, **kwargs)

    def serialize(self, output_value):
        # make sure resolved value is of `enum_cls` type
        return super().serialize(self.enum_cls(output_value))


def _to_enum_value(value, ctx) -> GraphQLEnumValue:
    params = ("description", "deprecation_reason")
    return GraphQLEnumValue(value=value, **{k: ctx[k] for k in params if k in ctx})


@cache_type
def _transform_enum(enum_cls: Type[enum.Enum], ctx) -> graphql.GraphQLEnumType:
    annotations = get_annotations(enum_cls)

    values = {}

    enum_values: List[enum.Enum] = list(enum_cls)

    for enum_val in enum_values:
        annotation = annotations.get(enum_val.name)
        if is_type_container(annotation):
            t, meta = unwrap_type_container(annotation)
            value = _to_enum_value(
                enum_val, meta.meta
            )  # TODO.`meta.meta` think of a better interface
        else:
            value = _to_enum_value(enum_val, ctx)
        value = _to_enum_value(enum_val, ctx)

        values[enum_val.name] = value

    name = get_name(enum_cls)
    description = get_doc(enum_cls)

    if ctx.recognize_enum_output_values:
        return GraphQLEnumType(
            enum_cls=enum_cls, name=name, values=values, description=description
        )
    return graphql.GraphQLEnumType(name=name, values=values, description=description)


def transform(t, ctx):
    return _transform_enum(t, ctx)


def can_transform(t, ctx):
    return is_class(t) and issubclass(t, enum.Enum)
