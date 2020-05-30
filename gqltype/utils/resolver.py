from collections import namedtuple
from functools import partial, wraps
import inspect
import enum

from . import MISSING
from .func import inspect_function

_ResolveCallContext = namedtuple("ResolveCallContext", ["source", "info", "params"])


def _wrap_resolver(fn, ctx):
    spec = inspect.getfullargspec(fn)
    args = frozenset(spec.args + spec.kwonlyargs)

    source_args = frozenset(name for name in ctx.source_param_names if name in args)
    info_args = frozenset(name for name in ctx.info_param_names if name in args)
    extra_args = {
        name: fn for name, fn in ctx.extra_special_params.items() if name in args
    }

    @wraps(fn)
    def wrap(source, info, **kwargs):
        if extra_args:
            call_ctx = _ResolveCallContext(source, info, kwargs)
            kwargs.update({arg: fn(call_ctx) for arg, fn in extra_args.items()})

        for arg in source_args:
            kwargs[arg] = source

        for arg in info_args:
            kwargs[arg] = info

        return fn(**kwargs)

    return wrap


def prepare_default_field_resolver(ctx, name, definition):
    """Generate a field resolver when no resolvers were specified."""
    if ctx.name_converter:
        # if there's a name converter, try to access attributes via original names
        def default_field_resolver(source, info, **args):
            if isinstance(source, dict):
                return source.get(name, None)
            return getattr(source, name, None)

    else:
        default_field_resolver = None

    return default_field_resolver, ()


def prepare_field_resolver(ctx, name, definition, fn):
    """
    Prepare a "resolve" function and information about its params.

    It should return the "resolve" function itself and a list of
    params accepted by corresponding field with information about parameter's type
    and default value (i.e. the function should return two values: function and a list
    of tuples where each tuple is (param_name, param_type, param_default_value)).

    Note. if `ctx.preprocess_resolver_params` is True, it'll take care of absence
    of special attributes (e.g. `source`, `info`, `self`, etc). Otherwise all "resolve"
    functions must have `source` and `info` as their first parameters.
    """
    if fn is None:
        return ctx.hook__prepare_default_field_resolver(name, definition)

    arguments, defaults, annotations = inspect_function(fn)

    if ctx.preprocess_resolver_params:
        fn = _wrap_resolver(fn, ctx)

        special_args = (
            tuple(ctx.source_param_names)
            + tuple(ctx.info_param_names)
            + tuple(ctx.extra_special_params)
        )
        # Eliminate special attributes from the list of accepted params
        arguments = [p for p in arguments if p not in special_args]

    else:
        # Consider first two args as `source` and `info`
        arguments = arguments[2:]

    fn_arguments = [
        (arg_name, annotations.get(arg_name, MISSING), defaults.get(arg_name, MISSING))
        for arg_name in arguments
    ]

    return fn, fn_arguments


def prepare_resolver_param_value_converter(
    ctx, resolve_fn, arg_name, arg_default, arg_python_type, arg_gql_type
):
    return None


def prepare_resolver_with_value_converters(ctx, resolve_fn, arguments):
    value_converters = {}

    for arg_name, arg_type, arg_default, arg_gql_type in arguments:
        if arg_type:
            value_converter = ctx.hook__prepare_resolver_param_value_converter(
                resolve_fn=resolve_fn,
                arg_name=arg_name,
                arg_default=arg_default,
                arg_python_type=arg_type,
                arg_gql_type=arg_gql_type,
            )
            if value_converter:
                value_converters[arg_name] = value_converter

    if value_converters:
        _resolve_fn = resolve_fn

        @wraps(resolve_fn)
        def wrapped(*args, **kwargs):
            for arg, converter in value_converters.items():
                if arg in kwargs:
                    kwargs[arg] = converter(kwargs[arg])
            return _resolve_fn(*args, **kwargs)

        return wrapped

    return resolve_fn


def prepare_union_type_resolver(ctx, type_resolver, name, types_map):
    @wraps(type_resolver)
    def wrap(value, info, union_type):
        ret_type = type_resolver(value, info, union_type)
        if ret_type in types_map:
            return types_map[ret_type]
        return ret_type

    return wrap


def prepare_default_union_type_resolver(ctx, name, types_map):
    def type_resolver(value, info, union_type):
        val_type = type(value)
        return types_map[val_type]

    return type_resolver


def _get_interface_implementations_types_map(ctx, cls):
    interface_implementations = []

    implementations = list(cls.__subclasses__())
    while implementations:
        _cls = implementations.pop()
        _cls_impls = _cls.__subclasses__()
        if not _cls_impls:
            interface_implementations.append(_cls)
        else:
            implementations.extend(_cls_impls)

    return {
        impl: ctx.transformer.transform(impl, allow_null=True)
        for impl in interface_implementations
    }


def prepare_interface_type_resolver(ctx, type_resolver, cls):
    types_map = _get_interface_implementations_types_map(ctx, cls)

    @wraps(type_resolver)
    def wrap(value, info, union_type):
        ret_type = type_resolver(value, info, union_type)
        if ret_type in types_map:
            return types_map[ret_type]
        return ret_type

    return wrap


def prepare_default_interface_type_resolver(ctx, cls):
    types_map = _get_interface_implementations_types_map(ctx, cls)

    def type_resolver(value, info, interface_type):
        val_type = type(value)
        return types_map[val_type]

    return type_resolver


def prepare_input_object_type_out_type(ctx, cls):
    def prepare_input_object(data: dict) -> cls:
        return cls(**data)

    return prepare_input_object
