from collections import OrderedDict, ChainMap, deque
from dataclasses import is_dataclass, fields as dataclass_fields, dataclass
from decimal import Decimal
import logging
import inspect
import enum
from types import LambdaType
import typing
from functools import lru_cache, partial
import abc

import graphql
from graphql.type.definition import GraphQLEnumValue

from .types import MISSING

logger = logging.getLogger(__name__)


def is_class(t):
    return inspect.isclass(t)


def is_interface(t):
    if not is_class(t):
        return False

    if not issubclass(t, abc.ABC):
        # currently we do not support abstract classes defined via metaclass
        return False

    return abc.ABC in t.__bases__


def get_interfaces(cls):
    interfaces = []
    bases = deque(cls.__bases__)

    while bases:
        base_cls = bases.popleft()

        if is_interface(base_cls):
            interfaces.append(base_cls)

        if base_cls is not object:
            bases.extend(base_cls.__bases__)

    return interfaces


def get_annotations(obj):
    """Returns type annotations for function, module or class"""
    return typing.get_type_hints(obj)


@dataclass
class ClassIntrospection:
    cls: typing.Any
    attributes: OrderedDict
    annotations: OrderedDict


def inspect_class(cls):
    return ClassIntrospection(
        cls=cls,
        attributes=OrderedDict(inspect.getmembers(cls)),
        annotations=OrderedDict(get_annotations(cls)),
    )


@dataclass
class AttrDefinition:
    name: str
    annotation: typing.Any
    value: typing.Any
    type_: typing.Any

    def __hash__(self):
        return id(self)


def get_attr_definitions(cls, only_props=False, only_funcs=False):
    """Returns all attributes except magic methods"""
    logger.debug(
        "[INSPECT:%s] Collecting definitions for attributes.", cls.__qualname__
    )
    assert is_class(cls)

    info = inspect_class(cls)
    cls_attributes = info.attributes
    cls_annotations = info.annotations

    all_attr_names = set(cls_attributes).union(set(cls_annotations))

    graphql_fields = getattr(cls, "__graphql_fields__", MISSING)
    assert graphql_fields is MISSING or isinstance(graphql_fields, (tuple, list))

    attrs = OrderedDict()

    for attr in all_attr_names:
        # Skip all magic methods/attributes
        if attr.startswith("__") and attr.endswith("__"):
            continue

        logger.debug("[INSPECT:%s] Checking '%s' field.", cls.__qualname__, attr)

        value = cls_attributes.get(attr, MISSING)
        is_func = inspect.isfunction(value) or inspect.ismethod(value)

        if graphql_fields is not MISSING and attr not in graphql_fields:
            logger.debug(
                "[INSPECT:%s] Skip '%s': should be in __graphql_fields__ list.",
                cls.__qualname__,
                attr,
            )
            continue

        if only_props and is_func:
            continue

        elif only_funcs and not is_func:
            continue

        annotation = cls_annotations.get(attr, MISSING)
        if annotation is MISSING and is_func:
            # getting annotation for returning func value
            annotation = get_annotations(value).get("return", MISSING)

        logger.debug("[INSPECT:%s] Added '%s' field.", cls.__qualname__, attr)
        attrs[attr] = AttrDefinition(
            name=attr, value=value, annotation=annotation, type_=annotation,
        )

    return attrs
