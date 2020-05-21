import graphql
import gqltype
from gqltype.contrib.graphiql_page import render_graphiql
from starlette.requests import Request
from starlette.responses import Response, HTMLResponse
from starlette.graphql import GraphQLApp as BaseGraphQLApp


class GraphQLApp(BaseGraphQLApp):
    def __init__(self, schema: gqltype.Schema, **kwargs):
        super().__init__(schema=schema.build(), **kwargs)

    async def execute(  # type: ignore
        self, query, variables=None, context=None, operation_name=None
    ):
        return await graphql.graphql(
            self.schema,
            source=query,
            operation_name=operation_name,
            variable_values=variables,
            context_value=context,
        )

    async def handle_graphiql(self, request: Request) -> Response:
        return HTMLResponse(render_graphiql(endpoint=request.url.path))
