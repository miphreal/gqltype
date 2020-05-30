from collections import OrderedDict
from dataclasses import is_dataclass, fields as dataclass_fields
import enum
import inspect
import logging
from functools import partial, wraps

import graphql

from ..context import TransformContext
from ..decorators import is_query, is_subscription, is_mutation
from ..graphql_types import ID
from ..utils import (
    cache_type,
    get_name,
    get_doc,
    get_attr_definitions,
    is_class,
    is_interface,
    get_interfaces,
    MISSING,
)
from ..utils.func import inspect_function
from .type_container import T


logger = logging.getLogger(__name__)


def to_field(t, ctx: TransformContext):
    params = ("args", "resolve", "subscribe", "description", "deprecation_reason")
    return graphql.GraphQLField(t, **{k: ctx[k] for k in params if k in ctx})


def to_input_field(t, ctx: TransformContext):
    params = ("description", "default_value", "out_name")
    return graphql.GraphQLInputField(t, **{k: ctx[k] for k in params if k in ctx})


def to_arg(t, ctx: TransformContext):
    params = ("description", "default_value", "out_name")
    return graphql.GraphQLArgument(t, **{k: ctx[k] for k in params if k in ctx})


def to_graphql_arguments(arguments, ctx: TransformContext):
    args = {}

    for arg_name, arg_type, default in arguments:
        if arg_type is None:
            raise TypeError(f"Cannot find type definition for argument '{arg_name}'")

        if ctx.auto_graphql_id and arg_name == "id" and arg_type is str:
            arg_type = ID

        kw = {}

        if isinstance(default, enum.Enum):
            default = default.value

        if default is not MISSING:
            kw["default_value"] = default

        gql_arg_type = ctx.transformer.transform(
            arg_type, allow_null=MISSING, is_input_type=True
        )

        kw["out_name"] = arg_name

        t = to_arg(gql_arg_type, ctx(**kw))
        args[ctx.hook__convert_name(arg_name, for_type=t)] = t

    return args


def iterate_class_attributes_for_output_type(cls, ctx: TransformContext):
    resolve_prefix = ctx.resolve_method_name_prefix
    subscribe_prefix = ctx.subscribe_method_name_prefix

    attrs = [
        *get_attr_definitions(cls, only_props=True).values(),
        *get_attr_definitions(cls, only_funcs=True).values(),
    ]

    names = set()

    for definition in attrs:
        if not (definition.annotation or definition.type_):
            continue

        name = definition.name
        value = definition.value

        resolve_fn = subscribe_fn = None
        field_kw = {}

        # function definition
        if inspect.isfunction(value) or inspect.ismethod(value):
            fn = value
            value = MISSING
            field_kw["description"] = get_doc(fn)

            # remove `resolve_` name prefix
            if name.startswith(resolve_prefix):
                name = name[len(resolve_prefix) :]
                resolve_fn = fn

            elif is_query(fn) or is_mutation(fn):
                resolve_fn = fn

            # remove `subscribe_` name prefix
            elif name.startswith(subscribe_prefix):
                name = name[len(subscribe_prefix) :]
                subscribe_fn = fn

            elif is_subscription(fn):
                subscribe_fn = fn

            else:
                logger.debug(
                    "[TRANSFORM:CLASS] Skipped %s because it is a function without proper "
                    "definition (please wrap it with proper decorator or name with a prefix).",
                    name,
                )
                continue

        # attribute definition
        else:
            resolve_fn = getattr(cls, f"{resolve_prefix}{name}", None)
            # subscribe_fn = getattr(cls, f"{subscribe_prefix}{name}", None)

        if resolve_fn and subscribe_fn:
            raise TypeError(f"Specified both resolve and subscribe methods for {name}")

        if name in names:
            continue

        resolve_fn, arguments = ctx.hook__prepare_field_resolver(
            name, definition, resolve_fn
        )
        graphql_arguments = to_graphql_arguments(arguments, ctx)

        if ctx.preprocess_resolver_params_values:
            _gql_args = {arg.out_name: arg for arg in graphql_arguments.values()}
            resolve_fn = ctx.hook__prepare_resolver_with_value_converters(
                resolve_fn=resolve_fn,
                arguments=[(*arg, _gql_args[arg[0]]) for arg in arguments],
            )

        field_kw["resolve"] = resolve_fn
        field_kw["args"] = graphql_arguments

        if isinstance(definition.type_, T):
            field_kw.update(definition.type_.graphql_kw)

        yield name, definition, field_kw
        names.add(name)


