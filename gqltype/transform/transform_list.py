from types import GenericAlias

import graphql

from ..utils import is_typing_type


def transform(t, ctx):
    return graphql.GraphQLList(ctx.transformer.transform(t.__args__[0]))


def can_transform(t, ctx):
    # List[T1]
    if is_typing_type(t) and getattr(t, "_name", None) == "List":
        return True

    # list[T1]
    if isinstance(t, GenericAlias) and issubclass(t.__origin__, list):
        return True

    return False
