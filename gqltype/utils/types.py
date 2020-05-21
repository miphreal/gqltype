from dataclasses import dataclass
import logging
import inspect
from types import LambdaType
import typing

logger = logging.getLogger(__name__)


@dataclass
class UnwrappedType:
    """Used to return type without consequent handling"""

    final_type: typing.Any


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


def get_name(obj):
    """Returns a name which will be presented in graphql schema"""
    return getattr(obj, "__graphql_name__", obj.__name__)


def get_doc(obj):
    """Returns documentation for object"""
    if hasattr(obj, "__graphql_description__"):
        return obj.__graphql_description__
    return inspect.getdoc(obj)


def is_typing_type(t):
    """Checks if it's something from `typing` module"""
    return inspect.getmodule(t) is typing


def filter_out_none_type(types_):
    return [t for t in types_ if t is not NoneType]


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
