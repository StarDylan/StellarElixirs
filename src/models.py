import typing as t

class PotionType(t.NamedTuple):
    red: int
    green: int
    blue: int
    dark: int

class PotionEntry(t.NamedTuple):
    potion_type: PotionType
    quantity: int

class BarrelStock(t.NamedTuple):
    red_ml: int
    green_ml: int
    blue_ml: int
    dark_ml: int
