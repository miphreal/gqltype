from __future__ import annotations
from abc import ABC
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import logging
from typing import List, Literal, Optional, Union, NamedTuple, NewType

import gqltype
from gqltype.contrib.connection import (
    Node,
    Connection,
    prepare_connection_slice,
    with_connection_pagination,
)
from gqltype.contrib.starlette import GraphQLApp

from starlette.applications import Starlette
from starlette.routing import Route
import uvicorn

from .storage import storage


class Gender(Enum):
    NONE = "none"
    UNKNOWN = "unknown"
    NOT_ACCEPTABLE = "n/a"
    MALE = "male"
    FEMALE = "female"
    HERMAPHRODITE = "hermaphrodite"


class Planet(Node):
    name: str


class Species(Node):
    name: str


class Starship(Node):
    name: str


class Film(Node):
    title: str


class Person(Node):
    """An individual person or character within the Star Wars universe."""

    created: datetime
    edited: datetime

    name: str
    birth_year: int
    eye_color: str
    gender: Gender
    hair_color: str
    height: int
    skin_color: str

    films: Connection(Person, Film)
    # species: List[Species]
    # filmConnection: connectionFromUrls('PersonFilms', 'films', FilmType),
    # starshipConnection: connectionFromUrls('PersonStarships', 'starships', StarshipType),
    # vehicleConnection: connectionFromUrls('PersonVehicles', 'vehicles', VehicleType),

    @with_connection_pagination
    async def resolve_starships(self, **kwargs) -> Connection(Person, Starship):
        data = await storage.get_objects("starships", self["starships"])
        return prepare_connection_slice(data, pagination_params=kwargs, limit=25)

    @with_connection_pagination
    async def resolve_films(self, **kwargs) -> Connection(Person, Film):
        data = await storage.get_objects("films", self["films"])
        return prepare_connection_slice(data, pagination_params=kwargs)

    async def resolve_homeworld(self) -> Planet:
        return await storage.get_object("planets", self["homeworld"])

    async def resolve_species(self) -> List[Species]:
        return await storage.get_objects("species", self["species"])

    def resolve_mass(self) -> Optional[float]:
        try:
            return float(self["mass"])
        except ValueError:
            return None


def resolve_node_type(value, info, interface_type):
    id_prefix = value["id"].split(":", 1)[0]
    return {
        "people": Person,
        "planets": Planet,
        "species": Species,
        "starships": Starship,
        "films": Film,
    }.get(id_prefix)


async def node(id: str) -> gqltype.T(Node, resolve_type=resolve_node_type):
    obj_type = id.split(":", 1)[0]
    return await storage.get_object(obj_type, id)


async def person(person_id: str) -> Optional[Person]:
    return await storage.get_object("people", person_id)


@with_connection_pagination
async def people(**params) -> Connection(Person):
    data = await storage.get_objects("people")
    return prepare_connection_slice(data, params)


schema = gqltype.Schema(queries=[node, person, people])
