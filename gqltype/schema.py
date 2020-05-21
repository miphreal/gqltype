from dataclasses import dataclass
from typing import Optional

import graphql

from .decorators import (
    query,
    mutation,
    subscription,
    is_mutation,
    is_query,
    is_subscription,
)
from .transform import Transformer
from .utils import is_class, get_name
from .context import RootContext


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

        extra_types = [
            self.transformer.transform(t, allow_null=True) for t in self._types
        ]

        return graphql.GraphQLSchema(
            query=self.transformer.transform(
                generate_root_type(queries, name="Query"), allow_null=True
            )
            if queries
            else None,
            mutation=self.transformer.transform(
                generate_root_type(mutations, name="Mutation"), allow_null=True
            )
            if mutations
            else None,
            subscription=self.transformer.transform(
                generate_root_type(subscriptions, name="Subscription"), allow_null=True
            )
            if subscriptions
            else None,
            types=extra_types,
        )
