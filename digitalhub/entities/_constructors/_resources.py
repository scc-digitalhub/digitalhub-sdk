# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0
"""
This file contains my divertissement with the European fauna and flora.
"""

from __future__ import annotations

from enum import Enum


class EuropeanMammalName(str, Enum):
    """Representative European wild mammal genera used to build random names."""

    BISON = "bison"
    CAPREOLUS = "capreolus"
    CASTOR = "castor"
    CERVUS = "cervus"
    DAMA = "dama"
    ERINACEUS = "erinaceus"
    LEPUS = "lepus"
    LUPUS = "lupus"
    LYNX = "lynx"
    MARMOTA = "marmota"
    MARTES = "martes"
    MUSTELA = "mustela"
    RUPICAPRA = "rupicapra"
    SCIURUS = "sciurus"
    SUS = "sus"
    TALPA = "talpa"
    URSUS = "ursus"
    VULPES = "vulpes"


class EuropeanAmphibianReptileName(str, Enum):
    """Representative European amphibian and reptile genera used to build random names."""

    BUFO = "bufo"
    HIEROPHIS = "hierophis"
    ICHTHYOSAURA = "ichthyosaura"
    LACERTA = "lacerta"
    NATRIX = "natrix"
    PODARCIS = "podarcis"
    RANA = "rana"
    SALAMANDRA = "salamandra"
    VIPERA = "vipera"


class EuropeanBirdName(str, Enum):
    """Representative European bird genera used to build random names."""

    AEGITHALOS = "aegithalos"
    ALECTORIS = "alectoris"
    ALCEDO = "alcedo"
    ANSER = "anser"
    AQUILA = "aquila"
    ARDEA = "ardea"
    BUBO = "bubo"
    BUTEO = "buteo"
    CORVUS = "corvus"
    DELICHON = "delichon"
    ERITHACUS = "erithacus"
    FALCO = "falco"
    GYPAETUS = "gypaetus"
    MOTACILLA = "motacilla"
    LARUS = "larus"
    COLUMBA = "columba"
    PICUS = "picus"
    PARUS = "parus"
    PASSER = "passer"
    STURNUS = "sturnus"
    STRIX = "strix"
    SYLVIA = "sylvia"
    TETRAO = "tetrao"
    TURDUS = "turdus"


class EuropeanArachnidInsectName(str, Enum):
    """Representative European arachnid and insect genera used to build random names."""

    APIS = "apis"
    ARANEUS = "araneus"
    ARGIOPE = "argiope"
    BOMBUS = "bombus"
    CALOPTERYX = "calopteryx"
    CANTHARIS = "cantharis"
    CARABUS = "carabus"
    COCCINELLA = "coccinella"
    EUSCORPIUS = "euscorpius"
    FORMICA = "formica"
    LIBELLULA = "libellula"
    LYCOSA = "lycosa"
    PAPILIO = "papilio"
    PHALANGIUM = "phalangium"
    PIERIS = "pieris"
    TETTIGONIA = "tettigonia"
    VANESSA = "vanessa"
    VESPA = "vespa"


class LichenFungusName(str, Enum):
    """Representative European lichen and basidiomycete genera used to build random names."""

    AGARICUS = "agaricus"
    AMANITA = "amanita"
    BOLETUS = "boletus"
    CANTHARELLUS = "cantharellus"
    CLADONIA = "cladonia"
    COPRINUS = "coprinus"
    EVERNIA = "evernia"
    HYPOGYMNIA = "hypogymnia"
    LACTARIUS = "lactarius"
    LETHARIA = "letharia"
    PARMELIA = "parmelia"
    PELTIGERA = "peltigera"
    PHYSCIA = "physcia"
    RUSAVSKIA = "rusavskia"
    RUSSULA = "russula"
    UMBILICARIA = "umbilicaria"
    XANTHORIA = "xanthoria"


class EuropeanTreeName(str, Enum):
    """Representative European tree genera used to build random names."""

    ABIES = "abies"
    ACER = "acer"
    ALNUS = "alnus"
    BETULA = "betula"
    FAGUS = "fagus"
    LARIX = "larix"
    PICEA = "picea"
    PINUS = "pinus"
    QUERCUS = "quercus"
    SALIX = "salix"
    TILIA = "tilia"
    ULMUS = "ulmus"


class EuropeanShrubName(str, Enum):
    """Representative European shrub genera used to build random names."""

    CORNUS = "cornus"
    CORYLUS = "corylus"
    CRATAEGUS = "crataegus"
    JUNIPERUS = "juniperus"
    LIGUSTRUM = "ligustrum"
    RIBES = "ribes"
    ROSA = "rosa"
    RUBUS = "rubus"
    SAMBUCUS = "sambucus"
    VIBURNUM = "viburnum"


