from aiohttp import web
import graphql
import logging

from gqltype.schema import Schema
from gqltype.contrib.graphiql_page import render_graphiql


logger = logging.getLogger(__name__)


async def graphql_view(request):
    query = operation_name = variables = None

    if "text/html" in request.headers["accept"]:
        return web.Response(text=render_graphiql(), content_type="text/html")

    if request.content_type == "application/json":
        _data = await request.json()
        query = _data.get("query")
        operation_name = _data.get("operationName")
        variables = _data.get("variables")

    elif request.content_type == "application/graphql":
        query = await request.text()

    result = await graphql.graphql(
        request.app["graphql_schema"],
        source=query,
        operation_name=operation_name,
        variable_values=variables,
        context_value={"request": request},
    )

    if result.errors:
        data = {"errors": [e.formatted for e in result.errors]}
        for err in result.errors:
            if err.original_error:
                logger.exception(err.original_error, exc_info=err.original_error)
    else:
        data = {"data": result.data}

    return web.json_response(data=data)


def init_graphql(app, schema: Schema, url: str = '/graphql'):
    if not "graphql_schema" in app:
        app["graphql_schema"] = schema.build()

    app.router.add_route("get", url, graphql_view)
    app.router.add_route("post", url, graphql_view)
