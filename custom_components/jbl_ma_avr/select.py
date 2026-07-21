"""Select platform for JBL MA AVR — enum-valued settings."""
import logging
from dataclasses import dataclass
from collections.abc import Callable, Coroutine
from typing import Any

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    DOMAIN,
    DISPLAY_DIM_MODES,
    DISPLAY_DIM_MODES_INV,
    ROOM_EQ_MODES,
    ROOM_EQ_MODES_INV,
    DOLBY_MODES,
    DOLBY_MODES_INV,
)
from .jbl_api import JblApi

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class JblSelectEntityDescription(SelectEntityDescription):
    """Describes a JBL MA AVR select entity."""

    options_map: dict[int, str] = None  # type: ignore[assignment]
    options_map_inv: dict[str, int] = None  # type: ignore[assignment]
    value_fn: Callable[[JblApi], int | None] = lambda _: None
    set_fn: Callable[[JblApi, int], Coroutine[Any, Any, None]] = lambda _, __: None


SELECT_DESCRIPTIONS: list[JblSelectEntityDescription] = [
    JblSelectEntityDescription(
        key="display_dim",
        name="Display Brightness",
        icon="mdi:brightness-6",
        options_map=DISPLAY_DIM_MODES,
        options_map_inv=DISPLAY_DIM_MODES_INV,
        options=list(DISPLAY_DIM_MODES.values()),
        value_fn=lambda api: api.display_dim,
        set_fn=lambda api, v: api.set_display_dim(v),
    ),
    JblSelectEntityDescription(
        key="room_eq",
        name="Room EQ",
        icon="mdi:equalizer-outline",
        options_map=ROOM_EQ_MODES,
        options_map_inv=ROOM_EQ_MODES_INV,
        options=list(ROOM_EQ_MODES.values()),
        value_fn=lambda api: api.room_eq,
        set_fn=lambda api, v: api.set_room_eq(v),
    ),
    JblSelectEntityDescription(
        key="dolby_mode",
        name="Dolby Mode",
        icon="mdi:dolby",
        options_map=DOLBY_MODES,
        options_map_inv=DOLBY_MODES_INV,
        options=list(DOLBY_MODES.values()),
        value_fn=lambda api: api.dolby_mode,
        set_fn=lambda api, v: api.set_dolby_mode(v),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up JBL MA AVR select entities."""
    api: JblApi = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        JblMaAvrSelect(api, config_entry.entry_id, description)
        for description in SELECT_DESCRIPTIONS
    )


class JblMaAvrSelect(SelectEntity):
    """Representation of a JBL MA AVR select entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        api: JblApi,
        entry_id: str,
        description: JblSelectEntityDescription,
    ) -> None:
        """Initialise the select entity."""
        self._api = api
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)})
        self._attr_options = description.options

    async def async_added_to_hass(self) -> None:
        """Register state-change callback."""
        self._api.register_callback(self.async_write_ha_state)

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option."""
        raw = self.entity_description.value_fn(self._api)
        if raw is None:
            return None
        return self.entity_description.options_map.get(raw)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        raw = self.entity_description.options_map_inv.get(option)
        if raw is not None:
            await self.entity_description.set_fn(self._api, raw)
