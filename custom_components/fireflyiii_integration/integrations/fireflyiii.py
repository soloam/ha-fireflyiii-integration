"""FireflyIII Integration API Access Class"""

import json
from datetime import datetime, timedelta

# from functools import cache, cached_property
from typing import List

import aiohttp
from aiohttp.client_exceptions import ContentTypeError, ServerTimeoutError
from datetimerange import DateTimeRange

from .fireflyiii_exceptions import AuthenticationError, ParseJSONError


class Fireflyiii:
    """Api Access class"""

    def __init__(
        self,
        host,
        access_token=None,
        timerange: DateTimeRange = None,
        verify_certificates=False,
    ) -> None:
        self._api = "/api/v1"
        self._host = host
        self._access_token = access_token
        self._verify_certificates = verify_certificates
        self._about = None
        self._preferences = {}
        self._timerange = timerange

    @property
    async def version(self) -> str:
        """Get FireflyIII version"""
        about = await self.about()

        if not about or not "version" in about:
            return ""

        return about["version"]

    @property
    async def os(self) -> str:
        """Get FireflyIII OS"""
        about = await self.about()

        if not about or not "os" in about:
            return ""

        return about["os"]

    @property
    def host(self) -> str:
        """Get FireflyIII Host"""
        return self._host

    @property
    def host_api(self) -> str:
        """Get FireflyIII URL for API"""
        return self.host + self._api

    @property
    async def default_currency(self) -> str:
        """Get FireflyIII Default Currency"""
        default_currency = await self._request_api("GET", "/currencies/default")
        if not "data" in default_currency:
            return ""

        if not "attributes" in default_currency["data"]:
            return ""

        return default_currency["data"]["attributes"].get("code", "")

    @property
    async def start_year(self) -> str:
        """Get FireflyIII start of year"""

        if "fiscalYearStart" in self._preferences:
            return self._preferences["fiscalYearStart"]

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

        self._preferences["fiscalYearStart"] = date.strftime("%Y-%m-%d")

        return self._preferences["fiscalYearStart"]

    async def accounts(self, types: List[str]) -> list[dict]:
        """Get FireflyIII Accounts"""
        accounts = await self._request_api("GET", "/accounts")
        if not "data" in accounts:
            return {}

        # // Get Account State at the end of the timerange
        date_range = {}
        if self._timerange:
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

        data = {}

        for account in accounts["data"]:
            account_id = account.get("id", 0)

            if account_id == 0:
                continue

            if "attributes" not in account:
                continue

            if types and account["attributes"]["type"] not in types:
                continue

            transactions = self.transactions(account_id, 5)

            for range_key, dt_range in date_range.items():
                path = f"/accounts/{account_id}"

                param = {"date": dt_range}
                account_obj = await self._request_api("GET", path, param)
                if account_obj and "data" in account_obj:
                    if account_id not in data:
                        data[account_id] = {}

                    data[account_id][range_key] = account_obj[
                        "data"
                    ]  # For now we assume the same state

            transactions = await transactions

        return data

    async def categories(self) -> list[dict]:
        """Get FireflyIII categories"""
        categories = await self._request_api("GET", "/categories")
        if not "data" in categories:
            return []

        date_range = {}
        if self._timerange:
            date_range = {
                "start": self._timerange.start_datetime.strftime("%Y-%m-%d"),
                "end": self._timerange.end_datetime.strftime("%Y-%m-%d"),
            }

        data = {}

        for category in categories["data"]:
            category_id = category.get("id", 0)
            if category_id == 0:
                continue
            path = f"/categories/{category_id}"
            category_obj = await self._request_api("GET", path, date_range)
            if category_obj and "data" in category_obj:
                data[category_id] = category_obj["data"]

        return data

    async def transactions(self, account_id: str = None, limit=None):
        """Get FireflyIII transactions"""
        if account_id:
            path = f"/accounts/{account_id}/transactions"
        else:
            path = "/transactions"

        date_range = {}
        if self._timerange:
            date_range = {
                "start": self._timerange.start_datetime.strftime("%Y-%m-%d"),
                "end": self._timerange.end_datetime.strftime("%Y-%m-%d"),
            }

        params = {}
        params.update(date_range)

        if limit:
            params["limit"] = limit

        transactions = await self._request_api("GET", path, params)
        if not "data" in transactions:
            return []

        return transactions["data"]

    async def check_connection(self) -> bool:
        """Check if FireflyIII is connected"""
        about = await self._about_get()
        if about:
            return True

        return False

    async def _about_get(self) -> dict:
        """Returns FireflyIII about Information"""

        about = await self._request_api("GET", "/about")
        if "data" in about and "version" in about["data"]:
            about = about["data"]
        else:
            about = {}

        return about

    async def about(self) -> dict:
        """Returns FireflyIII about Information with cache"""

        if self._about:
            return self._about

        about = await self._about_get()

        self._about = about

        return about

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

            await session.close()
            return message
