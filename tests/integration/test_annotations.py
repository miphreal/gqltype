from dataclasses import dataclass, fields

from typing import get_type_hints, Annotated

from gqltype.utils.cls import get_annotations


class SomeTypeGlobalNS:
    attr: int


def test_can_get_class_annotations__non_global_scope():
    class SomeTypeLocalNS:
        attr: int

    @dataclass
    class ExampleType:
        attr: str
        attr2: bool
        attr3: SomeTypeLocalNS

    # If any type is defined in local scope, it should be injected to
    # the `__annotations__` explicitly.
    ExampleType.__annotations__["attr3"] = SomeTypeLocalNS

    annotations = get_annotations(ExampleType)

    assert annotations == {"attr": str, "attr2": bool, "attr3": SomeTypeLocalNS}


def test_can_get_class_annotations__all_types_in_global_ns():
    @dataclass
    class ExampleType:
        attr: str
        attr2: bool
        attr3: SomeTypeGlobalNS

    annotations = get_annotations(ExampleType)

    assert annotations == {"attr": str, "attr2": bool, "attr3": SomeTypeGlobalNS}


def test_can_get_fn_annotations__non_global_scope():
    class SomeTypeLocalNS:
        attr: int

    def fn(attr: bool, attr1: SomeTypeLocalNS) -> SomeTypeLocalNS:
        ...

    # If any type is defined in local scope, it should be injected to
    # the `__annotations__` explicitly.
    fn.__annotations__["attr1"] = SomeTypeLocalNS
    fn.__annotations__["return"] = SomeTypeLocalNS

    annotations = get_annotations(fn)

    assert annotations == {
        "attr": bool,
        "attr1": SomeTypeLocalNS,
        "return": SomeTypeLocalNS,
    }


def test_can_get_fn_annotations__all_types_in_global_ns():
    def fn(attr: bool, attr1: SomeTypeGlobalNS) -> SomeTypeGlobalNS:
        ...

    annotations = get_annotations(fn)

    assert annotations == {
        "attr": bool,
        "attr1": SomeTypeGlobalNS,
        "return": SomeTypeGlobalNS,
    }


def test_annotated_type():
    def fn(attr: Annotated[str, {}]) -> Annotated[int, {}]:
        ...

    annotations = get_annotations(fn)

    assert annotations == {
        "attr": Annotated[str, {}],
        "return": Annotated[int, {}],
    }
