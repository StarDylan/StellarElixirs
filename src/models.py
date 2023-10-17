import typing as t
from dataclasses import dataclass

class PotionType(t.NamedTuple):
    id: int
    red: int
    green: int
    blue: int
    dark: int
    
    def to_array(self) -> t.List[int]:
        return [self.red, self.green, self.blue, self.dark]

    def __mul__(self, __value: int):
        return PotionType(red=self.red * __value, 
                          green=self.green * __value, 
                          blue=self.blue * __value, 
                          dark=self.dark * __value)

class PotionEntry(t.NamedTuple):
    potion_type: PotionType
    quantity: int
    sku: str

    def from_db(id, red, green, blue, dark, quantity, sku):
        potion_type = PotionType(id, red, green, blue, dark)
        return PotionEntry(potion_type, quantity, sku)


class CartEntry(t.NamedTuple):
    id: int
    potion_id: int
    quantity: int

class BarrelStock(t.NamedTuple):
    red_ml: int
    green_ml: int
    blue_ml: int
    dark_ml: int

    def all_ml(self) -> int:
        return self.red_ml + self.green_ml + self.blue_ml + self.dark_ml
    
    def to_array(self) -> t.List[int]:
        return [self.red_ml, self.green_ml, self.blue_ml, self.dark_ml]

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
    