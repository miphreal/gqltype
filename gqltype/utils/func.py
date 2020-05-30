import inspect
from typing import Any, Dict, List, NamedTuple, get_type_hints

PARAMS_DEFINITION_ATTR = "__graphql_params_definition__"
OVERRIDE_OP = "override"
PRESERVE_OP = "preserve"
EXTEND_OP = "extend"


class ParamsDefinition(NamedTuple):
    args: List[str]
    defaults: Dict[str, Any]
    type_hints: Dict[str, Any]


def _append_params_operation(fn, op, value):
    params_ops = getattr(fn, PARAMS_DEFINITION_ATTR, None)
    if params_ops is None:
        params_ops = [[PRESERVE_OP, fn]]
    params_ops.append([op, value])
    setattr(fn, PARAMS_DEFINITION_ATTR, params_ops)


def inspect_function(fn, with_redefined_params: bool = True) -> ParamsDefinition:
    if with_redefined_params and hasattr(fn, PARAMS_DEFINITION_ATTR):
        return _calc_prams_definition(fn)

    argspec = inspect.getfullargspec(fn)
    arguments = argspec.args + argspec.kwonlyargs
    defaults = dict(argspec.kwonlydefaults or {})
    if argspec.defaults:
        defaults.update(
            dict(zip(argspec.args[-len(argspec.defaults) :], argspec.defaults))
        )

    return (arguments, defaults, get_type_hints(fn))


def merge_params_definitions(
    def1: ParamsDefinition, def2: ParamsDefinition
) -> ParamsDefinition:
    args1, defaults1, hints1 = def1
    args2, defaults2, hints2 = def2

    args = [*args1, *[_arg for _arg in args2 if _arg not in args1]]
    defautls = {**defaults1, **defaults2}
    type_hints = {**hints1, **hints2}

    return args, defautls, type_hints


def _calc_prams_definition(fn):
    params_ops = getattr(fn, PARAMS_DEFINITION_ATTR, None) or []

    defs = ParamsDefinition((), {}, {})
    for op, val in params_ops:
        if op == PRESERVE_OP:
            defs = merge_params_definitions(
                defs, inspect_function(val, with_redefined_params=False)
            )
        elif op == OVERRIDE_OP:
            defs = val
        elif op == EXTEND_OP:
            defs = merge_params_definitions(defs, val)

    return defs


def override_params_definition(fn, defs):
    _append_params_operation(fn, OVERRIDE_OP, defs)


def extend_params_definition(fn, defs):
    _append_params_operation(fn, EXTEND_OP, defs)