class EuropeanHerbName(str, Enum):
    """Representative European herbaceous genera used to build random names."""

    ACHILLEA = "achillea"
    ANGELICA = "angelica"
    ACONITUM = "aconitum"
    ANTHRISCUS = "anthriscus"
    CENTAUREA = "centaurea"
    DAUCUS = "daucus"
    DIGITALIS = "digitalis"
    EPILOBIUM = "epilobium"
    GERANIUM = "geranium"
    HYPERICUM = "hypericum"
    LEONTODON = "leontodon"
    LOTUS = "lotus"
    MALVA = "malva"
    ORIGANUM = "origanum"
    PLANTAGO = "plantago"
    RANUNCULUS = "ranunculus"
    SANGUISORBA = "sanguisorba"
    STACHYS = "stachys"
    THYMUS = "thymus"
    VINCETOXUM = "vincetoxum"


class GemAdjective(str, Enum):
    """Gem-inspired adjectives used to build random names."""

    AGATE = "agate"
    ALEXANDRITE = "alexandrite"
    AMBER = "amber"
    AMETHYST = "amethyst"
    AQUAMARINE = "aquamarine"
    BERYL = "beryl"
    CARNELIAN = "carnelian"
    CITRINE = "citrine"
    CORAL = "coral"
    CRYSTAL = "crystal"
    DIAMOND = "diamond"
    EMERALD = "emerald"
    GARNET = "garnet"
    IVORY = "ivory"
    JADE = "jade"
    OPAL = "opal"
    PEARL = "pearl"
    RUBY = "ruby"
    SAPPHIRE = "sapphire"
    TANZANITE = "tanzanite"
    TOPAZ = "topaz"
    TOURMALINE = "tourmaline"
    TURQUOISE = "turquoise"


class AstronomicalAdjective(str, Enum):
    """Astronomical adjectives used to build random names."""

    ASTRAL = "astral"
    COSMIC = "cosmic"
    ELLIPTIC = "elliptic"
    GALACTIC = "galactic"
    LUNAR = "lunar"
    METEORIC = "meteoric"
    MOONLIT = "moonlit"
    NEBULAR = "nebular"
    ORBITAL = "orbital"
    SIDEREAL = "sidereal"
    SOLAR = "solar"
    STELLAR = "stellar"
    UNIVERSAL = "universal"


class ElegantAdjective(str, Enum):
    """Elegant adjectives used to build random names."""

    ARTFUL = "artful"
    AUSTERE = "austere"
    CLASSIC = "classic"
    COMPOSED = "composed"
    DIGNIFIED = "dignified"
    ELEGANT = "elegant"
    ETHEREAL = "ethereal"
    FLOWING = "flowing"
    GRACEFUL = "graceful"
    HARMONIOUS = "harmonious"
    ORNATE = "ornate"
    REFINED = "refined"
    SILKEN = "silken"
    SUBLIME = "sublime"
    SUBTLE = "subtle"
    SWIFT = "swift"
    VELVET = "velvet"


class ColorAdjective(str, Enum):
    """Color adjectives used to build random names."""

    AQUA = "aqua"
    AZURE = "azure"
    BEIGE = "beige"
    BLACK = "black"
    BLUE = "blue"
    BRONZE = "bronze"
    BROWN = "brown"
    CERULEAN = "cerulean"
    CHARCOAL = "charcoal"
    COPPER = "copper"
    CRIMSON = "crimson"
    CYAN = "cyan"
    GOLD = "gold"
    GRAY = "gray"
    GREEN = "green"
    INDIGO = "indigo"
    IVORY = "ivory"
    LAVENDER = "lavender"
    LILAC = "lilac"
    MAGENTA = "magenta"
    MAROON = "maroon"
    NAVY = "navy"
    OLIVE = "olive"
    ORANGE = "orange"
    PEACH = "peach"
    PINK = "pink"
    PLUM = "plum"
    PURPLE = "purple"
    RED = "red"
    ROSE = "rose"
    SAFFRON = "saffron"
    SALMON = "salmon"
    SILVER = "silver"
    SLATE = "slate"
    TEAL = "teal"
    TERRACOTTA = "terracotta"
    VIOLET = "violet"
    WHITE = "white"
    YELLOW = "yellow"


NAME_REGISTRY = (
    EuropeanMammalName,
    EuropeanAmphibianReptileName,
    EuropeanBirdName,
    EuropeanArachnidInsectName,
    LichenFungusName,
    EuropeanTreeName,
    EuropeanShrubName,
    EuropeanHerbName,
)
ADJECTIVE_REGISTRY = (GemAdjective, AstronomicalAdjective, ElegantAdjective, ColorAdjective)
