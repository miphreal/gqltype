from abc import ABC
from datetime import date, datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Union, TypeVar, NewType


import gqltype as gql


class State(Enum):
    """Available states"""

    ACTIVE = "active"
    INACTIVE = "inactive"


@dataclass
class BaseAttrs(ABC):
    """Interface type"""

    id: int
    created_at: str
    updated_at: str
    state: State

    def resolve_verbose_state(self, context) -> str:
        return str(self.state)


class TypeA(BaseAttrs):
    """Some A type"""

    name: str
    tags: List[str]


class TypeB(BaseAttrs):
    """Some B type"""

    count: int
    has_tags: bool
    tags: List[str]


AnyObj = Union[TypeA, TypeB]


@gql.query
def query_objects(state: State) -> List[AnyObj]:
    return ...


@gql.mutation
def change_something(param: str, context) -> BaseAttrs:
    return ...


@gql.subscription
async def watch_for_some_change(request) -> AnyObj:
    yield ...


class MySchema(gql.Schema):
    def register(self, known):
        return [query_objects, change_something, watch_for_some_change]


schema = MySchema().build()
