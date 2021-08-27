from typing import Annotated
from tests.utils import *
from gqltype.context import RootContext
from gqltype.transform.transformer import Transformer
from gqltype.transform.transform_class import transform, can_transform
from gqltype import meta

transformer = Transformer(RootContext())
ctx = transformer.ctx


class TestGetGraphQLType:
    @pytest.mark.parametrize("t,gql_t", TYPES.items())
    def test_simple_dataclass(self, t, gql_t):
        @dataclass
        class SomeType:
            """Description"""

            attr: t

            def resolve_attr(self, info):
                ...

        obj_type = transform(SomeType, transformer.ctx(allow_null=True))

        assert_that(
            obj_type,
            is_graphql_object_type("SomeType", "Description", attr=f"{gql_t}!"),
        )
