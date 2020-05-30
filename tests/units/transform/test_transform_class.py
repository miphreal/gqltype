from tests.utils import *
from gqltype.context import RootContext
from gqltype.transform.transformer import Transformer
from gqltype.transform.transform_class import transform, can_transform
from gqltype.transform.type_container import T

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


import inspect

from gqltype.utils import get_attr_definitions


def test_collect_type_info():
    class T1:
        pass

    class T2:
        pass

    UnionX = Union[T1, T2]
    import abc

    @dataclass
    class Example(abc.ABC):
        """Some doc"""

        attr1: Union[T1, T2]
        attr2: Union[T1, T2]
        # attr2: Optional[UnionX] = None
        # attr3 = UnionX
        # a = b = UnionX
        # c, d = UnionX, UnionX

        def resolve_x(
            self, a: int, c: int = 123, **kwargs
        ) -> T(List[Optional[UnionX]], description="some union"):
            ...

        # def y(self, b):
        #     ...

        # @property
        # def xx(self):
        #     ...

    from pprint import pprint as ppp

    obj_type = transform(Example, transformer.ctx(allow_null=True))


def test_exps1():
    class T:
        attr1 = 123
        attr2 = 'abc'

    obj_type = transform(T, transformer.ctx(allow_null=True))

    import ipdb; ipdb.set_trace()
    pass