def _lazy_fields(ctx: TransformContext, lazy_fields):
    ctx = ctx()  # clone context

    def lazy():
        fields = OrderedDict()

        for name, type_, field_kw in lazy_fields:
            if ctx.auto_graphql_id and name == "id" and type_ is str:
                type_ = ID
            gql_t = ctx.transformer.transform(type_)
            field = to_field(gql_t, ctx(**field_kw))
            fields[ctx.hook__convert_name(name, for_type=field)] = field

        return fields

    return lazy


@cache_type
def _transform_class_to_output_type(cls, ctx: TransformContext):
    fields = []

    dc_fields = {}
    if is_dataclass(cls):
        dc_fields = {f.name: f for f in dataclass_fields(cls)}

    for name, definition, field_kw in iterate_class_attributes_for_output_type(
        cls, ctx
    ):
        type_ = definition.type_

        dataclass_field = dc_fields.get(name)
        if dataclass_field:
            field_kw.update(dataclass_field.metadata)

        fields.append((name, type_, field_kw))

    if not fields:
        raise TypeError(f"Please define proper attributes on {cls.__qualname__}")

    if is_interface(cls):
        resolve_type = ctx.get("resolve_type", getattr(cls, "resolve_type", None))

        if resolve_type is None:
            resolve_type = ctx.hook__prepare_default_interface_type_resolver(cls)
        else:
            resolve_type = ctx.hook__prepare_interface_type_resolver(resolve_type, cls)

        return graphql.GraphQLInterfaceType(
            name=get_name(cls),
            fields=_lazy_fields(ctx, fields),
            description=get_doc(cls),
            resolve_type=resolve_type,
        )

    interfaces = lambda: [
        _transform_class_to_output_type(interface_cls, ctx)
        for interface_cls in get_interfaces(cls)
    ]

    return graphql.GraphQLObjectType(
        name=get_name(cls),
        fields=_lazy_fields(ctx, fields),
        description=get_doc(cls),
        interfaces=interfaces,
    )


def _lazy_input_fields(ctx: TransformContext, lazy_fields):
    ctx = ctx()  # clone context

    def lazy():
        fields = OrderedDict()

        for name, type_, field_kw in lazy_fields:
            allow_null = "default_value" in field_kw or field_kw.get(
                "allow_null", MISSING
            )
            gql_t = ctx.transformer.transform(type_, allow_null=allow_null)
            field = to_input_field(gql_t, ctx(**field_kw))
            fields[ctx.hook__convert_name(name, for_type=field)] = field

        return fields

    return lazy


def iterate_class_attributes_for_input_type(cls, ctx: TransformContext):
    attrs = [*get_attr_definitions(cls, only_props=True).values()]

    for definition in attrs:

        # for now skip all fields without annotation/type
        if not (definition.annotation or definition.type_):
            continue

        name = definition.name
        default = definition.value

        kw = {"out_name": name}

        if isinstance(default, enum.Enum):
            default = default.value

        if default is not MISSING:
            kw["default_value"] = default

        yield name, definition, kw


@cache_type
def _transform_class_to_input_type(cls, ctx: TransformContext):
    fields = []

    dc_fields = {}
    if is_dataclass(cls):
        dc_fields = {f.name: f for f in dataclass_fields(cls)}

    for name, definition, field_kw in iterate_class_attributes_for_input_type(cls, ctx):
        type_ = definition.type_

        dataclass_field = dc_fields.get(name)
        if dataclass_field:
            field_kw.update(dataclass_field.metadata)

        fields.append((name, type_, field_kw))

    def out_type(data: dict):
        return cls(**data)

    out_type = ctx.hook__prepare_input_object_type_out_type(cls)

    return graphql.GraphQLInputObjectType(
        name=get_name(cls),
        fields=_lazy_input_fields(ctx, fields),
        description=get_doc(cls),
        out_type=out_type,
    )


def transform(t, ctx: TransformContext):
    if ctx.get("is_input_type"):
        return _transform_class_to_input_type(t, ctx)
    return _transform_class_to_output_type(t, ctx)


def can_transform(t, ctx: TransformContext):
    return is_class(t) and not issubclass(t, enum.Enum)
