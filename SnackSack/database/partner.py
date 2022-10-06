import uuid as _uuid


class Partner:
    def __init__(
        self,
        chat_id: int,
        uuid: _uuid.UUID = _uuid.uuid4(),
        stores: list = [],
        addresses: list = [],
        packages: list = [],
        orders: list = [],
    ):
        self.chat_id = chat_id
        self.uuid = uuid
        self.stores = stores
        self.addresses = addresses
        self.packages = packages
        self.orders = orders

    def to_json(self):
        return {
            "chat_id": self.chat_id,
            "uuid": str(self.uuid),
            "stores": self.stores,
            "addresses": self.addresses,
            "packages": self.packages,
            "orders": self.orders,
        }

    @classmethod
    def from_json(cls, json_record):
        return cls(
            json_record["chat_id"],
            json_record["uuid"],
            json_record["stores"],
            json_record["addresses"],
            json_record["packages"],
            json_record["orders"],
        )

    def change_uuid(self):
        self.uuid = _uuid.uuid4()
