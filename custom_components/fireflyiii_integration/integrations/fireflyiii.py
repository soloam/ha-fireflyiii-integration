"""FireflyIII Integration API Access Class"""

import json
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp.client_exceptions import ContentTypeError, ServerTimeoutError
from datetimerange import DateTimeRange

from .fireflyiii_exceptions import AuthenticationError, ParseJSONError
from .fireflyiii_objects import (
    FireflyiiiAbout,
    FireflyiiiAccount,
    FireflyiiiBill,
    FireflyiiiBillPayment,
    FireflyiiiBudget,
    FireflyiiiCategory,
    FireflyiiiCurrency,
    FireflyiiiObjectBaseList,
    FireflyiiiObjectType,
    FireflyiiiPiggyBank,
    FireflyiiiPreferences,
    FireflyiiiTransaction,
)


class Fireflyiii:
    """Api Access class"""

    def __init__(
        self,
        host,
        access_token=None,
        timerange: Optional[DateTimeRange] = None,
        verify_certificates=False,
    ) -> None:
        self._api = "/api/v1"
        self._host = host
        self._access_token = access_token
        self._verify_certificates = verify_certificates
        self._about: FireflyiiiAbout = FireflyiiiAbout()
        self._preferences: FireflyiiiPreferences = FireflyiiiPreferences()
        self._timerange: Optional[DateTimeRange] = timerange

    @property
    async def version(self) -> str:
        """Get FireflyIII version"""
        about = await self.about()

        if not about:
            return ""

        return about.version

    @property
    async def os(self) -> str:
        """Get FireflyIII OS"""
        about = await self.about()

        if not about:
            return ""

        return about.os

    @property
    def host(self) -> str:
        """Get FireflyIII Host"""
        return self._host

    @property
    def host_api(self) -> str:
        """Get FireflyIII URL for API"""
        return self.host + self._api

    @property
    async def default_currency(self) -> FireflyiiiCurrency:
        """Get FireflyIII Default Currency"""
        default_currency = await self._request_api("GET", "/currencies/default")
        if not "data" in default_currency:
            return FireflyiiiCurrency.empty()

        if not "attributes" in default_currency["data"]:
            return FireflyiiiCurrency.empty()

        attributes = default_currency["data"].get("attributes", {})

        default_currency = FireflyiiiCurrency(
            id=attributes.get("id", ""),
            name=attributes.get("name", ""),
            code=attributes.get("code", ""),
            symbol=attributes.get("symbol", ""),
            enabled=attributes.get("enabled", True),
            decimal_places=attributes.get("decimal_places", 2),
        )

        return default_currency

    @property
    async def start_year(self) -> str:
        """Get FireflyIII start of year"""

        if self._preferences.year_start:
            return self._preferences.year_start

        year_start = await self._request_api("GET", "/preferences/fiscalYearStart")
        if not "data" in year_start:
            return ""

        if not "attributes" in year_start["data"]:
            return ""

        start = year_start["data"]["attributes"].get("data", "")
        if not start:
            return ""

        start = start + "-" + str(datetime.today().year)

        try:
            date = datetime.strptime(start, "%m-%d-%Y")
        except ValueError:
            return ""

        self._preferences.year_start = date.strftime("%Y-%m-%d")

        return self._preferences.year_start

    @property
    async def accounts_autocomplete(
        self,
    ) -> FireflyiiiObjectBaseList:
        """Returns simple information regarding accounts"""

        # pylint: disable=import-outside-toplevel
        from .fireflyiii_config import FireflyiiiConfig as ffconfig

        accounts = await self._request_api("GET", "/autocomplete/accounts")
        if not isinstance(accounts, list):
            return FireflyiiiObjectBaseList()

        fireflyiii_config = ffconfig()

        account_list = FireflyiiiObjectBaseList()
        for account in accounts:
            account_type = account.get("type", "")

            if not any(
                sub.lower() in account_type.lower()
                for sub in fireflyiii_config.get_account_types
            ):
                continue

            account_obj = FireflyiiiAccount(
                id=account.get("id", ""),
                name=account.get("name_with_balance", ""),
                type=account.get("type", ""),
                iban="",
                currency=account.get("currency_code", ""),
                balance=0,
                balance_beginning=0,
            )

            account_list.update(account_obj)

        return account_list

    async def accounts(
        self, types: Optional[List[str]] = None, ids: Optional[List[str]] = None
    ) -> FireflyiiiObjectBaseList:
        """Get FireflyIII Accounts"""
        account_list = FireflyiiiObjectBaseList(type=FireflyiiiObjectType.ACCOUNTS)

        accounts = await self._request_api("GET", "/accounts")
        if not "data" in accounts:
            return account_list

        # // Get Account State at the end of the timerange
        date_range = {}
        if (
            self._timerange
            and self._timerange.start_datetime
            and self._timerange.end_datetime
        ):
            date_range["start_state"] = (
                self._timerange.start_datetime - timedelta(hours=24)
            ).strftime(
                "%Y-%m-%d"
            )  # The state at the end of the day before
            date_range["end_state"] = self._timerange.end_datetime.strftime("%Y-%m-%d")
        else:
            date_range["start_state"] = (
                datetime.today() - timedelta(hours=24)
            ).strftime("%Y-%m-%d")
            date_range["end_state"] = datetime.today().strftime("%Y-%m-%d")

        for account in accounts["data"]:
            account_id = account.get("id", 0)

            if account_id == 0:
                continue

            if "attributes" not in account:
                continue

            if types and account.get("attributes", {}).get("type") not in types:
                continue

            if ids and account.get("id", "") not in ids:
                continue

            data = {}

            # Get Account to Start And End of the range
            for range_key, dt_range in date_range.items():
                path = f"/accounts/{account_id}"

                param = {"date": dt_range}
                account_obj = await self._request_api("GET", path, param)
                if not account_obj or "data" not in account_obj:
                    continue

                data[range_key] = account_obj["data"]

            start_state = data.get("start_state", {})
            end_state = data.get("end_state", {})

            start_attibutes = start_state.get("attributes", {})
            end_attributes = end_state.get("attributes", {})

            if start_attibutes and end_attributes:
                pass
            elif not start_attibutes and end_attributes:
                start_attibutes = end_attributes
            elif start_attibutes and not end_attributes:
                end_attributes = start_attibutes
            else:
                continue

            try:
                balance = float(end_attributes.get("current_balance", 0))
            except ValueError:
                balance = float(0)

            try:
                balance_beginning = float(start_attibutes.get("current_balance", 0))
            except ValueError:
                balance_beginning = float(0)

            account_obj = FireflyiiiAccount(
                id=end_attributes.get("id", account_id),
                name=end_attributes.get("name", ""),
                type=end_attributes.get("type", ""),
                iban=end_attributes.get("iban", ""),
                currency=end_attributes.get("currency_code", ""),
                balance=balance,
                balance_beginning=balance_beginning,
            )

            account_list.update(account_obj)

        return account_list

    @property
    async def categories_autocomplete(
        self,
    ) -> FireflyiiiObjectBaseList:
        """Returns basic information regarding categories"""

        categories = await self._request_api("GET", "/autocomplete/categories")
        if not isinstance(categories, list):
            return FireflyiiiObjectBaseList()

        category_list = FireflyiiiObjectBaseList()
        for category in categories:
            category_obj = FireflyiiiCategory(
                id=category.get("id", ""),
                name=category.get("name", ""),
                currency=await self.default_currency,
            )

            category_list.update(category_obj)

        return category_list

    async def categories(self, ids=None, currency=None) -> FireflyiiiObjectBaseList:
        """Get FireflyIII categories"""
        categories = await self._request_api("GET", "/categories")
        if not "data" in categories:
            return FireflyiiiObjectBaseList()

        date_range = {}
        if (
            self._timerange
            and self._timerange.start_datetime
            and self._timerange.end_datetime
        ):
            date_range = {
                "start": self._timerange.start_datetime.strftime("%Y-%m-%d"),
                "end": self._timerange.end_datetime.strftime("%Y-%m-%d"),
            }

        category_list = FireflyiiiObjectBaseList()

        for category in categories["data"]:
            category_id = category.get("id", 0)
            if category_id == 0:
                continue

            if ids and category_id not in ids:
                continue

            path = f"/categories/{category_id}"
            category_obj = await self._request_api("GET", path, date_range)
            if category_obj and "data" in category_obj:
                attributes = category_obj["data"].get("attributes", {})
                if not attributes:
                    continue

            try:
                balance = float(attributes.get("current_balance", 0))
            except ValueError:
                balance = float(0)

            spend = attributes.get("spent", [])
            earned = attributes.get("earned", [])

            spent_get = [{}] if len(spend) == 0 else spend
            earned_get = [{}] if len(earned) == 0 else earned

            if currency:
                get_currency = currency
            else:
                get_currency = await self.default_currency

            try:
                spent_currency = sum(
                    float(s.get("sum", 0))
                    for s in spent_get
                    if s.get("currency_code", "") == str(get_currency)
                )
            except ValueError:
                spent_currency = 0

            try:
                earned_currency = sum(
                    float(s.get("sum", 0))
                    for s in earned_get
                    if s.get("currency_code", "") == str(get_currency)
                )
            except ValueError:
                earned_currency = 0

            category_obj = FireflyiiiCategory(
                id=attributes.get("id", category_id),
                name=attributes.get("name", ""),
                balance=balance,
                spent=spent_currency,
                earned=earned_currency,
                currency=get_currency,
            )

            category_list.update(category_obj)

        return category_list

    async def currencies(self, ids=None, enabled=None) -> FireflyiiiObjectBaseList:
        """Get FireflyIII currencies"""

        currency_list = FireflyiiiObjectBaseList(type=FireflyiiiObjectType.CURRENCIES)

        currencies = await self._request_api("GET", "/currencies")
        if not "data" in currencies:
            return currency_list

        for currency in currencies["data"]:
            currency_id = currency.get("id", 0)
            if currency_id == 0:
                continue

            if ids and currency_id not in ids:
                continue

            attributes = currency.get("attributes")
            if not attributes:
                continue

            currency_obj = FireflyiiiCurrency(
                id=attributes.get("id", currency_id),
                name=attributes.get("name", ""),
                code=attributes.get("code", ""),
                default=attributes.get("default", False),
                enabled=attributes.get("enabled", False),
                symbol=attributes.get("symbol", False),
            )

            if (
                enabled is not None
                and enabled is True
                and currency_obj.enabled is not True
            ):
                continue
            elif (
                enabled is not None
                and enabled is False
                and currency_obj.enabled is not False
            ):
                continue

            currency_list.update(currency_obj)

        return currency_list

    async def piggy_banks(self, ids=None) -> FireflyiiiObjectBaseList:
        """Get FireflyIII Piggy Banks"""

        piggy_bank_list = FireflyiiiObjectBaseList(
            type=FireflyiiiObjectType.PIGGY_BANKS
        )

        piggy_banks = await self._request_api("GET", "/piggy-banks")
        if not "data" in piggy_banks:
            return piggy_bank_list

        for piggy_bank in piggy_banks["data"]:
            piggy_bank_id = piggy_bank.get("id", 0)
            if piggy_bank_id == 0:
                continue

            if ids and piggy_bank_id not in ids:
                continue

            attributes = piggy_bank.get("attributes")
            if not attributes:
                continue

            account_id = attributes.get("account_id", None)
            if not account_id:
                continue

            piggy_account_list = await self.accounts(ids=[account_id])
            if not piggy_account_list:
                continue

            account_id = next(iter(piggy_account_list))
            piggy_account = piggy_account_list.get(account_id, None)

            if not isinstance(piggy_account, FireflyiiiAccount):
                continue

            piggy_bank_obj = FireflyiiiPiggyBank(
                id=attributes.get("id", piggy_bank_id),
                name=attributes.get("name", ""),
                account=piggy_account,
                target_amount=attributes.get("target_amount", 0),
                percentage=attributes.get("percentage", 0),
                current_amount=attributes.get("current_amount", 0),
                left_to_save=attributes.get("left_to_save", 0),
                currency=None,  # Get from account
            )

            piggy_bank_list.update(piggy_bank_obj)

        return piggy_bank_list

    async def budgets(self, ids=None, currency=None) -> FireflyiiiObjectBaseList:
        """Get FireflyIII Budgets"""

        budgets_list = FireflyiiiObjectBaseList(type=FireflyiiiObjectType.BUDGETS)

        date_range = {}
        if (
            self._timerange
            and self._timerange.start_datetime
            and self._timerange.end_datetime
        ):
            date_range = {
                "start": self._timerange.start_datetime.strftime("%Y-%m-%d"),
                "end": self._timerange.end_datetime.strftime("%Y-%m-%d"),
            }

        budgets = await self._request_api("GET", "/budgets", date_range)
        if not "data" in budgets:
            return budgets_list

        for budget in budgets["data"]:
            budget_id = budget.get("id", 0)
            if budget_id == 0:
                continue

            if ids and budget_id not in ids:
                continue

            attributes = budget.get("attributes")
            if not attributes:
                continue

            budget_limits = await self._request_api(
                "GET", f"/budgets/{budget_id}/limits", date_range
            )
            if not "data" in budget_limits or len(budget_limits["data"]) < 1:
                budget_limits = None
            else:
                budget_limit = budget_limits["data"][0]

            limit_attributes = budget_limit.get("attributes", {})

            try:
                start_limit = datetime.fromisoformat(limit_attributes.get("start"))
                end_limit = datetime.fromisoformat(limit_attributes.get("end"))
            except ValueError:
                start_limit = None
                end_limit = None

            if currency:
                get_currency = currency
            else:
                get_currency = await self.default_currency

            try:
                spent_currency = sum(
                    float(s.get("sum", 0))
                    for s in attributes["spent"]
                    if s.get("currency_code", "") == str(get_currency)
                )
            except ValueError:
                spent_currency = 0

            budget_obj = FireflyiiiBudget(
                id=attributes.get("id", budget_id),
                name=attributes.get("name", ""),
                spent=spent_currency,
                currency=get_currency,
                limit=limit_attributes.get("amount", 0),
                limit_start=start_limit,
                limit_end=end_limit,
            )

            budgets_list.update(budget_obj)

        return budgets_list

    async def bills(
        self, ids=None, timerange: Optional[DateTimeRange] = None
    ) -> FireflyiiiObjectBaseList:
        """Get FireflyIII bills"""

        get_timerange: Optional[DateTimeRange] = None

        if timerange:
            get_timerange = timerange
        elif self._timerange:
            # The bills object is special, it uses de time of the range up and down
            # to pull the bills
            get_timerange = deepcopy(self._timerange)
            delta = self._timerange.get_timedelta_second()
            end_date = self._timerange.end_datetime
            if end_date:
                end_date = end_date + timedelta(seconds=delta)
                end_date = end_date.replace(
                    hour=23, minute=59, second=59, microsecond=59
                )
                get_timerange.set_end_datetime(end_date)

        date_range = {}
        if (
            get_timerange
            and get_timerange.start_datetime
            and get_timerange.end_datetime
        ):
            date_range = {
                "start": get_timerange.start_datetime.strftime("%Y-%m-%d"),
                "end": get_timerange.end_datetime.strftime("%Y-%m-%d"),
            }

        bill_list = FireflyiiiObjectBaseList(type=FireflyiiiObjectType.BILLS)

        bills = await self._request_api("GET", "/bills", date_range)
        if not "data" in bills:
            return bill_list

        for bill in bills["data"]:
            bill_id = bill.get("id", 0)
            if bill_id == 0:
                continue

            if ids and bill_id not in ids:
                continue

            attributes = bill.get("attributes")
            if not attributes:
                continue

            pay_list = attributes.get("pay_dates", [])
            paid_list = attributes.get("paid_dates", [])

            pay_events = []
            for pay in pay_list:
                date = datetime.fromisoformat(pay)

                obj = FireflyiiiBillPayment(date=date)

                pay_events.append(obj)

            paid_events = []
            for paid in paid_list:
                date = datetime.fromisoformat(paid.get("date", ""))

                transactions_list = await self.transactions(
                    ids=[paid.get("transaction_journal_id")]
                )

                if transactions_list:
                    transaction_id = next(iter(transactions_list))
                    transaction = transactions_list.get(transaction_id, None)

                if not isinstance(transaction, FireflyiiiTransaction):
                    continue

                obj = FireflyiiiBillPayment(
                    date=date, payed=True, transaction=transaction
                )

                paid_events.append(obj)

            try:
                value_min = float(attributes.get("amount_min", 0))
            except ValueError:
                value_min = 0

            try:
                value_max = float(attributes.get("amount_max", 0))
            except ValueError:
                value_max = 0

            bill_obj = FireflyiiiBill(
                id=attributes.get("id", bill_id),
                name=attributes.get("name", ""),
                value_min=value_min,
                value_max=value_max,
                currency=attributes.get("currency_code", ""),
                pay=pay_events,
                paid=paid_events,
            )

            bill_list.update(bill_obj)

        return bill_list

    async def transactions(
        self, ids=None, account_id: Optional[str] = None, limit: Optional[int] = None
    ) -> FireflyiiiObjectBaseList:
        """Get FireflyIII transactions"""
        if account_id:
            path = f"/accounts/{account_id}/transactions"
        else:
            path = "/transactions"

        date_range = {}
        if (
            self._timerange
            and self._timerange.start_datetime
            and self._timerange.end_datetime
        ):
            date_range = {
                "start": self._timerange.start_datetime.strftime("%Y-%m-%d"),
                "end": self._timerange.end_datetime.strftime("%Y-%m-%d"),
            }

        params: Dict[str, Any] = {}
        params.update(date_range)

        if limit:
            params["limit"] = limit

        transactions_list = FireflyiiiObjectBaseList(
            type=FireflyiiiObjectType.TRANSACTIONS
        )

        if ids:
            transactions = []
            for tid in ids:
                transaction = await self._request_api("GET", f"{path}/{tid}")
                if "data" not in transaction:
                    continue
                transactions.append(transaction)
        else:
            transactions = await self._request_api("GET", path, params)
            if "data" not in transactions:
                return transactions_list

        for transaction in transactions:
            attributes = transaction.get("data", {}).get("attributes", {})
            if not attributes:
                continue

            transaction_id = transaction.get("data", {}).get("id", 0)
            if not transaction_id:
                continue

            attributes = attributes.get("transactions", [])
            if len(attributes) == 0:
                attributes = {}
            else:
                attributes = attributes[0]

            try:
                value = attributes.get("amount", 0)
            except ValueError:
                value = 0

            try:
                date = datetime.fromisoformat(attributes.get("date", None))
            except ValueError:
                continue

            transaction_obj = FireflyiiiTransaction(
                id=transaction_id,
                description=attributes.get("description", ""),
                value=value,
                currency=attributes.get("currency_code", ""),
                date=date,
            )

            transactions_list.update(transaction_obj)

        return transactions_list

    async def check_connection(self) -> bool:
        """Check if FireflyIII is connected"""
        about = await self._about_get()
        if not about or not about.version:
            return False

        return True

    async def _about_get(self) -> FireflyiiiAbout:
        """Returns FireflyIII about Information"""

        about = await self._request_api("GET", "/about")

        if "data" in about and "version" in about["data"]:
            data = about["data"]

            about = FireflyiiiAbout(os=data.get("os"), version=data.get("version"))

        else:
            about = None

        return about

    async def about(self) -> FireflyiiiAbout:
        """Returns FireflyIII about Information with cache"""

        if self._about:
            return self._about

        about = await self._about_get()

        self._about = about

        return about

    async def preferences(self) -> FireflyiiiPreferences:
        """Returns FireflyIII Preferences"""

        preferences = FireflyiiiPreferences(
            await self.default_currency, await self.start_year
        )
        return preferences

    def _set_auth(self, header=None):
        """Set FireflyIII API Auth Token"""
        if header is None:
            header = {}

        header["Authorization"] = f"Bearer {self._access_token}"

    def _set_headers(self, header=None):
        """Set FireflyIII API Comon Headers"""
        if header is None:
            header = {}

        header["Content-Type"] = "application/json"
        header["Accept"] = "application/json"

    async def _request_api(
        self,
        method="GET",
        path="",
        params=None,
        data=None,
        timeout=10,
    ):
        """Request FireflyIII API"""

        url = f"{self.host_api}{path}"

        method = method.lower()

        request_headers = {}

        self._set_auth(request_headers)
        self._set_headers(request_headers)

        async with aiohttp.ClientSession() as session:
            http_method = getattr(session, method)

            try:
                async with http_method(
                    url,
                    headers=request_headers,
                    params=params,
                    json=data,
                    verify_ssl=self._verify_certificates,
                    timeout=timeout,
                ) as resp:
                    try:
                        message = await resp.text()
                    except UnicodeDecodeError:
                        message = await resp.read()
                        message = message.decode(errors="replace")

                    try:
                        message = json.loads(message)
                    except ValueError:
                        pass

                    if resp.status == 400:
                        if "msg" in message.keys():
                            pass  # index = "msg"
                        elif "error" in message.keys():
                            pass  # index = "error"
                        raise ParseJSONError
                    if resp.status == 401:
                        raise AuthenticationError
                    if resp.status in [404, 405, 500]:
                        pass

                    return message
            except (TimeoutError, ServerTimeoutError):
                message = {"msg": "Timeout"}
            except ContentTypeError as err:
                message = {"msg": err}
            except AssertionError as err:
                message = {"msg": err}

            await session.close()
            return message
