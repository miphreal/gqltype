from __future__ import annotations

import typing

from ..utils import MISSING


class T:
    """A container for a type which can ship some extra meta data, e.g. description"""

    type_: typing.Any
    allow_null: bool
    graphql_kw: dict

    def __init__(self, type_: typing.Any, *, allow_null: bool = MISSING, **graphql_kw):
        self.type_ = type_
        self.allow_null = MISSING if allow_null is None else allow_null
        self.graphql_kw = graphql_kw

    def __repr__(self) -> str:
        return f"<T type_={repr(self.type_)}, allow_null={self.allow_null}, graphql_kw={self.graphql_kw}>"

    def __call__(self, **kw) -> T:
        allow_null = kw.pop("allow_null", self.allow_null)
        type_ = kw.pop("type_", self.type_)
        return T(type_=type_, allow_null=allow_null, **{**self.graphql_kw, **kw})

    def deprecated(self, why: str) -> T:
        return self(deprecation_reason=why)
