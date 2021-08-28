import typing

import graphql

from ..utils import cache_type, get_name, filter_out_none_type


def _to_union(**kwargs):
    params = ("name", "types", "resolve_type", "description")
    kwargs = {k: v for k, v in kwargs.items() if k in params}
    return graphql.GraphQLUnionType(**kwargs)


def _is_union_annotation(t):
    """Checks if it's a Union[T1, T2] annotation"""
    return typing.get_origin(t) is typing.Union


def _is_union_definition(t):
    # TypeVar('Type', T1, T2)
    if hasattr(t, "__constraints__"):
        types_ = filter_out_none_type(t.__constraints__)

        # Generic typevar would not work, e.g. TypeVar('T')
        return bool(types_)

    # Union[T1, T2]
    if _is_union_annotation(t):
        types_ = filter_out_none_type(typing.get_args(t))

        # At least two types are required
        # because `Union[str]` is the same as just `str`
        # Note. If you need to define union with just one type,
        # use TypeVar (actually, it should be a rare case).
        return len(types_) > 1

    return False


@cache_type
def _transform_union(t, ctx):
    name = None

    # handle TypeVar('SomeUnion', T1, T2, T3)
    if hasattr(t, "__constraints__"):
        name = get_name(t)
        types_ = t.__constraints__

    # handle Union[T1, T2, T3]
    elif _is_union_annotation(t):
        types_ = typing.get_args(t)

    else:
        TypeError("Cannot transform {t} to union: unknown definition.")

    # graphql union cannot be defined with nullable types.
    types_ = filter_out_none_type(types_)
    gql_types = [
        graphql.get_nullable_type(ctx.transformer.transform(_t)) for _t in types_
    ]

    # Sanity check
    for t in gql_types:
        if not graphql.is_object_type(t):
            raise TypeError(f"Union can contain only object types, got {t} (Scalar?).")

    name = ctx.get("name", name)
    if name is None:
        name = "".join(map(str, gql_types)) + "Union"

    description = ctx.get("description")
    resolve_type = ctx.get("resolve_type")
    types_map = dict(zip(types_, gql_types))
    if resolve_type is None:
        resolve_type = ctx.hook__prepare_default_union_type_resolver(name, types_map)
    else:
        resolve_type = ctx.hook__prepare_union_type_resolver(
            resolve_type, name, types_map
        )

    return _to_union(
        name=name, types=gql_types, resolve_type=resolve_type, description=description
    )


def transform(t, ctx):
    return _transform_union(t, ctx)


def can_transform(t, ctx):
    return _is_union_definition(t)
