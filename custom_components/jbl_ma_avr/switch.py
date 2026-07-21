"""Switch platform for JBL MA AVR — boolean features."""
import logging
from dataclasses import dataclass
from collections.abc import Callable, Coroutine
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .jbl_api import JblApi

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class JblSwitchEntityDescription(SwitchEntityDescription):
    """Describes a JBL MA AVR switch."""

    value_fn: Callable[[JblApi], bool | None] = lambda _: None
    turn_on_fn: Callable[[JblApi], Coroutine[Any, Any, None]] = lambda _: None
    turn_off_fn: Callable[[JblApi], Coroutine[Any, Any, None]] = lambda _: None


SWITCH_DESCRIPTIONS: list[JblSwitchEntityDescription] = [
    JblSwitchEntityDescription(
        key="party_mode",
        name="Party Mode",
        icon="mdi:party-popper",
        value_fn=lambda api: api.party_mode,
        turn_on_fn=lambda api: api.set_party_mode(True),
        turn_off_fn=lambda api: api.set_party_mode(False),
    ),
    JblSwitchEntityDescription(
        key="dialog_enhance",
        name="Dialog Enhance",
        icon="mdi:account-voice",
        value_fn=lambda api: api.dialog_enhance,
        turn_on_fn=lambda api: api.set_dialog_enhance(True),
        turn_off_fn=lambda api: api.set_dialog_enhance(False),
    ),
    JblSwitchEntityDescription(
        key="dolby_compression",
        name="Dolby DRC",
        icon="mdi:equalizer",
        value_fn=lambda api: api.dolby_compression,
        turn_on_fn=lambda api: api.set_dolby_compression(True),
        turn_off_fn=lambda api: api.set_dolby_compression(False),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up JBL MA AVR switch entities."""
    api: JblApi = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        JblMaAvrSwitch(api, config_entry.entry_id, description)
        for description in SWITCH_DESCRIPTIONS
    )


class JblMaAvrSwitch(SwitchEntity):
    """Representation of a JBL MA AVR switch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        api: JblApi,
        entry_id: str,
        description: JblSwitchEntityDescription,
    ) -> None:
        """Initialise the switch."""
        self._api = api
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)})

    async def async_added_to_hass(self) -> None:
        """Register state-change callback."""
        self._api.register_callback(self.async_write_ha_state)

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        return self.entity_description.value_fn(self._api)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.entity_description.turn_on_fn(self._api)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.entity_description.turn_off_fn(self._api)
