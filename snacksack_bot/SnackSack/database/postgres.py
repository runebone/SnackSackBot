from uuid import UUID

from .sql_query import SqlQuery

from .tables import Stores
from .tables import Addresses
from .tables import Packages
from .tables import Orders
from .tables import OrderPackages
from .tables import Partners
from .tables import PartnerAddresses
from .tables import PartnerPackages
from .tables import PartnerOrders

from .base_db import BaseDB


class PostgresDB(BaseDB):
    async def get_all_packages(self) -> list[Packages.Record]:
        sql_query = SqlQuery(
            f"""
        SELECT * FROM {Packages.table}
        """
        )

        packages_list = list(
            map(
                lambda x: Packages.Record.create_from_dict(x),
                await self.fetch(sql_query),
            )
        )

        return packages_list

    async def get_all_partners(self) -> list[Partners.Record]:
        sql_query = SqlQuery(
            f"""
        SELECT * FROM {Partners.table}
        """
        )

        partners_list = list(
            map(
                lambda x: Partners.Record.create_from_dict(x),
                await self.fetch(sql_query),
            )
        )

        return partners_list

    async def get_partner_addresses(self, chat_id: int) -> list[Addresses.Record]:
        addresses_ids_sql_query = SqlQuery(
            f"""
        SELECT * FROM {PartnerAddresses.table}
        WHERE {PartnerAddresses.partner_id} = :chat_id
        """,
        chat_id=chat_id
        )

        partner_addresses_ids = list(
            map(
                lambda x: PartnerAddresses.Record.create_from_dict(x),
                await self.fetch(addresses_ids_sql_query)
            )
        )

        partner_addresses = [
            await self.get_by_id(Addresses, x.address_id) for x in partner_addresses_ids
        ]

        return partner_addresses

    async def get_partner_packages(self, chat_id: int) -> list[Packages.Record]:
        packages_ids_sql_query = SqlQuery(
            f"""
        SELECT * FROM {PartnerPackages.table}
        WHERE {PartnerPackages.partner_id} = :chat_id
        """,
        chat_id=chat_id
        )

        partner_packages_ids = list(
            map(
                lambda x: PartnerPackages.Record.create_from_dict(x),
                await self.fetch(packages_ids_sql_query)
            )
        )

        partner_packages = [
            await self.get_by_id(Packages, x.package_id) for x in partner_packages_ids
        ]

        return partner_packages

    async def get_partner_orders(self, chat_id: int) -> list[Orders.Record]:
        orders_ids_sql_query = SqlQuery(
            f"""
        SELECT * FROM {PartnerOrders.table}
        WHERE {PartnerOrders.partner_id} = :chat_id
        """,
        chat_id=chat_id
        )

        partner_orders_ids = list(
            map(
                lambda x: PartnerOrders.Record.create_from_dict(x),
                await self.fetch(orders_ids_sql_query)
            )
        )

        partner_orders = [
            await self.get_by_id(Orders, x.order_id) for x in partner_orders_ids
        ]

        return partner_orders

    async def get_by_id(self, type_: type, id_: UUID):
        assert type_ in [Stores, Addresses, Packages, Orders], "Invalid type."

        sql_query = SqlQuery(
            f"""
        SELECT * FROM {type_.table}
        WHERE {type_.id_} = :id_
        """,
        id_=id_
        )

        fetched_record = (await self.fetch(sql_query))[0]

        record = type_.Record.create_from_dict(
            fetched_record
        )

        return record

    async def get_order_packages(self, order_id: UUID) -> list[Packages.Record]:
        sql_query = SqlQuery(
            f"""
        SELECT * FROM {OrderPackages.table}
        WHERE {OrderPackages.order_id} = :order_id
        """,
        order_id=order_id
        )

        order_packages = list(
            map(
                lambda x: OrderPackages.Record.create_from_dict(x),
                await self.fetch(sql_query)
            )
        )

        packages = []
        for order_package in order_packages:
            packages.append(
                await self.get_by_id(Packages, order_package.package_id)
            )

        return packages

    async def create_partner(self, chat_id: int):
        sql_query = SqlQuery(
            f"""
        INSERT INTO {Partners.table} ({Partners.chat_id})
        VALUES (:chat_id)
        """,
        chat_id=chat_id
        )

        # TODO: log; catch errors
        await self.execute(sql_query)

    async def create_store(self, record: Stores.Record):
        # INSERT INTO:
        # -> stores
        sql_query = SqlQuery(
            f"""
        INSERT INTO {Stores.table} ({Stores.id_}, {Stores.name})
        VALUES (:record_id, :record_name)
        """,
        record_id=record.id,
        record_name=record.name
        )

        # TODO: log; catch errors
        await self.execute(sql_query)

    async def create_address(self, partner_chat_id: int, record: Addresses.Record):
        # INSERT INTO:
        # -> addresses
        # -> partner_addresses
        sql_query = SqlQuery(
            f"""
        INSERT INTO {Addresses.table}
        ({Addresses.id_}, {Addresses.store_id}, {Addresses.address})
        VALUES (:record_id, :record_store_id, :record_address)
        """,
        record_id=record.id,
        record_store_id=record.store_id,
        record_address=record.address
        )

        # TODO: log; catch errors
        await self.execute(sql_query)

        sql_query = SqlQuery(
            f"""
        INSERT INTO {PartnerAddresses.table}
        ({PartnerAddresses.partner_id}, {PartnerAddresses.address_id})
        VALUES (:partner_chat_id, :record_id)
        """,
        partner_chat_id=partner_chat_id,
        record_id=record.id
        )

        # TODO: log; catch errors
        await self.execute(sql_query)

    async def create_package(self, partner_chat_id: int, record: Packages.Record):
        # INSERT INTO:
        # -> packages
        # -> partner_packages
        sql_query = SqlQuery(
            f"""
        INSERT INTO {Packages.table}
        ({Packages.id_}, {Packages.address_id}, {Packages.description}, {Packages.pickup_before}, {Packages.amount}, {Packages.price})
        VALUES (:record_id, :record_address_id, :record_description, :record_pickup_before, :record_amount, :record_price)
        """,
        record_id=record.id,
        record_address_id=record.address_id,
        record_description=record.description,
        record_pickup_before=record.pickup_before,
        record_amount=record.amount,
        record_price=record.price
        )

        # TODO: log; catch errors
        await self.execute(sql_query)

        sql_query = SqlQuery(
            f"""
        INSERT INTO {PartnerPackages.table}
        ({PartnerPackages.partner_id}, {PartnerPackages.package_id})
        VALUES (:partner_chat_id, :record_id)
        """,
        partner_chat_id=partner_chat_id,
        record_id=record.id
        )

        # TODO: log; catch errors
        await self.execute(sql_query)

    async def create_order(self, record: Orders.Record, packages: list[Packages.Record]):
        # INSERT INTO:
        # -> orders
        # -> order_packages
        # -> partner_orders
        sql_query = SqlQuery(
            f"""
        INSERT INTO {Orders.table} ({Orders.id_}, {Orders.chat_id}, {Orders.random_number})
        VALUES (:record_id, :record_chat_id, :random_number)
        """,
        record_id=record.id,
        record_chat_id=record.chat_id,
        random_number=record.random_number
        )

        # TODO: log; catch errors
        await self.execute(sql_query)

        for package in packages:
            sql_query = SqlQuery(
                f"""
            INSERT INTO {OrderPackages.table}
            ({OrderPackages.order_id}, {OrderPackages.package_id})
            VALUES (:record_id, :package_id)
            """,
            record_id=record.id,
            package_id=package.id
            )

            # TODO: log; catch errors
            await self.execute(sql_query)

        # FIXME consider all packages belong to a single partner
        partner = await self.get_partner_by_package(packages[0])

        sql_query = SqlQuery(
            f"""
        INSERT INTO {PartnerOrders.table}
        ({PartnerOrders.partner_id}, {PartnerOrders.order_id})
        VALUES (:partner_chat_id, :record_id)
        """,
        partner_chat_id=partner.chat_id,
        record_id=record.id
        )

        # TODO: log; catch errors
        await self.execute(sql_query)


    async def get_partner_by_package(self, package: Packages.Record) -> Partners.Record:
        sql_query = SqlQuery(
            f"""
        SELECT * FROM {PartnerPackages.table}
        WHERE {PartnerPackages.package_id} = :package_id
        """,
        package_id=package.id
        )

        partner_package = PartnerPackages.Record.create_from_dict((await self.fetch(sql_query))[0])

        partner_sql_query = SqlQuery(
            f"""
        SELECT * FROM {Partners.table}
        WHERE {Partners.chat_id} = :partner_id
        """,
        partner_id=partner_package.partner_id
        )

        partner_dict = (await self.fetch(partner_sql_query))[0]

        partner = Partners.Record.create_from_dict(partner_dict)

        return partner

    async def decrement_package_amount(self, package_id: UUID):
        sql_query = SqlQuery(
                f"""
                UPDATE {Packages.table}
                SET {Packages.amount} = {Packages.amount} - 1
                WHERE {Packages.id_} = :package_id
                """,
                package_id=package_id
                )
        await self.execute(sql_query)

    async def increment_package_amount(self, package_id: UUID):
        sql_query = SqlQuery(
                f"""
                UPDATE {Packages.table}
                SET {Packages.amount} = {Packages.amount} + 1
                WHERE {Packages.id_} = :package_id
                """,
                package_id=package_id
                )
        await self.execute(sql_query)

    async def delete_order(self, order_id: UUID):
        sql_query = SqlQuery(
                f"""
                DELETE FROM {Orders.table}
                WHERE {Orders.id_} = :order_id
                """,
                order_id=order_id
                )
        await self.execute(sql_query)

    async def delete_package(self, package_id: UUID):
        sql_query = SqlQuery(
                f"""
                DELETE FROM {Packages.table}
                WHERE {Packages.id_} = :package_id
                """,
                package_id=package_id
                )
        await self.execute(sql_query)
