import uuid as _uuid

Time = str


class Package:
    def __init__(
        self,
        store: str,
        address: str,
        description: str,
        time: Time,
        amount: int,
        price: int,
        uuid: _uuid.UUID = _uuid.uuid4(),
    ):
        self.store = store
        self.address = address
        self.description = description
        self.time = time
        self.amount = amount
        self.price = price
        self.uuid = uuid

    def to_json(self):
        return {
            "store": self.store,
            "address": self.address,
            "description": self.description,
            "time": str(self.time),
            "amount": self.amount,
            "price": self.price,
            "uuid": str(self.uuid),
        }

    @classmethod
    def from_json(cls, json_record):
        return cls(
            json_record["store"],
            json_record["address"],
            json_record["description"],
            json_record["time"],
            json_record["amount"],
            json_record["price"],
            json_record["uuid"],
        )

    def change_uuid(self):
        self.uuid = _uuid.uuid4()

    def __str__(self):
        return f"""<b>Магазин</b>: {self.store}
<b>Адрес</b>:\n{self.address}
<b>Описание</b>:\n{self.description}
<b>Забрать до</b>: {self.time}
<b>Кол-во</b>: {self.amount}
<b>Цена (за 1 шт.)</b>: {self.price}"""
