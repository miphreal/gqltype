"""
Let's implement everything defined in the graphql tutorial.

https://graphql.org/learn/schema/
"""
from dataclasses import dataclass
from enum import Enum
from typing import List

import gqltype


class Episode(Enum):
    """Codename for the episodes"""

    NEWHOPE = "new hope"
    EMPIRE = "empire"
    JEDI = "jedi"


@dataclass
class Character:
    """An individual person within the Star Wars universe"""

    name: str
    appears_in: List[Episode]


class LengthUnit(Enum):
    """Measure of length"""

    METER = "meter"
    INCH = "inch"


@dataclass
class Starship:
    """A single transport craft that has hyperdrive capability"""

    id: str
    name: str
    length: float

    def resolve_length(self, unit: LengthUnit = LengthUnit.METER) -> float:
        if unit == LengthUnit.INCH:
            return self.length / 0.0254
        return self.length


def get_character() -> Character:
    return Character(name="R2D2", appears_in=[Episode.JEDI, Episode.NEWHOPE])


async def get_starship() -> Starship:
    return Starship(id="F1000", name="Millennium Falcon", length=34.75)


def add_character(name: str, appears_in: List[Episode]) -> Character:
    return Character(name=name, appears_in=appears_in)


schema = gqltype.Schema(
    queries=[get_character, get_starship], mutations=[add_character]
)

from graphql.utilities import print_schema

print(print_schema(schema.build()))


if __name__ == "__main__":
    import uvicorn
    from gqltype.contrib.starlette import GraphQLApp
    from starlette.applications import Starlette
    from starlette.routing import Route

    app = Starlette(routes=[Route("/graphql", GraphQLApp(schema=schema))])
    uvicorn.run(app)
