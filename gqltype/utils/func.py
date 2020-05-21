import inspect

from typing import get_type_hints

PARAMS_DEFINITION_ATTR = "__graphql_params_definition__"


def preserve_params_definition(fn):
    def wrap(wrapper):
        setattr(wrapper, PARAMS_DEFINITION_ATTR, inspect_function(fn))
        return wrapper

    return wrap


def extend_params_definition(fn):
    def wrap(wrapper):
        fn_args, fn_defaults, fn_type_hints = inspect_function(fn)
        wfn_args, wfn_defaults, wfn_type_hints = inspect_function(wrapper)

        args = [*fn_args, *[_arg for _arg in wfn_args if _arg not in fn_args]]
        defautls = {**fn_defaults, **wfn_defaults}
        type_hints = {**fn_type_hints, **wfn_type_hints}

        setattr(wrapper, PARAMS_DEFINITION_ATTR, (args, defautls, type_hints))
        return wrapper

    return wrap


def override_params_definition(fn):
    def wrap(wrapper):
        setattr(wrapper, PARAMS_DEFINITION_ATTR, inspect_function(wrapper))
        return wrapper

    return wrap


def inspect_function(fn):
    if hasattr(fn, PARAMS_DEFINITION_ATTR):
        return getattr(fn, PARAMS_DEFINITION_ATTR)

    argspec = inspect.getfullargspec(fn)
    arguments = argspec.args + argspec.kwonlyargs
    defaults = dict(argspec.kwonlydefaults or {})
    if argspec.defaults:
        defaults.update(
            dict(zip(argspec.args[-len(argspec.defaults) :], argspec.defaults))
        )

    return (arguments, defaults, get_type_hints(fn))
