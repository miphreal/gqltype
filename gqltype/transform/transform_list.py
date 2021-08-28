import typing

import graphql


def transform(t: typing.Type[list], ctx):
    list_element_type = typing.get_args(t)[0]
    return graphql.GraphQLList(ctx.transformer.transform(list_element_type))


def can_transform(t, ctx):
    # List[T1] or list[T1]
    return typing.get_origin(t) is list
