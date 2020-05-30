## Description

Currently EXPERIMENTAL.

`gqltype` is a GraphQL schema generator from python type annotations.


## Features

- simple definition of GraphQL schema via python type annotations
- builds schema based on `graphql-core>=3.0` library
- asgi friendly


## Installation

Using `pip`
```bash
$ pip install gqltype
```

Using `poetry`
```bash
$ poetry add gqltype
```


## Quick intro

Let's say we want to model the schema mentioned in the beginning of https://graphql.org/learn/schema/ tutorial.

```python
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
    queries=[get_character, get_starship],
    mutations=[add_character]
)

from graphql.utilities import print_schema
print(print_schema(schema.build()))
```

It'll produce the following output
```graphql
type Query {
  getCharacter: Character!
  getStarship: Starship!
}

"""An individual person within the Star Wars universe"""
type Character {
  appearsIn: [Episode!]!
  name: String!
}

"""Codename for the episodes"""
enum Episode {
  NEWHOPE
  EMPIRE
  JEDI
}

"""A single transport craft that has hyperdrive capability"""
type Starship {
  length(unit: LengthUnit! = METER): Float!
  id: ID!
  name: String!
}

"""Measure of length"""
enum LengthUnit {
  METER
  INCH
}

type Mutation {
  addCharacter(name: String!, appearsIn: [Episode!]!): Character!
}
```

In order to run server with this schema we can use Starlette
```python
if __name__ == "__main__":
    import uvicorn
    from gqltype.contrib.starlette import GraphQLApp
    from starlette.applications import Starlette
    from starlette.routing import Route

    app = Starlette(routes=[Route("/graphql", GraphQLApp(schema=schema))])
    uvicorn.run(app)
```

Executing
```graphql
{
  getCharacter {
    name
    appearsIn
  }

  getStarship {
    id
    name
    length(unit: INCH)
  }
}
```
gives
```json
{
  "data": {
    "getCharacter": {
      "name": "R2D2",
      "appearsIn": [
        "JEDI",
        "NEWHOPE"
      ]
    },
    "getStarship": {
      "id": "F1000",
      "name": "Millennium Falcon",
      "length": 1368.1102362204724
    }
  }
}
```

## TODO

- sanity checks
    - warn if class and resolve method specify different types

- generic resolvers for certain types?

- gqltype.F ? -- field definition

- core part and high level part

- business level
    - validation for input values
    - serialization of output values
