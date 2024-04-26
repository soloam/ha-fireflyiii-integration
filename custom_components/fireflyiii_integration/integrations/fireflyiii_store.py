"""FireflyIII Integration Store"""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.json import JSONEncoder
from homeassistant.helpers.storage import Store
from homeassistant.util import json as json_util

from ..const import STORE_PREFIX, STORE_VERSION
from .fireflyiii_exceptions import FireflyiiiException

_LOGGER = logging.getLogger(__name__)


class FireflyiiiStore(Store):
    """FireflyIII Store"""

    def __init__(
        self,
        hass: HomeAssistant,
        version: str,
        key: str,
    ) -> None:
        self._key = key
        self._hass = hass
        self._version = version

        super().__init__(
            hass, version, self.key, encoder=JSONEncoder, atomic_writes=True
        )

    @property
    def key(self) -> str:
        """Store Key"""
        return f"{STORE_PREFIX}.{self._key}"

    @classmethod
    def get_store(cls, hass: HomeAssistant, key: str) -> "FireflyiiiStore":
        """Get The Store"""
        return cls(hass, STORE_VERSION, key)

    @classmethod
    async def async_get_store(cls, hass: HomeAssistant, key: str) -> "FireflyiiiStore":
        """Get The Store Async"""
        return await cls.get_store(hass, key).async_load()

    async def save(self, data=None):
        """Save Store to disk"""
        current = await FireflyiiiStore.async_get_store(self._hass, self.key)
        if current is None or current != data:
            await FireflyiiiStore.async_get_store(self._hass, self.key).async_save(data)
            return
        _LOGGER.debug(
            "<HACSStore async_save_to_store> Did not store data for '%s'. Content did not change",
            self.key,
        )

    async def remove(self):
        """Remove store"""
        await FireflyiiiStore.async_get_store(self._hass, self.key).async_remove()

    def load(self):
        """Load the data from disk if version matches."""
        try:
            data = json_util.load_json(self.path)
        except (
            BaseException  # lgtm [py/catch-base-exception] pylint: disable=broad-except
        ) as exception:
            _LOGGER.critical(
                "Could not load '%s', restore it from a backup or delete the file: %s",
                self.path,
                exception,
            )
            raise FireflyiiiException(exception) from exception
        if data == {} or data["version"] != self.version:
            return None
        return data["data"]

    async def _async_migrate_func(self, old_major_version, old_minor_version, old_data):
        """Migrate to the new version."""
