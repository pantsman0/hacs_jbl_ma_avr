"""Button platform for JBL MA AVR — one-shot actions."""
import logging
from dataclasses import dataclass
from collections.abc import Callable, Coroutine
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .jbl_api import JblApi

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class JblButtonEntityDescription(ButtonEntityDescription):
    """Describes a JBL MA AVR button."""

    press_fn: Callable[[JblApi], Coroutine[Any, Any, None]] = lambda _: None


BUTTON_DESCRIPTIONS: list[JblButtonEntityDescription] = [
    JblButtonEntityDescription(
        key="reboot",
        name="Reboot",
        icon="mdi:restart",
        press_fn=lambda api: api.reboot(),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up JBL MA AVR button entities."""
    api: JblApi = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        JblMaAvrButton(api, config_entry.entry_id, description)
        for description in BUTTON_DESCRIPTIONS
    )


class JblMaAvrButton(ButtonEntity):
    """Representation of a JBL MA AVR button."""

    _attr_has_entity_name = True

    def __init__(
        self,
        api: JblApi,
        entry_id: str,
        description: JblButtonEntityDescription,
    ) -> None:
        """Initialise the button."""
        self._api = api
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)})

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.entity_description.press_fn(self._api)
