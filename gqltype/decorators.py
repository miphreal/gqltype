from typing import Optional


def query(func):
    func.__graphql_query__ = True
    return func


resolver = query


def is_query(func):
    return getattr(func, "__graphql_query__", False)


def mutation(func):
    func.__graphql_mutation__ = True
    return func


def is_mutation(func):
    return getattr(func, "__graphql_mutation__", False)


def subscription(func):
    func.__graphql_subscription__ = True
    return func


def is_subscription(func):
    return getattr(func, "__graphql_subscription__", False)


def schema_options(**kwargs):
    def wrap(obj):
        existing_options = get_extra_schema_options(obj)
        obj.__graphql_schema_options__ = {**existing_options, **kwargs}
        return obj

    return wrap


def get_extra_schema_options(obj):
    return getattr(obj, "__graphql_schema_options__", None) or {}
