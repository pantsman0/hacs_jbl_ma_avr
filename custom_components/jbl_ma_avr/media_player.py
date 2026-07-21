import logging

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, SOURCES, SOURCES_INV
from .jbl_api import JblApi

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the JBL MA AVR media player."""
    api: JblApi = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([JblMaAvrMediaPlayer(api, config_entry.entry_id)])


class JblMaAvrMediaPlayer(MediaPlayerEntity):
    """Representation of a JBL MA AVR."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, api: JblApi, entry_id: str) -> None:
        """Initialize the media player."""
        self._api = api
        self._attr_unique_id = entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="JBL MA AVR",
            manufacturer="JBL",
            model="MA Series AV Receiver",
        )
        self._attr_supported_features = (
            MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
            | MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_STEP
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.SELECT_SOURCE
        )

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self._api.register_callback(self.async_write_ha_state)

    @property
    def device_class(self) -> MediaPlayerDeviceClass:
        """Return the device class of the entity."""
        return MediaPlayerDeviceClass.RECEIVER

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the device."""
        if self._api.power is None:
            return MediaPlayerState.OFF
        if self._api.power:
            return MediaPlayerState.ON
        return MediaPlayerState.OFF

    @property
    def volume_level(self) -> float | None:
        """Volume level of the media player (0..1)."""
        if self._api.volume is None:
            return None
        return self._api.volume / 99.0

    @property
    def volume_step(self) -> float:
        """Step size to use for volume_up() and volume_down()."""
        return 1.0 / 99.0

    @property
    def is_volume_muted(self) -> bool | None:
        """Boolean if volume is currently muted."""
        return self._api.mute

    @property
    def source(self) -> str | None:
        """Name of the current input source."""
        if self._api.source is None:
            return None
        return SOURCES.get(self._api.source, f"Unknown ({self._api.source})")

    @property
    def source_list(self) -> list[str]:
        """List of available input sources."""
        return list(SOURCES.values())

    async def async_turn_on(self) -> None:
        """Turn the media player on."""
        await self._api.turn_on()

    async def async_turn_off(self) -> None:
        """Turn the media player off."""
        await self._api.turn_off()

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute the volume."""
        await self._api.mute_volume(mute)

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        vol_int = int(volume * 99)
        await self._api.set_volume(vol_int)
        
    async def async_volume_up(self) -> None:
        """Turn volume up for media player."""
        await self._api.volume_up()
            
    async def async_volume_down(self) -> None:
        """Turn volume down for media player."""
        await self._api.volume_down()

    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        if source in SOURCES_INV:
            await self._api.select_source(SOURCES_INV[source])
