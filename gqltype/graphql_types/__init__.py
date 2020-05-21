from graphql.type import (
    GraphQLInt as Int,
    GraphQLFloat as Float,
    GraphQLString as String,
    GraphQLBoolean as Bool,
    GraphQLID as ID,
)
from .decimal import GraphQLDecimal as Decimal, PyDecimal
from .date import GraphQLDate as Date, PyDate
from .time import GraphQLTime as Time, PyTime
from .datetime import GraphQLDateTime as DateTime, PyDateTime
from .duration import GraphQLDuration as Duration, PyDuration
from .uuid import GraphQLUUID as UUID, PyUUID

SUPPORTED_TYPES = {}


def register_type(t, gql_t):
    global SUPPORTED_TYPES
    SUPPORTED_TYPES[t] = gql_t


# Base GraphQL type mapping
register_type(bool, Bool)
register_type(int, Int)
register_type(float, Float)
register_type(str, String)

# Extra types
register_type(PyDecimal, Decimal)
register_type(PyUUID, UUID)
register_type(PyDate, Date)
register_type(PyTime, Time)
register_type(PyDateTime, DateTime)
register_type(PyDuration, Duration)
