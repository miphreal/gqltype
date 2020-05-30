from __future__ import annotations

from tests.utils import *

from gqltype import Schema, T

schema = Schema()

transform = schema.transformer.transform


def test_transform_bare_class():
    class ExampleType:
        """Type description"""

    assert_that(
        transform(ExampleType, allow_null=True),
        has_properties({"name": "ExampleType", "description": "Type description"}),
    )


@pytest.mark.parametrize("t,gql_t", TYPES.items())
@pytest.mark.parametrize(
    "match",
    [
        lambda t, gql_t: (t, f"{gql_t}!"),
        lambda t, gql_t: (Optional[t], f"{gql_t}"),
        lambda t, gql_t: (List[t], f"[{gql_t}!]!"),
        lambda t, gql_t: (Optional[List[t]], f"[{gql_t}!]"),
        lambda t, gql_t: (Optional[List[Optional[t]]], f"[{gql_t}]"),
    ],
)
def test_transform_python_types(t, gql_t, match):
    T, GQL_T = match(t, gql_t)

    class ExampleType:
        attr: T

    ExampleType.__annotations__["attr"] = T

    assert_that(
        transform(ExampleType, allow_null=True).fields["attr"], is_graphql_field(GQL_T)
    )


def test_transform_enum():
    class SomeType(Enum):
        VAL1 = 1
        VAL2 = 2

    class ExampleType:
        attr: SomeType

    ExampleType.__annotations__["attr"] = SomeType

    assert_that(
        transform(ExampleType, allow_null=True).fields["attr"],
        is_graphql_field("SomeType!"),
    )


def test_transform_enum__full_declaration():
    from graphql.type.definition import GraphQLEnumValue

    class SomeType(Enum):
        VAL1: T(
            int, description="Some description", deprecation_reason="Deprecated."
        ) = 1
        VAL2 = 2

    class ExampleType:
        attr: SomeType

        def resolve_attr(self, info, a: SomeType = SomeType.VAL1):
            return self

        resolve_attr.__annotations__["a"] = SomeType

    ExampleType.__annotations__["attr"] = SomeType

    assert_that(
        transform(ExampleType, allow_null=True).fields["attr"],
        is_graphql_field("SomeType!"),
    )


def test_camel_case_mode__on():
    class ExampleType:
        attr_name: str

        def resolve_attr_name(self, param_name: int):
            return self

    gql_type = transform(ExampleType, allow_null=True, preset__camel_case=True)
    assert "attrName" in gql_type.fields
    assert "paramName" in gql_type.fields["attrName"].args


def test_camel_case_mode__off():
    class ExampleType:
        attr_name: str

        def resolve_attr_name(self, param_name: int):
            return self

    gql_type = transform(ExampleType, allow_null=True, preset__camel_case=False)
    assert "attr_name" in gql_type.fields
    assert "param_name" in gql_type.fields["attr_name"].args
