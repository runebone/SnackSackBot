import types

from uuid import UUID
from datetime import datetime

# Helpers
class _Table:
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name


class _Field:
    def __init__(self, table: _Table, name: str, type_: type):
        self._table = table
        self.name = name
        self.type = type_

    def __str__(self):
        return self.name


class _BaseRecord:
    def __str__(self):
        return "\n".join(
            [
                f"{i}: {getattr(self, i)}"
                for i in self.__dir__()
                if not i.startswith("__")
                and not isinstance(
                    getattr(self, i), types.FunctionType | types.MethodType
                )
            ]
        )


# Database tables
class Stores():
    table = _Table("stores")

    id_ = _Field(table, "id", UUID)
    name = _Field(table, "name", str)

    class Record(_BaseRecord):
        def __init__(self, id_: UUID, name: str):
            self.id = id_
            self.name = name

        # TODO XXX in every table:
        # 1) DRY: try to move create_from_dict method to _BaseRecord
        # 2) instead of using ..dict["field"] use ..dict[cls.parent.field.name]
        @classmethod
        def create_from_dict(cls, dict_: dict):
            return cls(
                id_=dict_["id"],
                name=dict_["name"],
            )


class Addresses():
    table = _Table("addresses")

    id_ = _Field(table, "id", UUID)
    store_id = _Field(table, "store_id", UUID)
    address = _Field(table, "address", str)

    class Record(_BaseRecord):
        def __init__(self, id_: UUID, store_id: UUID, address: str):
            self.id = id_
            self.store_id = store_id
            self.address = address

        @classmethod
        def create_from_dict(cls, dict_: dict):
            return cls(
                id_=dict_["id"],
                store_id=dict_["store_id"],
                address=dict_["address"],
            )


class Packages():
    table = _Table("packages")

    id_ = _Field(table, "id", UUID)
    address_id = _Field(table, "address_id", UUID)
    description = _Field(table, "description", str)
    pickup_before = _Field(table, "pickup_before", datetime)
    amount = _Field(table, "amount", int)
    price = _Field(table, "price", int)

    class Record(_BaseRecord):
        def __init__(
            self,
            id_: UUID,
            address_id: UUID,
            description: str,
            pickup_before: datetime,
            amount: int,
            price: int,
        ):
            self.id = id_
            self.address_id = address_id
            self.description = description
            self.pickup_before = pickup_before
            self.amount = amount
            self.price = price

        @classmethod
        def create_from_dict(cls, dict_: dict):
            return cls(
                id_=dict_["id"],
                address_id=dict_["address_id"],
                description=dict_["description"],
                pickup_before=dict_["pickup_before"],
                amount=dict_["amount"],
                price=dict_["price"],
            )

        @property
        def time(self):
            dt = str(self.pickup_before)
            HHmm_time = dt.split()[1][:-3]
            return HHmm_time


class Orders():
    table = _Table("orders")

    id_ = _Field(table, "id", UUID)

    class Record(_BaseRecord):
        def __init__(self, id_: UUID):
            self.id = id_

        @classmethod
        def create_from_dict(cls, dict_: dict):
            return cls(
                id_=dict_["id"],
            )


class OrderPackages():
    table = _Table("order_packages")

    order_id = _Field(table, "order_id", UUID)
    package_id = _Field(table, "package_id", UUID)

    class Record(_BaseRecord):
        def __init__(self, order_id: UUID, package_id: UUID):
            self.order_id = order_id
            self.package_id = package_id

        @classmethod
        def create_from_dict(cls, dict_: dict):
            return cls(
                order_id=dict_["order_id"],
                package_id=dict_["package_id"],
            )


class Partners():
    table = _Table("partners")

    chat_id = _Field(table, "chat_id", int)

    class Record(_BaseRecord):
        def __init__(self, chat_id: int):
            self.chat_id = chat_id

        @classmethod
        def create_from_dict(cls, dict_: dict):
            return cls(
                chat_id=dict_["chat_id"],
            )


class PartnerAddresses():
    table = _Table("partner_addresses")

    partner_id = _Field(table, "partner_id", int)
    address_id = _Field(table, "address_id", UUID)

    class Record(_BaseRecord):
        def __init__(self, partner_id: int, address_id: UUID):
            self.partner_id = partner_id
            self.address_id = address_id

        @classmethod
        def create_from_dict(cls, dict_: dict):
            return cls(
                partner_id=dict_["partner_id"],
                address_id=dict_["address_id"],
            )


class PartnerPackages():
    table = _Table("partner_packages")

    partner_id = _Field(table, "partner_id", int)
    package_id = _Field(table, "package_id", UUID)

    class Record(_BaseRecord):
        def __init__(self, partner_id: int, package_id: UUID):
            self.partner_id = partner_id
            self.package_id = package_id

        @classmethod
        def create_from_dict(cls, dict_: dict):
            return cls(
                partner_id=dict_["partner_id"],
                package_id=dict_["package_id"],
            )


class PartnerOrders():
    table = _Table("partner_orders")

    partner_id = _Field(table, "partner_id", int)
    order_id = _Field(table, "order_id", UUID)

    class Record(_BaseRecord):
        def __init__(self, partner_id: int, order_id: UUID):
            self.partner_id = partner_id
            self.order_id = order_id

        @classmethod
        def create_from_dict(cls, dict_: dict):
            return cls(
                partner_id=dict_["partner_id"],
                order_id=dict_["order_id"],
            )
