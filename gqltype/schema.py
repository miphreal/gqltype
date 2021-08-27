import graphql

from .context import RootContext
from .decorators import (
    is_mutation,
    is_query,
    is_subscription,
    mutation,
    query,
    subscription,
)
from .transform import Transformer
from .utils import get_name, is_class


def generate_root_type(objs, name=None):
    bases = []
    attrs = {}
    for f in objs:
        if is_class(f):
            bases.append(f)
        else:
            attrs[get_name(f)] = f

    return type(name or "RootType", tuple(bases), attrs)


class Schema:
    default_options = {"preset__camel_case": True}
    root_context_class = RootContext

    def __init__(
        self, queries=None, mutations=None, subscriptions=None, types=None, **options
    ):
        self._queries = queries or []
        self._mutations = mutations or []
        self._subscriptions = subscriptions or []
        self._types = types or []
        self._root_context = self.root_context_class(
            **{**self.default_options, **options}
        )
        self.transformer = Transformer(self._root_context)

    def register(self, *objs):
        for obj in objs:
            if is_query(obj):
                self._queries.append(obj)
            elif is_mutation(obj):
                self._mutations.append(obj)
            elif is_subscription(obj):
                self._subscriptions.append(obj)
            elif is_class(obj):
                self._types.append(obj)

    def build(self, **options):
        self._root_context.update(options)
        queries = list(map(query, self._queries))
        mutations = list(map(mutation, self._mutations))
        subscriptions = list(map(subscription, self._subscriptions))

        def _transform_top_type(t):
            return graphql.get_nullable_type(self.transformer.transform(t))

        extra_types = list(map(_transform_top_type, self._types))

        return graphql.GraphQLSchema(
            query=_transform_top_type(generate_root_type(queries, name="Query"))
            if queries
            else None,
            mutation=_transform_top_type(generate_root_type(mutations, name="Mutation"))
            if mutations
            else None,
            subscription=_transform_top_type(
                generate_root_type(subscriptions, name="Subscription")
            )
            if subscriptions
            else None,
            types=extra_types,
        )
