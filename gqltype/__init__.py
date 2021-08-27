from typing import Annotated, Optional, Union

from .decorators import mutation, query, resolver, schema_options, subscription
from .graphql_types import ID as GraphQLID
from .graphql_types import PyDate, PyDateTime, PyDecimal, PyDuration, PyTime, PyUUID
from .schema import Schema
from .utils import extend_params_definition, meta, override_params_definition


# shortcuts
class ID(str):
    __graphql_type__ = GraphQLID


UUID = PyUUID
Decimal = PyDecimal
Date = PyDate
Time = PyTime
DateTime = PyDateTime
Duration = PyDuration
Bool = bool
Int = int
Float = float
String = str
