"""
Implementaion of Relay's connections approach.

https://relay.dev/graphql/connections.htm
"""
from abc import ABC
from dataclasses import dataclass
from functools import wraps
from typing import NamedTuple, List, Optional

import gqltype
import gqltype.utils
from gqltype.utils.func import extend_params_definition, ParamsDefinition


@dataclass
class Node(ABC):
    """An object with an ID"""

    id: gqltype.ID(description="The id of the object", allow_null=True)


def _connection_type(
    parent_t=None,
    t=None,
    extend_page_info=None,
    extend_connection=None,
    extend_edge=None,
    prefix=None,
):
    """Generates GraphQL Connection type"""
    if t is None and parent_t is not None:
        t, parent_t = parent_t, t
    if not prefix and t:
        type_name = gqltype.utils.get_name(t)
        parent_type_name = gqltype.utils.get_name(parent_t) if parent_t else ""
        prefix = parent_type_name + type_name

    return NamedTuple(
        f"{prefix}Connection",
        edges=List[
            NamedTuple(f"{prefix}Edge", node=t, cursor=str, **(extend_edge or {}))
        ],
        page_info=NamedTuple(
            f"{prefix}PageInfo",
            has_previous_page=bool,
            has_next_page=bool,
            start_cursor=Optional[str],
            end_cursor=Optional[str],
            **(extend_page_info or {}),
        ),
        **(extend_connection or {}),
    )


Connection = _connection_type


def prepare_connection_slice(
    data, pagination_params: dict, limit: Optional[int] = None
):
    after = pagination_params.get("after")
    first = pagination_params.get("first")

    before = pagination_params.get("before")
    last = pagination_params.get("last")

    # It's allowed to have either after/first or before/last params, not both
    if after or first is not None:
        start = int(after) if after else 0
        end = start + (first or limit)
    elif before or last is not None:
        end = int(before) if before else len(data)
        start = end - (last or limit)
        start = 0 if start < 0 else start
    else:
        start, end = 0, limit

    data = list(data[start : end + 1 if end is not None else None])
    has_prev = start > 0
    has_next = len(data) > end - start if end is not None else False
    if has_next:
        data.pop()

    edges = [{"node": node, "cursor": str(start + i)} for i, node in enumerate(data)]

    start_cursor = edges[0]["cursor"] if edges else None
    end_cursor = edges[-1]["cursor"] if edges else None

    return {
        "edges": edges,
        "page_info": {
            "has_previous_page": has_prev,
            "has_next_page": has_next,
            "start_cursor": start_cursor,
            "end_cursor": end_cursor,
        },
    }


def with_connection_pagination(fn):
    extend_params_definition(
        fn,
        ParamsDefinition(
            args=["first", "after", "last", "before"],
            defaults={"first": None, "after": None, "last": None, "before": None},
            type_hints={
                "first": Optional[int],
                "after": Optional[str],
                "last": Optional[int],
                "before": Optional[str],
            },
        ),
    )

    return fn
