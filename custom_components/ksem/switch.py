import logging
from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    wallbox_coordinator = data.get("wallbox_coordinator")  # kann None sein
    client = data["client"]

    # Bevorzugt das Wallbox-Device; wenn (noch) nicht vorhanden, ans Smartmeter hängen
    smartmeter_device_info = data.get("device_info")
    wallbox_device_info = data.get("wallbox_device_info")

    if not wallbox_coordinator:
        _LOGGER.info(
            "Kein Wallbox-Coordinator vorhanden – BatteryUsageSwitch wird übersprungen."
        )
        return

    entities = []

    if wallbox_coordinator:
        entities.append(BatteryUsageSwitch(wallbox_coordinator, client, wallbox_device_info, entry.entry_id))
        if wallbox_coordinator.data and "evse" in wallbox_coordinator.data:
            for evse in wallbox_coordinator.data["evse"]:
                uuid = evse.get("uuid")
                if uuid:
                    entities.append(
                        KsemChargePauseSwitch(wallbox_coordinator, client, wallbox_device_info, entry.entry_id, uuid)
                    )
    
    async_add_entities(entities, update_before_add=False)

class BatteryUsageSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, client, device_info: DeviceInfo, entry_id: str):
        super().__init__(coordinator)
        self._client = client
        self._attr_name = "Battery Usage bei PV"
        # pro Config-Eintrag eindeutig, falls Integration mehrfach vorhanden ist
        self._attr_unique_id = f"{entry_id}_ksem_battery_usage"
        self._attr_device_info = device_info

    @property
    def available(self) -> bool:
        # verfügbar, wenn Coordinator zuletzt erfolgreich und energyflow_config vorhanden ist
        if not self.coordinator.last_update_success:
            return False
        data = self.coordinator.data or {}
        return "energyflow_config" in data

    @property
    def is_on(self):
        cfg = (self.coordinator.data or {}).get("energyflow_config") or {}
        return bool(cfg.get("batteryusage", False))

    async def async_turn_on(self, **kwargs):
        await self._client.set_battery_usage(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self._client.set_battery_usage(False)
        await self.coordinator.async_request_refresh()

class KsemChargePauseSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, client, device_info, entry_id, uuid):
        super().__init__(coordinator)
        self._client = client
        self._uuid = uuid
        self._attr_device_info = device_info
        self._attr_name = "Pause Charging"
        self._attr_unique_id = f"{entry_id}_pause_{uuid}"
        self._attr_icon = "mdi:pause-circle"

    @property
    def is_on(self):
        # Prüft den Status in der evse-Liste des Coordinators.
        if not self.coordinator.data:
            return False
            
        evse_data_list = self.coordinator.data.get("evse", [])
        for wb in evse_data_list:
            if wb.get("uuid") == self._uuid:
                return "Paused" in wb.get("state", "")
        return False
        return "Paused" in evse_state

    async def async_turn_on(self, **kwargs):
        # Schalter AN -> Pause AKTIV -> {"pause": true}.
        await self._client.set_pause_charging(self._uuid, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        # Schalter AUS -> Pause INAKTIV -> {"pause": false}.
        await self._client.set_pause_charging(self._uuid, False)
        await self.coordinator.async_request_refresh()

