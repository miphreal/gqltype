import logging

import graphql
import gqltype
from gqltype.contrib.graphiql_page import render_graphiql
from starlette import status
from starlette.background import BackgroundTasks
from starlette.requests import Request
from starlette.responses import Response, HTMLResponse
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from starlette.types import Receive, Scope, Send

logger = logging.getLogger(__name__)


class GraphQLApp:
    def __init__(self, schema: gqltype.Schema, enable_graphiql: bool = True,) -> None:
        self.graphql_schema = schema.build()
        self.enable_graphiql = enable_graphiql

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive=receive)
        response = await self.handle_graphql(request)
        await response(scope, receive, send)

    async def handle_graphql(self, request: Request) -> Response:
        if request.method in ("GET", "HEAD"):
            if "text/html" in request.headers.get("Accept", ""):
                if not self.enable_graphiql:
                    return PlainTextResponse(
                        "Not Found", status_code=status.HTTP_404_NOT_FOUND
                    )
                return await self.handle_graphiql(request)

            data = request.query_params  # type: typing.Mapping[str, typing.Any]

        elif request.method == "POST":
            content_type = request.headers.get("Content-Type", "")

            if "application/json" in content_type:
                data = await request.json()
            elif "application/graphql" in content_type:
                body = await request.body()
                text = body.decode()
                data = {"query": text}
            elif "query" in request.query_params:
                data = request.query_params
            else:
                return PlainTextResponse(
                    "Unsupported Media Type",
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )

        else:
            return PlainTextResponse(
                "Method Not Allowed", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        try:
            query = data["query"]
            variables = data.get("variables")
            operation_name = data.get("operationName")
        except KeyError:
            return PlainTextResponse(
                "No GraphQL query found in the request",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        background = BackgroundTasks()
        context = {"request": request, "background": background}

        result = await self.execute(
            query, variables=variables, context=context, operation_name=operation_name
        )
        error_data = [err.formatted for err in result.errors] if result.errors else None
        response_data = {"data": result.data}
        if error_data:
            response_data["errors"] = error_data
        status_code = (
            status.HTTP_400_BAD_REQUEST if result.errors else status.HTTP_200_OK
        )

        if result.errors:
            for err in result.errors:
                if err.original_error:
                    logger.exception(err.original_error, exc_info=err.original_error)
                else:
                    logger.error(err.message)

        return JSONResponse(
            response_data, status_code=status_code, background=background
        )

    async def execute(  # type: ignore
        self, query, variables=None, context=None, operation_name=None
    ):
        return await graphql.graphql(
            self.graphql_schema,
            source=query,
            operation_name=operation_name,
            variable_values=variables,
            context_value=context,
        )

    async def handle_graphiql(self, request: Request) -> Response:
        return HTMLResponse(render_graphiql(endpoint=request.url.path))
