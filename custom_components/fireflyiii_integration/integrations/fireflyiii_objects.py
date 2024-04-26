"""
FireflyIII Integration FireflyIII Agregation Classes

Defines a base to the sensor data, helps adjustments if api changes
"""

from asyncio import gather
from collections import UserDict
from collections.abc import Coroutine, ItemsView, ValuesView
from dataclasses import dataclass, field
from datetime import datetime
from enum import EnumMeta, StrEnum
from typing import ClassVar, Dict, List, Optional, Self, TypeAlias, Union, cast

from .fireflyiii_exceptions import FireflyiiiObjectException

Object: TypeAlias = Union[
    Dict[str, "FireflyiiiObjectBaseId"],
    "FireflyiiiObjectBase",
]


class FireflyiiiObjectTypeMeta(EnumMeta):
    """Meta Class to overide methods in Enum"""

    def __getitem__(cls, name):
        """Return the member matching `name`."""
        if name in cls._value2member_map_:
            return cls._value2member_map_[name]

        return cls._member_map_[name]


class FireflyiiiObjectType(StrEnum, metaclass=FireflyiiiObjectTypeMeta):
    """FireflyIII Object Enum"""

    NONE = ""
    ABOUT = "about"
    ACCOUNTS = "accounts"
    CATEGORIES = "categories"
    BILLS = "bills"
    BUDGETS = "budgets"
    TRANSACTIONS = "transactions"
    PIGGY_BANKS = "piggy_banks"
    SERVER = "server"
    PREFERENCES = "preferences"
    CURRENCIES = "currencies"

    def __repr__(self) -> str:
        """Simple representation"""
        return self.value


@dataclass
class FireflyiiiObjectBase:
    """FireflyIII Object Base"""

    _objtype: ClassVar[FireflyiiiObjectType] = field(default=FireflyiiiObjectType.NONE)

    @property
    def objtype(self) -> FireflyiiiObjectType:
        """Returns Object Type"""
        return self._objtype


@dataclass
class FireflyiiiObjectEmpty(FireflyiiiObjectBase):
    """Empty Container"""


@dataclass
class FireflyiiiObjectBaseId(FireflyiiiObjectBase):
    """FireflyIII Object Base For Items With Id"""

    id: str


