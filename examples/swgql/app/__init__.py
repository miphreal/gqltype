from gqltype.contrib.starlette import GraphQLApp
from starlette.applications import Starlette
from starlette.routing import Route

from . import schema_relay, schema_simple


routes = [
    Route("/relay", GraphQLApp(schema=schema_relay.schema)),
    Route("/simple", GraphQLApp(schema=schema_simple.schema)),
]

app = Starlette(routes=routes)
