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
        WHERE {PartnerAddresses.partner_id} = {chat_id}
        """
        )

        partner_addresses_ids = await self.fetch(addresses_ids_sql_query)

        partner_addresses = list(
            map(
                lambda x: await self.get_by_id(Addresses, x),
                partner_addresses_ids,
            )
        )

        return partner_addresses

    async def get_partner_packages(self, chat_id: int) -> list[Packages.Record]:
        packages_ids_sql_query = SqlQuery(
            f"""
        SELECT * FROM {PartnerPackages.table}
        WHERE {PartnerPackages.partner_id} = {chat_id}
        """
        )

        partner_packages_ids = await self.fetch(packages_ids_sql_query)

        partner_packages = list(
            map(
                lambda x: await self.get_by_id(Packages, x),
                partner_packages_ids,
            )
        )

        return partner_packages

    async def get_partner_orders(self, chat_id: int) -> list[Orders.Record]:
        orders_ids_sql_query = SqlQuery(
            f"""
        SELECT * FROM {PartnerOrders.table}
        WHERE {PartnerOrders.partner_id} = {chat_id}
        """
        )

        partner_orders_ids = await self.fetch(orders_ids_sql_query)

        partner_orders = list(
            map(
                lambda x: await self.get_by_id(Orders, x),
                partner_orders_ids,
            )
        )

        return partner_orders

    async def get_by_id(self, type_: type, id_: UUID):
        assert type_ in [Stores, Addresses, Packages, Orders], "Invalid type."

        sql_query = SqlQuery(
            f"""
        SELECT 1 FROM {type_.table}
        WHERE {type_.id_} = {id_}
        """
        )

        record = type_.Record.create_from_dict(
            await self.fetch(sql_query)
        )

        return record

    async def get_order_packages(self, order_id: UUID) -> list[Packages.Record]:
        sql_query = SqlQuery(
            f"""
        SELECT * FROM {OrderPackages.table}
        WHERE {Orders.id_} = {order_id}
        """
        )

        order_packages = list(
            map(
                lambda x: Packages.Record.create_from_dict(x),
                await self.fetch(sql_query),
            )
        )

        return order_packages
