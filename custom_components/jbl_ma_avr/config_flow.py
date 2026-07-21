import logging
import voluptuous as vol

from typing import Any

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.components.ssdp import SsdpServiceInfo
from homeassistant.components.zeroconf import ZeroconfServiceInfo

from .const import DOMAIN, DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)

class JblMaAvrConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for JBL MA AVR."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_host: str | None = None
        self._discovered_name: str | None = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            # We could add connection validation here
            return self.async_create_entry(title=user_input[CONF_HOST], data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_HOST): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )

    async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> config_entries.ConfigFlowResult:
        """Handle a discovered device via SSDP."""
        host = discovery_info.ssdp_location.split("//")[1].split(":")[0] if discovery_info.ssdp_location else None
        if not host:
            return self.async_abort(reason="no_host")

        self._discovered_host = host
        self._discovered_name = discovery_info.upnp.get("friendlyName", "JBL MA AVR")

        if udn := discovery_info.upnp.get("UDN"):
            await self.async_set_unique_id(udn)
            self._abort_if_unique_id_configured(updates={CONF_HOST: host})
        
        self._async_abort_entries_match({CONF_HOST: host})

        self.context["title_placeholders"] = {"name": self._discovered_name}
        return await self.async_step_discovery_confirm()

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> config_entries.ConfigFlowResult:
        """Handle a discovered device via Zeroconf."""
        self._discovered_host = discovery_info.host
        self._discovered_name = discovery_info.name.split(".")[0]

        self._async_abort_entries_match({CONF_HOST: self._discovered_host})

        self.context["title_placeholders"] = {"name": self._discovered_name}
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Confirm discovery."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovered_name or self._discovered_host or "JBL MA Series AV Receiver",
                data={CONF_HOST: self._discovered_host},
            )

        return self.async_show_form(
            step_id="discovery_confirm",
            description_placeholders={"name": self._discovered_name},
        )
