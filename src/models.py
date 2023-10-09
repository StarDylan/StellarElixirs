import typing as t
from dataclasses import dataclass
from typing_extensions import SupportsIndex

class PotionType(t.NamedTuple):
    red: int
    green: int
    blue: int
    dark: int
    
    def to_array(self) -> t.List[int]:
        return [self.red, self.green, self.blue, self.dark]
    
    def from_array(array: t.List[int]) -> t.Self:
        return PotionType(red=array[0], green=array[1], blue=array[2], dark=array[3])

    def __mul__(self, __value: int) -> t.Self:
        return PotionType(red=self.red * __value, 
                          green=self.green * __value, 
                          blue=self.blue * __value, 
                          dark=self.dark * __value)

class PotionEntry(t.NamedTuple):
    id: int
    potion_type: PotionType
    quantity: int
    desired_qty: int
    sku: str
    price: int

    def from_db(id, red, green, blue, dark, quantity,desired_qty, sku, price):
        potion_type = PotionType(red, green, blue, dark)
        return PotionEntry(id, potion_type, quantity,desired_qty, sku, price)


class CartEntry(t.NamedTuple):
    potion_id: int
    quantity: int

class BarrelStock(t.NamedTuple):
    red_ml: int
    green_ml: int
    blue_ml: int
    dark_ml: int

    def all_ml(self) -> int:
        return self.red_ml + self.green_ml + self.blue_ml + self.dark_ml

@dataclass
class BarrelDelta():
    red_ml: int
    green_ml: int
    blue_ml: int
    dark_ml: int

    def init_zero() -> t.Self:
        return BarrelDelta(red_ml=0, green_ml=0, blue_ml=0, dark_ml=0)

    def add_stock(self, other: t.List[int], ml_per_barrel: int, qty: int):
        self.red_ml=self.red_ml + (other[0] * qty * ml_per_barrel)
        self.green_ml=self.green_ml + (other[1] * qty * ml_per_barrel)
        self.blue_ml=self.blue_ml + (other[2] * qty * ml_per_barrel)
        self.dark_ml=self.dark_ml + (other[3] * qty * ml_per_barrel)


    def remove_stock(self, other: t.List[int], qty: int):
        self.red_ml=self.red_ml - (other[0] * qty )
        self.green_ml=self.green_ml - (other[1] * qty)
        self.blue_ml=self.blue_ml - (other[2] * qty)
        self.dark_ml=self.dark_ml - (other[3] * qty)
    
    def zero_if_negative(self):
        self.red_ml = max(self.red_ml, 0)
        self.green_ml = max(self.green_ml, 0)
        self.blue_ml = max(self.blue_ml, 0)
        self.dark_ml = max(self.dark_ml, 0)
    
    def to_array(self) -> t.List[int]:
        return [self.red_ml, self.green_ml, self.blue_ml, self.dark_ml]
    