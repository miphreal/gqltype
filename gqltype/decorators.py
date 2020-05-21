def query(func):
    func.__graphql_query__ = True
    return func


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


def graphql_name(name: str):
    def wrap(fn):
        fn.__graphql_name__ = name
        return fn

    return wrap


def graphql_doc(doc: str):
    def wrap(fn):
        fn.__graphql_description__ = doc
        return fn

    return wrap
