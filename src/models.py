import typing as t
from dataclasses import dataclass
from pydantic import BaseModel

class PotionType(t.NamedTuple):
    red: int
    green: int
    blue: int
    dark: int
    
    def to_array(self) -> t.List[int]:
        return [self.red, self.green, self.blue, self.dark]
    def from_array(array: t.List[int]) -> t.Self:
        return PotionType(red=array[0], green=array[1], blue=array[2], dark=array[3])

    def __mul__(self, __value: int):
        return PotionType(red=self.red * __value, 
                          green=self.green * __value, 
                          blue=self.blue * __value, 
                          dark=self.dark * __value)

class PotionEntry(t.NamedTuple):
    potion_type: PotionType
    quantity: int
    sku: str
    price: int
    desired_qty: int

    def from_db(red, green, blue, dark, quantity, sku, price, desired_qty):
        potion_type = PotionType(red, green, blue, dark)
        return PotionEntry(potion_type, quantity, sku, price, desired_qty)

    def with_quantity(self, quantity: int) -> t.Self:
        return PotionEntry(self.potion_type, quantity, self.sku, self.price, self.desired_qty)

    def with_desired_qty(self, desired_qty: int) -> t.Self:
        return PotionEntry(self.potion_type, self.quantity, self.sku, self.price, desired_qty)
    
class CartEntry(t.NamedTuple):
    id: int
    potion_id: int
    quantity: int
    price: int


@dataclass
class BarrelDelta():
    red_ml: int
    green_ml: int
    blue_ml: int
    dark_ml: int

    def init_zero():
        return BarrelDelta(red_ml=0, green_ml=0, blue_ml=0, dark_ml=0)

    def add_stock(self, other: t.List[int], ml_per_barrel: int, qty: int):
        self.red_ml=self.red_ml + (other[0] * qty * ml_per_barrel)
        self.green_ml=self.green_ml + (other[1] * qty * ml_per_barrel)
        self.blue_ml=self.blue_ml + (other[2] * qty * ml_per_barrel)
        self.dark_ml=self.dark_ml + (other[3] * qty * ml_per_barrel)


    def remove_stock(self, type: PotionType, qty: int):
        self.red_ml=self.red_ml - (type.red * qty )
        self.green_ml=self.green_ml - (type.green * qty)
        self.blue_ml=self.blue_ml - (type.blue * qty)
        self.dark_ml=self.dark_ml - (type.dark * qty)
    
    def zero_if_negative(self):
        self.red_ml = max(self.red_ml, 0)
        self.green_ml = max(self.green_ml, 0)
        self.blue_ml = max(self.blue_ml, 0)
        self.dark_ml = max(self.dark_ml, 0)
    
    def has_at_least(self, other: t.Self):
        return self.red_ml >= other.red_ml and self.green_ml >= other.green_ml and self.blue_ml >= other.blue_ml and self.dark_ml >= other.dark_ml
    
    def to_array(self) -> t.List[int]:
        return [self.red_ml, self.green_ml, self.blue_ml, self.dark_ml]
    def from_array(barrel_qty: list[int]) -> t.Self:
        return BarrelDelta(red_ml=barrel_qty[0], green_ml=barrel_qty[1], blue_ml=barrel_qty[2], dark_ml=barrel_qty[3])

class BarrelStock(t.NamedTuple):
    red_ml: int
    green_ml: int
    blue_ml: int
    dark_ml: int

    def all_ml(self) -> int:
        return self.red_ml + self.green_ml + self.blue_ml + self.dark_ml
    
    def to_array(self) -> t.List[int]:
        return [self.red_ml, self.green_ml, self.blue_ml, self.dark_ml]
    def to_delta(self) -> BarrelDelta:
        return BarrelDelta(red_ml=self.red_ml, green_ml=self.green_ml, blue_ml=self.blue_ml, dark_ml=self.dark_ml)


class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

BARREL_TYPES = [[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]]