import enum

import graphql
from graphql.type.definition import GraphQLEnumValue

from ..utils import cache_type, get_annotations, get_name, get_doc, is_class
from .type_container import T


def _to_enum_value(value, ctx) -> GraphQLEnumValue:
    params = ("description", "deprecation_reason")
    return GraphQLEnumValue(value=value, **{k: ctx[k] for k in params if k in ctx})


@cache_type
def _transform_enum(enum_cls: enum.Enum, ctx) -> graphql.GraphQLEnumType:
    annotations = get_annotations(enum_cls)

    values = {}

    for enum_val in list(enum_cls):
        annotation = annotations.get(enum_val.name)
        if isinstance(annotation, T):
            value = _to_enum_value(enum_val, ctx(**annotation.graphql_kw))
        else:
            value = _to_enum_value(enum_val, ctx)

        values[enum_val.name] = value

    return graphql.GraphQLEnumType(
        name=get_name(enum_cls), values=values, description=get_doc(enum_cls)
    )


def transform(t, ctx):
    return _transform_enum(t, ctx)


def can_transform(t, ctx):
    return is_class(t) and issubclass(t, enum.Enum)