class FireflyiiiObjectBaseList(UserDict):
    """FireflyIII Special Object Holder Lists items by type"""

    _coroutines: Optional[List[Coroutine]] = None
    _listtype: Optional[FireflyiiiObjectType] = None

    # pylint: disable=redefined-builtin
    def __init__(
        self,
        dict: Optional[FireflyiiiObjectBase] = None,
        type: Optional[FireflyiiiObjectType] = None,
    ):
        super().__init__(cast(UserDict, dict))
        self._listtype = type

    def values(self):
        "D.values() -> an object providing a view on D's values"
        if self._listtype:
            return ValuesView(self[self._listtype])
        else:
            return ValuesView(self)

    @property
    def list_type(self) -> Optional[FireflyiiiObjectType]:
        """Get List Type"""
        return self._listtype

    def items(self):
        "D.items() -> a set-like object providing a view on D's items"

        if self._listtype:
            return ItemsView(self[self._listtype])
        else:
            return super().items()

    def __iter__(self):
        if self._listtype:
            return iter(self.data[self._listtype])
        else:
            return iter(self.data)

    def __getitem__(self, key: str) -> FireflyiiiObjectBase:
        if self._listtype and key in self.data[self._listtype]:
            return self.data[self._listtype].__getitem__(key)

        return super().__getitem__(key)

    def __getattr__(self, attr: str) -> Union[FireflyiiiObjectBase, Object]:
        """Gets Attr"""

        attr = str(attr)

        if attr in self.data:
            return self.data[attr]

        if (
            attr in FireflyiiiObjectType
        ):  # If it's a valid type we send a empty dic to avoid errors
            return FireflyiiiObjectEmpty()

        raise AttributeError(
            f"'FireflyiiiObjectBaseList' object has no attribute '{attr}'"
        )

    def get(
        self, key, default=None
    ) -> Union[FireflyiiiObjectBase, "FireflyiiiObjectBaseList"]:
        """Get key"""

        key = str(key)

        if self._listtype and key not in FireflyiiiObjectType:
            ret_type = self.data.get(self._listtype)
            if ret_type and key in ret_type:
                ret = ret_type.get(key)
        elif key in FireflyiiiObjectType:
            return getattr(self, key)
        else:
            ret = super().get(key, default)

        if not ret:
            return FireflyiiiObjectBaseList()

        return ret

    def __setitem__(
        self: Self, key: FireflyiiiObjectType, item: FireflyiiiObjectBase
    ) -> None:
        """Sets a new item into dict"""

        # Item must inherit the Base Class
        if not isinstance(item, FireflyiiiObjectBase):
            raise FireflyiiiObjectException(
                "FireflyiiiObjectBaseList can only append FireflyiiiObjectBase objects"
            )

        # The key must be valid in the Object Types
        if key not in FireflyiiiObjectType:
            raise FireflyiiiObjectException(
                f"FireflyiiiObjectBaseList can only append to key with valid type, tried {key}"
            )

        # The item must have a Object Type
        if not item.objtype:
            raise FireflyiiiObjectException(
                "FireflyiiiObjectBaseList can only append FireflyiiiObjectBase with type in class FireflyiiiObjectBase"  # pylint: disable=line-too-long
            )

        # The item must have a valid Object Type
        if not item.objtype in FireflyiiiObjectType:
            raise FireflyiiiObjectException(
                f"FireflyiiiObjectBaseList can only append FireflyiiiObjectBase with valid type, tried FireflyiiiObjectBase with {item.objtype}"  # pylint: disable=line-too-long
            )

        # Ensure that type in objet is typed to Enum
        if not isinstance(item.objtype, FireflyiiiObjectType):
            key = FireflyiiiObjectType[item.objtype]

        # Check if the item is of this container
        if item.objtype != key:
            raise FireflyiiiObjectException(
                f"FireflyiiiObjectBaseList tried to append a {item.objtype} into a {key} container"
            )

        # If it's a item with id, this must be valid
        if isinstance(item, FireflyiiiObjectBaseId) and not item.id:
            raise FireflyiiiObjectException(
                f"FireflyiiiObjectBaseList tried to append invalid id '{item.id}'"
            )

        # Store the item in the key container
        key_str = str(key)

        if key_str not in self.data:
            self.data[key_str] = {}

        if isinstance(item, FireflyiiiObjectBaseId):
            self.data[key_str][item.id] = item
        else:
            self.data[key_str] = item

    def update(self, obj):  # pylint: disable=[arguments-differ]
        """Updates Dict"""
        if not obj:  # If its none ignore
            return
        elif isinstance(obj, FireflyiiiObjectBase):  # If its from base Add it
            self[obj.objtype] = obj
        elif isinstance(
            obj, FireflyiiiObjectBaseList
        ):  # If its a Base List Loop and add it
            for tp, ob in obj.items():
                if obj.list_type:
                    tp = obj.list_type

                if isinstance(
                    ob, FireflyiiiObjectBase
                ):  # If the objetct is from base it's a item without id, add it
                    self[tp] = ob
                else:
                    for _, ob2 in ob.items():
                        self[tp] = ob2
        elif isinstance(obj, list):  # If it's list loop and add it
            for ob in obj:
                self.update(ob)
        elif type(obj).__name__ == "coroutine":  # Store coroutines to await later
            if not self._coroutines:
                self._coroutines = []
            self._coroutines.append(obj)
        else:
            raise FireflyiiiObjectException(
                "FireflyiiiObjectBaseList can only append FireflyiiiObjectBase with type"
            )

    async def gather(self):
        """Gathers Coroutines"""
        if not self._coroutines:
            return

        result = await gather(*[res for res in self._coroutines])
        self.update(result)


@dataclass
class FireflyiiiCurrency(FireflyiiiObjectBaseId):
    """FireflyIII Currencies Data Agregation"""

    _objtype: ClassVar[FireflyiiiObjectType] = FireflyiiiObjectType.CURRENCIES

    name: str
    code: str
    symbol: str = ""
    enabled: bool = True
    default: bool = False
    decimal_places: int = 2

    def __str__(self) -> str:
        return self.code

    @classmethod
    def empty(cls) -> "FireflyiiiCurrency":
        """Returns empty Currency"""
        return FireflyiiiCurrency(id="0", name="", code="")


