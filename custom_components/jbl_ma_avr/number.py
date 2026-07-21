"""Number platform for JBL MA AVR — EQ and volume parameters."""
import logging
from dataclasses import dataclass
from collections.abc import Callable, Coroutine
from typing import Any

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .jbl_api import JblApi

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class JblNumberEntityDescription(NumberEntityDescription):
    """Describes a JBL MA AVR number entity."""

    value_fn: Callable[[JblApi], float | None] = lambda _: None
    set_fn: Callable[[JblApi, float], Coroutine[Any, Any, None]] = lambda _, __: None


NUMBER_DESCRIPTIONS: list[JblNumberEntityDescription] = [
    JblNumberEntityDescription(
        key="treble_eq",
        name="Treble",
        icon="mdi:music-clef-treble",
        native_min_value=-12,
        native_max_value=12,
        native_step=1,
        native_unit_of_measurement="dB",
        mode=NumberMode.SLIDER,
        value_fn=lambda api: api.treble_eq,
        set_fn=lambda api, v: api.set_treble_eq(int(v)),
    ),
    JblNumberEntityDescription(
        key="bass_eq",
        name="Bass",
        icon="mdi:music-clef-bass",
        native_min_value=-12,
        native_max_value=12,
        native_step=1,
        native_unit_of_measurement="dB",
        mode=NumberMode.SLIDER,
        value_fn=lambda api: api.bass_eq,
        set_fn=lambda api, v: api.set_bass_eq(int(v)),
    ),
    JblNumberEntityDescription(
        key="party_volume",
        name="Party Volume",
        icon="mdi:speaker",
        native_min_value=0,
        native_max_value=99,
        native_step=1,
        mode=NumberMode.SLIDER,
        value_fn=lambda api: api.party_volume,
        set_fn=lambda api, v: api.set_party_volume(int(v)),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up JBL MA AVR number entities."""
    api: JblApi = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        JblMaAvrNumber(api, config_entry.entry_id, description)
        for description in NUMBER_DESCRIPTIONS
    )


class JblMaAvrNumber(NumberEntity):
    """Representation of a JBL MA AVR numeric parameter."""

    _attr_has_entity_name = True

    def __init__(
        self,
        api: JblApi,
        entry_id: str,
        description: JblNumberEntityDescription,
    ) -> None:
        """Initialise the number entity."""
        self._api = api
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)})

    async def async_added_to_hass(self) -> None:
        """Register state-change callback."""
        self._api.register_callback(self.async_write_ha_state)

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        return self.entity_description.value_fn(self._api)

    async def async_set_native_value(self, value: float) -> None:
        """Set a new value."""
        await self.entity_description.set_fn(self._api, value)
