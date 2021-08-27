import logging
import typing

import graphql

from ..utils import is_typing_type


logger = logging.getLogger(__name__)


def _is_list_annotation(t):
    # TODO. is it still valid for 3.10+
    return is_typing_type(t) and getattr(t, "_name", None) == "List"


def _transform_list(t, ctx):
    return graphql.GraphQLList(ctx.transformer.transform(t.__args__[0]))


def transform(t, ctx):
    # List[T1]
    if _is_list_annotation(t):
        return _transform_list(t, ctx)

    raise TypeError(f"{t} cannot be handled as type hint.")


def can_transform(t, ctx):
    return _is_list_annotation(t)
