"""Sensor platform for JBL MA AVR — read-only state values."""
import logging
from dataclasses import dataclass
from collections.abc import Callable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, STREAMING_SERVERS, STREAMING_PLAY_STATES
from .jbl_api import JblApi

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class JblSensorEntityDescription(SensorEntityDescription):
    """Describes a JBL MA AVR sensor."""

    value_fn: Callable[[JblApi], str | None] = lambda _: None


def _streaming_value(api: JblApi) -> str | None:
    if api.streaming_server is None or api.streaming_state is None:
        return None
    server = STREAMING_SERVERS.get(api.streaming_server, f"Server {api.streaming_server}")
    state = STREAMING_PLAY_STATES.get(api.streaming_state, f"State {api.streaming_state}")
    return f"{server} – {state}"


SENSOR_DESCRIPTIONS: list[JblSensorEntityDescription] = [
    JblSensorEntityDescription(
        key="streaming_state",
        name="Streaming",
        icon="mdi:cast-audio",
        value_fn=_streaming_value,
    ),
    JblSensorEntityDescription(
        key="version_ip_control",
        name="IP Control Version",
        icon="mdi:information-outline",
        value_fn=lambda api: api.version_ip_control,
    ),
    JblSensorEntityDescription(
        key="version_host",
        name="Host Version",
        icon="mdi:chip",
        value_fn=lambda api: api.version_host,
    ),
    JblSensorEntityDescription(
        key="version_dsp",
        name="DSP Version",
        icon="mdi:waveform",
        value_fn=lambda api: api.version_dsp,
    ),
    JblSensorEntityDescription(
        key="version_osd",
        name="OSD Version",
        icon="mdi:television-play",
        value_fn=lambda api: api.version_osd,
    ),
    JblSensorEntityDescription(
        key="version_net",
        name="Network Version",
        icon="mdi:lan",
        value_fn=lambda api: api.version_net,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up JBL MA AVR sensor entities."""
    api: JblApi = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        JblMaAvrSensor(api, config_entry.entry_id, description)
        for description in SENSOR_DESCRIPTIONS
    )


class JblMaAvrSensor(SensorEntity):
    """Representation of a JBL MA AVR sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        api: JblApi,
        entry_id: str,
        description: JblSensorEntityDescription,
    ) -> None:
        """Initialise the sensor."""
        self._api = api
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)})

    async def async_added_to_hass(self) -> None:
        """Register state-change callback."""
        self._api.register_callback(self.async_write_ha_state)

    @property
    def native_value(self) -> str | None:
        """Return the sensor value."""
        return self.entity_description.value_fn(self._api)
