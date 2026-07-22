from custom_components.jbl_ma_avr.number import NUMBER_DESCRIPTIONS
import logging
import asyncio
from typing import Any
from homeassistant.components.remote import (
    RemoteEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from .const import IR_COMMANDS, DOMAIN
from .jbl_api import JblApi

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up JBL MA AVR number entities."""
    api: JblApi = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [JBLMARemote(api, config_entry.entry_id)]
    )

class JBLMARemote(RemoteEntity):
    """JBL MA Receiver Remote Entity."""

    def __init__(self, api, entry_id) -> None:
        self._api = api
        self._attr_name = "Remote"
        self._attr_unique_id = f"{entry_id}_remote"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)})
        self._attr_is_on = True

    async def async_turn_on(self, activity: str | None = None, **kwargs: Any) -> None:
         """Send the power off command."""
         await self._api.turn_on()

    async def async_turn_off(self, activity: str | None = None, **kwargs: Any) -> None:
         """Send the power off command."""
         await self._api.turn_off()

    async def async_send_command(self, command: list[str], **kwargs: Any) -> None:
        """Send a sequence of IR commands to the receiver."""
        num_repeats = kwargs.get("num_repeats", 1)
        delay_secs = kwargs.get("delay_secs", 0.1)

        for _ in range(num_repeats):
            for cmd in command:
                normalized_key = cmd.upper().strip().replace(" ", "_")

                if payload := IR_COMMANDS.get(normalized_key):
                    _LOGGER.debug("Sending IR Payload '%s' for command '%s'", payload, cmd)
                    await self._api.send_ir_command(payload)
                else:
                    _LOGGER.warning("Unknown IR command requested: '%s'", cmd)

                if len(command) > 1 and delay_secs > 0:
                    await asyncio.sleep(delay_secs)