from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([RefreshButton(entry.runtime_data, entry.entry_id)])


class RefreshButton(CoordinatorEntity, ButtonEntity):
    _attr_has_entity_name = True
    _attr_name = "Historie aktualisieren"
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_refresh"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "EnBW mobility+",
            "manufacturer": "EnBW",
        }

    async def async_press(self):
        await self.coordinator.async_request_refresh()
