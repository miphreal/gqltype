from collections import ChainMap
import logging
from typing import Optional

import graphql

from ..context import TransformContext, RootContext
from ..decorators import get_extra_schema_options
from ..utils import resolve_thunk, UnwrappedType, MISSING
from . import (
    transform_graphql_type,
    transform_general_type,
    transform_class,
    transform_enum,
    transform_union,
    transform_type_hint,
    transform_nothing_type,
)
from .type_container import T


logger = logging.getLogger(__name__)


class Transformer:
    def __init__(self, root_context: RootContext):
        self.transformations = [
            transform_nothing_type,
            transform_graphql_type,
            transform_type_hint,
            transform_general_type,
            transform_enum,
            transform_union,
            transform_class,
        ]
        self.ctx = TransformContext(root_context, transformer=self, types_cache={})

    def transform(self, t, *, allow_null=MISSING, **kw):
        logger.debug(
            "[TRANSFORM] Try to transform %r with (allow_null=%s, %s)",
            t,
            allow_null,
            kw,
        )

        t = resolve_thunk(t)

        # Unwrap type container
        if isinstance(t, T):
            allow_null = t.allow_null if t.allow_null is not MISSING else allow_null
            kw = {**t.graphql_kw, **kw}
            return self.transform(t.type_, allow_null=allow_null, **kw)

        ctx = self.ctx(origin_type=t, allow_null=allow_null, **kw)

        extra_options = get_extra_schema_options(t)
        if extra_options:
            ctx = ctx(**extra_options)

        gql_t = self._transform(t, ctx=ctx)
        # The case with unwrapping types
        # (they don't need nullability handling)
        if isinstance(gql_t, UnwrappedType):
            return gql_t.final_type

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

        if (
            allow_null is False
            or allow_null is MISSING
            and self.ctx.explicit_nullability
        ):
            gql_t = graphql.GraphQLNonNull(gql_t)

        return gql_t