@dataclass
class FireflyiiiAbout(FireflyiiiObjectBase):
    """FireflyIII About Data Agregation"""

    _objtype: ClassVar[FireflyiiiObjectType] = FireflyiiiObjectType.ABOUT

    os: str = ""
    version: str = ""


@dataclass
class FireflyiiiPreferences(FireflyiiiObjectBase):
    """FireflyIII Preferences Data Agregation"""

    _objtype: ClassVar[FireflyiiiObjectType] = FireflyiiiObjectType.PREFERENCES

    default_currency: Optional[FireflyiiiCurrency] = None
    year_start: str = ""


@dataclass
class FireflyiiiAccount(FireflyiiiObjectBaseId):
    """FireflyIII Account Data Agregation"""

    _objtype: ClassVar[FireflyiiiObjectType] = FireflyiiiObjectType.ACCOUNTS

    name: str
    type: str
    currency: FireflyiiiCurrency
    balance: float = 0
    balance_beginning: float = 0
    iban: str = ""
    transactions: List["FireflyiiiTransaction"] = field(default_factory=list)


@dataclass
class FireflyiiiCategory(FireflyiiiObjectBaseId):
    """FireflyIII Category Data Agregation"""

    _objtype: ClassVar[FireflyiiiObjectType] = FireflyiiiObjectType.CATEGORIES

    name: str
    currency: FireflyiiiCurrency
    balance: Optional[float] = 0
    spent: float = 0
    earned: float = 0
    transactions: List["FireflyiiiTransaction"] = field(default_factory=list)


@dataclass
class FireflyiiiTransaction(FireflyiiiObjectBaseId):
    """FireflyIII Transaction Data Agregation"""

    _objtype: ClassVar[FireflyiiiObjectType] = FireflyiiiObjectType.TRANSACTIONS

    description: str
    value: float
    currency: FireflyiiiCurrency
    date: datetime
    from_account: Optional[FireflyiiiAccount] = None
    to_account: Optional[FireflyiiiAccount] = None
    category: Optional[FireflyiiiCategory] = None


@dataclass
class FireflyiiiBill(FireflyiiiObjectBaseId):
    """FireflyIII Bill Data Agregation"""

    _objtype: ClassVar[FireflyiiiObjectType] = FireflyiiiObjectType.BILLS

    name: str
    value_min: float
    value_max: float
    currency: FireflyiiiCurrency
    paid: List["FireflyiiiBillPayment"] = field(default_factory=list)
    pay: List["FireflyiiiBillPayment"] = field(default_factory=list)

    @property
    def value(self) -> float:
        """Returns bill value"""

        value_min = self.value_min
        value_max = self.value_max

        if not value_min and not value_max:
            return 0
        elif not value_min and value_max:
            value_min = value_max
        elif not value_max and value_min:
            value_max = value_min

        return (value_min + value_max) / 2


@dataclass
class FireflyiiiBillPayment:
    """FireflyIII Bill Payment Data Agregation"""

    date: datetime
    payed: bool = False
    transaction: Optional[FireflyiiiTransaction] = None

    @property
    def value(self) -> float:
        """Reurns Payment Value"""

        if self.transaction:
            return self.transaction.value
        else:
            return 0

    @property
    def currency(self) -> FireflyiiiCurrency:
        """Reurns Payment Currency"""

        if self.transaction:
            return self.transaction.currency
        else:
            return FireflyiiiCurrency.empty()


@dataclass
class FireflyiiiPiggyBank(FireflyiiiObjectBaseId):
    """FireflyIII Preferences Data Agregation"""

    _objtype: ClassVar[FireflyiiiObjectType] = FireflyiiiObjectType.PIGGY_BANKS

    def __post_init__(self):
        if not self.currency and isinstance(self.account, FireflyiiiAccount):
            self.currency = self.account.currency

    name: str
    account: FireflyiiiAccount
    target_amount: float = 0
    percentage: float = 0
    current_amount: float = 0
    left_to_save: float = 0
    currency: Optional[FireflyiiiCurrency] = None
