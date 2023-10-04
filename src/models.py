import typing as t

class PotionType(t.NamedTuple):
    red: int
    green: int
    blue: int
    dark: int
    
    def to_array(self) -> t.List[int]:
        return [self.red, self.green, self.blue, self.dark]
    
    def from_array(array: t.List[int]) -> t.Self:
        return PotionType(red=array[0], green=array[1], blue=array[2], dark=array[3])

class PotionEntry(t.NamedTuple):
    id: int
    potion_type: PotionType
    quantity: int
    sku: str
    price: int

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

class BarrelDelta(t.NamedTuple):
    red_ml: int
    green_ml: int
    blue_ml: int
    dark_ml: int

    def init_zero() -> t.Self:
        return BarrelStock(red_ml=0, green_ml=0, blue_ml=0, dark_ml=0)

    def add_stock(self, other: t.List[int], qty: int):

        self.red_ml=self.red_ml + (other[0] * qty),
        self.green_ml=self.green_ml + (other[1] * qty),
        self.blue_ml=self.blue_ml + (other[2] * qty),
        self.dark_ml=self.dark_ml + (other[3] * qty),


    def remove_stock(self, other: t.List[int], qty: int) -> t.Self:
        self.red_ml=self.red_ml - (other[0] * qty),
        self.green_ml=self.green_ml - (other[1] * qty),
        self.blue_ml=self.blue_ml - (other[2] * qty),
        self.dark_ml=self.dark_ml - (other[3] * qty),