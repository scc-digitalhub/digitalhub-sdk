# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import random

from pydantic import BaseModel, Field

NAME_REGEX = r"^[a-zA-Z0-9.+-_]+$"
ANIMALS = [
    "aardvark",
    "anaconda",
    "axolotl",
    "baboon",
    "binturong",
    "blackbuck",
    "capybara",
    "caracal",
    "cassowary",
    "civet",
    "coati",
    "crocodile",
    "dromedary",
    "echidna",
    "fennec",
    "flamingo",
    "gerenuk",
    "gibbon",
    "gorilla",
    "ibis",
    "impala",
    "lemur",
    "mandrill",
    "manatee",
    "narwhal",
    "okapi",
    "orangutan",
    "pangolin",
    "quokka",
    "rhea",
    "saiga",
    "sloth",
    "tapir",
    "tarantula",
    "toucan",
    "vaquita",
    "walrus",
    "wombat",
    "yak",
    "zebra",
]

ADJECTIVES = [
    "amethyst",
    "airy",
    "alabaster",
    "amber",
    "ample",
    "antique",
    "aquamarine",
    "aristocratic",
    "artful",
    "astral",
    "austere",
    "balanced",
    "balletic",
    "beryl",
    "bespoke",
    "blended",
    "blissful",
    "blooming",
    "brushed",
    "buoyant",
    "calm",
    "cerulean",
    "chic",
    "citrine",
    "classic",
    "clean",
    "cloudless",
    "coastal",
    "composed",
    "coral",
    "cosmic",
    "crisp",
    "curated",
    "delicate",
    "diamond",
    "dignified",
    "dusky",
    "elegant",
    "elliptic",
    "embellished",
    "emerald",
    "ethereal",
    "faint",
    "finely",
    "finespun",
    "flowing",
    "frosted",
    "garnet",
    "gentle",
    "glossy",
    "golden",
    "graceful",
    "harmonious",
    "heraldic",
    "hushed",
    "immaculate",
    "ivory",
    "jade",
    "laced",
    "languid",
    "lavish",
    "light",
    "lilting",
    "luminous",
    "lunar",
    "lustrous",
    "majestic",
    "marbled",
    "mellow",
    "meteoric",
    "minimal",
    "minted",
    "misty",
    "modest",
    "moonlit",
    "muted",
    "nebular",
    "nestled",
    "opal",
    "orbital",
    "ornate",
    "peaceful",
    "pearl",
    "pearled",
    "polished",
    "precious",
    "pure",
    "refined",
    "regal",
    "rosy",
    "ruby",
    "sapphire",
    "silken",
    "silvery",
    "solar",
    "soothing",
    "sparkling",
    "spun",
    "stately",
    "stellar",
    "suave",
    "sublime",
    "subtle",
    "supple",
    "swift",
    "tender",
    "timeless",
    "topaz",
    "universal",
    "velvet",
    "velvety",
    "verdant",
    "warm",
    "whispering",
    "wide",
    "wisped",
    "zen",
    "zenith",
]


class NameValidator(BaseModel):
    """
    Validate name format.
    """

    name: str = Field(min_length=1, max_length=256, pattern=NAME_REGEX)


def build_name(name: str) -> str:
    """
    Build name.

    Parameters
    ----------
    name : str
        The name.

    Returns
    -------
    str
        The name.
    """
    NameValidator(name=name)
    return name


def random_name() -> str:
    """
    Generate a random name.

    Returns
    -------
    str
        The random name.
    """
    adjective = random.choice(ADJECTIVES)
    animal = random.choice(ANIMALS)
    return f"{adjective}-{animal}"
