import logging
import inspect
from types import LambdaType
import typing

logger = logging.getLogger(__name__)


NoneType = type(None)

MISSING = type(
    "MISSING", (), {"__repr__": lambda o: "<MISSING>", "__bool__": lambda o: False}
)()


def cache_type(func):
    def wrap(obj, ctx):
        cache = ctx["types_cache"]
        if obj in cache:
            return cache[obj]
        ret = cache[obj] = func(obj, ctx)
        return ret

    return wrap


def get_name(obj: typing.Any) -> str:
    """Returns a name which will be presented in graphql schema"""
    return getattr(obj, "__graphql_name__", obj.__name__)


def get_doc(obj: typing.Any) -> typing.Optional[str]:
    """Returns documentation for object"""
    if hasattr(obj, "__graphql_description__"):
        return obj.__graphql_description__
    return inspect.getdoc(obj)


def is_typing_type(t):
    """Checks if it's something from `typing` module"""
    return inspect.getmodule(t) is typing


def is_optional_type(t):
    """Checks if it's a Union[T, NoneType] or Optional[T] (which is the same)"""
    return (
        is_typing_type(t)
        and getattr(t, "__origin__", None) is typing.Union
        and NoneType in getattr(t, "__args__", ())  # type: ignore
    )


def unwrap_optional_type(t):
    if is_optional_type(t):
        union_types = filter_out_none_type(t.__args__)
        if len(union_types) == 1:
            return union_types[0], True
        return typing.Union[tuple(union_types)], True
    return t, False


def filter_out_none_type(types_):
    return [t for t in types_ if t is not NoneType]  # type: ignore


def resolve_thunk(type_):
    if isinstance(type_, LambdaType):
        spec = inspect.getfullargspec(type_)
        if (
            spec.args == []
            and spec.kwonlyargs == []
            and spec.varkw is None
            and spec.varargs is None
        ):
            type_ = type_()
    return type_


class Meta:
    def __init__(self, **kwargs):
        self.meta = kwargs


def meta(**kwargs):
    return Meta(**kwargs)


def is_type_container(t):
    return hasattr(t, "__metadata__") and repr(t).startswith("typing.Annotated[")


def unwrap_type_container(t):
    if is_type_container(t):
        meta = getattr(t, "__metadata__", None)
        if meta and isinstance(meta, tuple):
            meta = meta[0]
        meta = meta if isinstance(meta, Meta) else None
        return t.__origin__, meta
    return t, None


class UnwrappedTypeInfo(typing.NamedTuple):
    type_: typing.Type
    is_nullable: bool
    graphql_kw: dict


def unwrap_type(t: typing.Type) -> UnwrappedTypeInfo:
    is_nullable = False
    graphql_kw = {}

    while True:
        _t = resolve_thunk(t)
        _t, meta = unwrap_type_container(_t)
        if meta:
            graphql_kw.update(meta.meta)
        _t, _is_nullable = unwrap_optional_type(_t)
        is_nullable = is_nullable or _is_nullable

        if _t is t:
            t = _t
            break

        t = _t

    return UnwrappedTypeInfo(t, is_nullable, graphql_kw)
