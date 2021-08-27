import logging

import graphql

from ..context import TransformContext, RootContext
from ..decorators import get_extra_schema_options
from ..utils import resolve_thunk, unwrap_optional_type, unwrap_type_container
from . import (
    transform_graphql_type,
    transform_general_type,
    transform_class,
    transform_enum,
    transform_union,
    transform_type_hint,
)


logger = logging.getLogger(__name__)


class Transformer:
    def __init__(self, root_context: RootContext):
        self.transformations = [
            transform_graphql_type,
            transform_type_hint,
            transform_general_type,
            transform_enum,
            transform_union,
            transform_class,
        ]
        self.ctx = TransformContext(root_context, transformer=self, types_cache={})

    def transform(self, t, **context_options):
        logger.debug("[TRANSFORM] Try to transform %r", t)

        ctx = self.ctx(**context_options)

        allow_null = False

        while True:
            _t = resolve_thunk(t)
            _t, _ = unwrap_type_container(_t)
            _t, _allow_null = unwrap_optional_type(_t)
            allow_null = allow_null or _allow_null

            if _t is t:
                t = _t
                break

            t = _t

        extra_options = get_extra_schema_options(t)
        if extra_options:
            ctx = ctx(**extra_options)

        gql_t = self._transform(t, ctx=ctx)

        # Catch if `t` was not converted
        if not graphql.is_type(gql_t):
            raise TypeError(f"Type {t!r} cannot be converted to graphql type.")

        return self._handle_nullability(gql_t, allow_null)

    def _transform(self, t, ctx):
        """Converts regular type to graphql type"""
        for transformation in self.transformations:
            if transformation.can_transform(t, ctx=ctx):
                logger.debug(
                    "[TRANSFOMR] Applying %s to %s",
                    transformation.transform.__module__,
                    t,
                )

                gql_t = transformation.transform(t, ctx=ctx)
                if gql_t is not None:
                    logger.debug("[TRANSFORM] %r transformed to %r", t, gql_t)
                    return gql_t

        return t

    def _handle_nullability(self, gql_t, allow_null):
        gql_t = graphql.get_nullable_type(gql_t)

        if not allow_null:
            gql_t = graphql.GraphQLNonNull(gql_t)

        return gql_t
