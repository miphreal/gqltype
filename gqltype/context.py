from collections import ChainMap, namedtuple
from functools import partial
import inspect
import logging
import operator
from typing import Tuple

from .utils.resolver import (
    prepare_field_resolver,
    prepare_default_field_resolver,
    prepare_default_union_type_resolver,
    prepare_union_type_resolver,
    prepare_resolver_with_value_converters,
    prepare_resolver_param_value_converter,
    prepare_interface_type_resolver,
    prepare_default_interface_type_resolver,
    prepare_input_object_type_out_type,
)
from .utils.camel_case import to_camel_case

logger = logging.getLogger(__name__)


class Context:
    _context: ChainMap

    def __init__(self, parent_context=None, **kw):
        parent_context = parent_context._context if parent_context else ChainMap()
        self._context = parent_context.new_child(kw)

    def __getattribute__(self, name):
        try:
            ctx = super().__getattribute__("_context")
            return ctx[name]
        except (KeyError, AttributeError):
            return super().__getattribute__(name)

    def __getitem__(self, name):
        try:
            return getattr(self, name)
        except AttributeError as e:
            raise KeyError(name) from e

    def get(self, name, *default):
        if default:
            return self._context.get(name, default[0])
        return self._context.get(name)

    def __setattr__(self, name, val):
        if name == "_context":
            super().__setattr__(name, val)
        else:
            self._context[name] = val

    def __contains__(self, name):
        return name in self._context

    def __call__(self, **kw):
        return self.__class__(self, **kw)

    def update(self, kw):
        self._context.update(kw)


class HooksContext(Context):
    def __getattr__(self, name):
        try:
            return super().__getattribute__(name)
        except AttributeError:
            if name.startswith("hook__"):
                return partial(self.hook_dispatcher, name[6:])
            raise

    def hook_dispatcher(self, hook_name, *args, **kwargs):
        # default behavior - is identity fn
        logger.warning(
            "[CTX] Called unknown hook 'hook__%s' with %s", hook_name, (args, kwargs)
        )
        return args[0] if args else None


class PresetsContext(HooksContext):
    def __init__(self, parent_context=None, **kw):
        options, presets = self._extract_options_and_presets(kw)
        super().__init__(parent_context, **options)
        self._handle_presets(presets)

    def _extract_options_and_presets(self, options: dict) -> Tuple[dict, dict]:
        presets = {k: v for k, v in options.items() if k.startswith("preset__")}
        options = {k: v for k, v in options.items() if k not in presets}
        return options, presets

    def _handle_presets(self, presets: dict):
        for name, val in presets.items():
            fn = getattr(self, name, None)
            if fn is None:
                raise AttributeError(f"There's no preset called {name}.")
            if not callable(fn):
                raise AttributeError(f"Preset {name} is not callable.")
            fn(val)

    def register_preset(self, name: str, fn) -> None:
        self._context["preset__{}".format(name)] = fn

    def __setattr__(self, name, val):
        if name.startswith("preset__"):
            self._handle_presets({name: val})
        else:
            super().__setattr__(name, val)

    def update(self, kw):
        options, presets = self._extract_options_and_presets(kw)
        super().update(options)
        self._handle_presets(presets)


class RootContext(PresetsContext):
    debug: bool = False

    # Default options
    # - require explicit nullability definition with `Optional[T]`
    explicit_nullability: bool = True
    # - function prefixes to disntinquish resolve / mutate and subscribe methods
    resolve_method_name_prefix: str = "resolve_"
    mutate_method_name_prefix: str = "mutate_"
    subscribe_method_name_prefix: str = "subscribe_"

    # Automatically conver output values to corresponding Enum type.
    recognize_enum_output_values: bool = True

    # Automatically convert "id" with type str to GraphQLID
    auto_graphql_id: bool = True

    # Options for resolver
    preprocess_resolver_params: bool = True
    source_param_names = ("obj", "self")
    info_param_names = ("info",)
    extra_special_params = {
        "request": lambda call_ctx: call_ctx.info.context["request"]
    }

    hook__prepare_field_resolver = prepare_field_resolver
    hook__prepare_default_field_resolver = prepare_default_field_resolver

    hook__prepare_union_type_resolver = prepare_union_type_resolver
    hook__prepare_default_union_type_resolver = prepare_default_union_type_resolver

    hook__prepare_interface_type_resolver = prepare_interface_type_resolver
    hook__prepare_default_interface_type_resolver = (
        prepare_default_interface_type_resolver
    )

    hook__prepare_input_object_type_out_type = prepare_input_object_type_out_type

    # Convertion of param values passed to resolver
    preprocess_resolver_params_values: bool = True
    hook__prepare_resolver_param_value_converter = (
        prepare_resolver_param_value_converter
    )
    hook__prepare_resolver_with_value_converters = (
        prepare_resolver_with_value_converters
    )

    # Name convertion (e.g. snake_case to camelCase)
    name_converter = None

    def hook__convert_name(self, name, for_type):
        if self.name_converter:
            return self.name_converter(name)
        return name

    def preset__camel_case(self, val: bool):
        self.name_converter = to_camel_case if val else None


class TransformContext(RootContext):
    transformer: "Transformer"
    types_cache: dict
