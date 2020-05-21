import logging
import typing

import graphql

from ..utils import is_typing_type, filter_out_none_type, UnwrappedType, NoneType
from .type_container import T


logger = logging.getLogger(__name__)


def _is_nullable(t):
    """Checks if it's a Union[T, NoneType] or Optional[T] (which is the same)"""
    return (
        is_typing_type(t)
        and getattr(t, "__origin__", None) is typing.Union
        and NoneType in getattr(t, "__args__", ())
    )


def _transform_nullable(t, ctx):
    union_types = filter_out_none_type(t.__args__)

    # Optional[T1] which is Union[T1, NoneType]
    if len(union_types) == 1:
        return UnwrappedType(
            final_type=ctx.transformer.transform(union_types[0], allow_null=True)
        )

    # Union[T1, T2, NoneType] -- it's optional union
    return UnwrappedType(
        final_type=ctx.transformer.transform(
            typing.Union[tuple(union_types)], allow_null=True
        )
    )


def _is_list_annotation(t):
    return is_typing_type(t) and getattr(t, "_name", None) == "List"


def _transform_list(t, ctx):
    return graphql.GraphQLList(ctx.transformer.transform(t.__args__[0]))


def transform(t, ctx):
    if _is_nullable(t):
        return _transform_nullable(t, ctx)

    # List[T1]
    if _is_list_annotation(t):
        return _transform_list(t, ctx)

    raise TypeError(f"{t} cannot be handled as type hint.")


def can_transform(t, ctx):
    return _is_nullable(t) or _is_list_annotation(t)
