import json
import logging
from datetime import timedelta

from hikconnect.api import HikConnect
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=3)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    data = hass.data[DOMAIN]
    api, coordinator = data["api"], data["coordinator"]

    new_entities = []
    for device_info in coordinator.data:
        new_entities.append(CallStatusSensor(api, device_info))

    if new_entities:
        async_add_entities(new_entities, update_before_add=True)


class CallStatusSensor(SensorEntity):
    """
    Represents a call status of an indoor station.
    """

    def __init__(self, api: HikConnect, device_info: dict):
        super().__init__()
        self._api = api
        self._device_info = device_info

    async def async_update(self) -> None:
        res = await self._api.get_call_status(self._device_info["serial"])
        # TODO fix API of hikconnect library / make it more human friendly
        res_json = json.loads(res)
        status = res_json["callStatus"]
        info = res_json["callerInfo"]

        try:
            self._attr_native_value = {1: "idle", 2: "ringing", 3: "call in progress"}[status]
        except KeyError:
            _LOGGER.warning("Unknown call status: %s", status)
            self._attr_native_value = "unknown"

        try:
            self._attr_extra_state_attributes = {
                "building_number": info["buildingNo"],
                "floor_number": info["floorNo"],
                "zone_number": info["zoneNo"],
                "unit_number": info["unitNo"],
                "device_number": info["devNo"],
                "device_type": info["devType"],
                "lock_number": info["lockNum"],
            }
        except KeyError:
            _LOGGER.exception("Error getting call info: %s", status)

    @property
    def name(self):
        return f"{self._device_info['name']} call status"  # TODO translate?

    @property
    def unique_id(self):
        return "-".join((DOMAIN, self._device_info["id"], "call-status"))

    @property
    def device_info(self):
        # https://developers.home-assistant.io/docs/device_registry_index/#device-properties
        return {
            "identifiers": {(DOMAIN, self._device_info["id"])},
        }

    @property
    def icon(self):
        # TODO fix duplication of constants?
        if self.native_value == "idle":
            return "mdi:phone-hangup"
        elif self.native_value == "ringing":
            return "mdi:phone-ring"
        elif self.native_value == "call in progress":
            return "mdi:phone-in-talk"
        else:
            return "mdi:phone-alert"
