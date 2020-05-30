from .decorators import query, resolver, mutation, subscription, schema_options
from .utils import (
    extend_params_definition,
    override_params_definition,
)
from .graphql_types import (
    ID,
    UUID,
    Bool,
    Int,
    Float,
    Decimal,
    String,
    Date,
    Time,
    Duration,
    DateTime,
)
from .schema import Schema
from .transform.type_container import T


ID = T(ID)
UUID = T(UUID)
Bool = T(Bool)
Int = T(Int)
Float = T(Float)
Decimal = T(Decimal)
String = T(String)
Date = T(Date)
Time = T(Time)
DateTime = T(DateTime)
Duration = T(Duration)

from typing import Union as PyUnion

Union = lambda *types, **kw: T(PyUnion[tuple(types)], **kw)
