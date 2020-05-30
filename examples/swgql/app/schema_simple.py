from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

import gqltype

from .storage import storage


class Gender(Enum):
    NONE = "none"
    UNKNOWN = "unknown"
    NOT_ACCEPTABLE = "n/a"
    MALE = "male"
    FEMALE = "female"
    HERMAPHRODITE = "hermaphrodite"


class Planet:
    id: str
    name: str


class Species:
    id: str
    name: str


class Starship:
    id: str
    name: str


class Film:
    id: str
    title: str


class Person:
    """An individual person or character within the Star Wars universe."""

    id: str
    created: datetime
    edited: datetime

    name: str
    birth_year: int
    eye_color: str
    gender: Gender
    hair_color: str
    height: int
    skin_color: str

    async def resolve_starships(self) -> List[Starship]:
        return await storage.get_objects("starships", self["starships"])

    async def resolve_films(self) -> List[Film]:
        return await storage.get_objects("films", self["films"])

    async def resolve_homeworld(self) -> Planet:
        return await storage.get_object("planets", self["homeworld"])

    async def resolve_species(self) -> List[Species]:
        return await storage.get_objects("species", self["species"])

    def resolve_mass(self) -> Optional[float]:
        try:
            return float(self["mass"])
        except ValueError:
            return None


async def person(person_id: str) -> Person:
    return await storage.get_object("people", person_id)


async def people() -> List[Person]:
    return await storage.get_objects("people")


schema = gqltype.Schema(queries=[person, people])
