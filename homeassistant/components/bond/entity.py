"""An abstract class common to all Bond entities."""
from abc import abstractmethod
from asyncio import TimeoutError as AsyncIOTimeoutError
import logging
from typing import Any, Dict, Optional

from aiohttp import ClientError

from homeassistant.const import ATTR_NAME
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .utils import BondDevice, BondHub

_LOGGER = logging.getLogger(__name__)


class BondEntity(Entity):
    """Generic Bond entity encapsulating common features of any Bond controlled device."""

    def __init__(self, hub: BondHub, device: BondDevice):
        """Initialize entity with API and device info."""
        self._hub = hub
        self._device = device
        self._available = True

    @property
    def unique_id(self) -> Optional[str]:
        """Get unique ID for the entity."""
        return self._device.device_id

    @property
    def name(self) -> Optional[str]:
        """Get entity name."""
        return self._device.name

    @property
    def device_info(self) -> Optional[Dict[str, Any]]:
        """Get a an HA device representing this Bond controlled device."""
        return {
            ATTR_NAME: self.name,
            "identifiers": {(DOMAIN, self._device.device_id)},
            "via_device": (DOMAIN, self._hub.bond_id),
        }

    @property
    def assumed_state(self) -> bool:
        """Let HA know this entity relies on an assumed state tracked by Bond."""
        return True

    @property
    def available(self) -> bool:
        """Report availability of this entity based on last API call results."""
        return self._available

    async def async_update(self):
        """Fetch assumed state of the cover from the hub using API."""
        try:
            state: dict = await self._hub.bond.device_state(self._device.device_id)
        except (ClientError, AsyncIOTimeoutError, OSError) as error:
            if self._available:
                _LOGGER.warning(
                    "Entity %s has become unavailable", self.entity_id, exc_info=error
                )
            self._available = False
        else:
            if not self._available:
                _LOGGER.info("Entity %s has come back", self.entity_id)
            self._available = True
            self._apply_state(state)

    @abstractmethod
    def _apply_state(self, state: dict):
        raise NotImplementedError
