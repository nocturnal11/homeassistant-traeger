"""TraegerBaseEntity class"""
import time
import logging
from homeassistant.helpers.entity import Entity
from .const import DOMAIN, NAME, VERSION, ATTRIBUTION

_LOGGER = logging.getLogger(__name__)

class TraegerBaseEntity(Entity):
    def __init__(self, client, grill_id):
        super().__init__()
        self.grill_id = grill_id
        self.client = client
        self.grill_refresh_state()

    def grill_refresh_state(self):
        self.grill_state = self.client.get_state_for_device(self.grill_id)
        self.grill_units = self.client.get_units_for_device(self.grill_id)
        self.grill_details = self.client.get_details_for_device(self.grill_id)
        self.grill_features = self.client.get_features_for_device(self.grill_id)
        self.grill_settings = self.client.get_settings_for_device(self.grill_id)
        self.grill_limits = self.client.get_limits_for_device(self.grill_id)
        self.grill_cloudconnect = self.client.get_cloudconnect(self.grill_id)

    def grill_register_callback(self):
        # Tell the Traeger client to call grill_update() when it gets an update
        self.client.set_callback_for_grill(self.grill_id, self.grill_update_internal)

    def grill_update_internal(self):
        self.grill_refresh_state()
        if self.hass is None:
            return
        # Tell HA we have an update
        self.schedule_update_ha_state()

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return self.grill_id

    @property
    def should_poll(self):
        return False

    @property
    def device_info(self):
        if self.grill_settings is None:
            return {
                "identifiers": {(DOMAIN, self.grill_id)},
                "name": NAME,
                "manufacturer": NAME
            }
        return {
            "identifiers": {(DOMAIN, self.grill_id)},
            "name": self.grill_details["friendlyName"],
            "model": self.grill_settings["device_type_id"],
            "sw_version": self.grill_settings["fw_version"],
            "manufacturer": NAME
        }

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "attribution": ATTRIBUTION,
            "integration": DOMAIN,
        }

class TraegerProbeReliabilityManager:
    """Manages probe connection reliability and state persistence"""
    
    def __init__(self):
        self.probe_states = {}  # uuid -> probe reliability state
        
    def get_probe_state(self, probe_uuid):
        """Get or create probe reliability state"""
        if probe_uuid not in self.probe_states:
            self.probe_states[probe_uuid] = {
                'last_connected_time': 0,
                'last_disconnected_time': 0,
                'connection_failures': 0,
                'consecutive_failures': 0,
                'target_temp_backup': None,
                'connection_history': [],  # Recent connection events
                'availability_grace_until': 0,
                'last_valid_temp': None,
                'temp_validation_failures': 0
            }
        return self.probe_states[probe_uuid]
    
    def update_probe_connection(self, probe_uuid, is_connected, temperature=None):
        """Update probe connection state and calculate reliability metrics"""
        state = self.get_probe_state(probe_uuid)
        current_time = time.time()
        
        # Update connection history (keep last 10 events)
        state['connection_history'].append({
            'time': current_time,
            'connected': is_connected,
            'temperature': temperature
        })
        if len(state['connection_history']) > 10:
            state['connection_history'].pop(0)
        
        if is_connected:
            if state['last_connected_time'] == 0 or current_time - state['last_disconnected_time'] > 5:
                # New connection or significant gap
                state['consecutive_failures'] = 0
                _LOGGER.debug(f"Probe {probe_uuid} connected")
            state['last_connected_time'] = current_time
            
            # Validate temperature reading
            if temperature is not None:
                if self._is_valid_temperature(temperature, state['last_valid_temp']):
                    state['last_valid_temp'] = temperature
                    state['temp_validation_failures'] = 0
                else:
                    state['temp_validation_failures'] += 1
                    _LOGGER.warning(f"Probe {probe_uuid} invalid temperature: {temperature}")
        else:
            state['last_disconnected_time'] = current_time
            state['consecutive_failures'] += 1
            state['connection_failures'] += 1
            
            # Set grace period for temporary disconnections
            if state['consecutive_failures'] <= 3:
                grace_period = min(30 * state['consecutive_failures'], 120)  # 30s to 2min
                state['availability_grace_until'] = current_time + grace_period
                _LOGGER.debug(f"Probe {probe_uuid} disconnected, grace period: {grace_period}s")
            else:
                _LOGGER.warning(f"Probe {probe_uuid} multiple failures: {state['consecutive_failures']}")
    
    def should_show_available(self, probe_uuid, raw_connected):
        """Determine if probe should show as available considering grace periods"""
        if raw_connected:
            return True
            
        state = self.get_probe_state(probe_uuid)
        current_time = time.time()
        
        # Check if we're in grace period
        if current_time < state['availability_grace_until']:
            return True
            
        return False
    
    def backup_target_temperature(self, probe_uuid, target_temp):
        """Backup probe target temperature for persistence"""
        if target_temp and target_temp > 0:
            state = self.get_probe_state(probe_uuid)
            state['target_temp_backup'] = target_temp
    
    def get_backup_target_temperature(self, probe_uuid):
        """Get backed up target temperature"""
        state = self.get_probe_state(probe_uuid)
        return state.get('target_temp_backup')
    
    def _is_valid_temperature(self, temp, last_valid_temp):
        """Validate temperature reading for reasonableness"""
        if temp is None:
            return False
            
        # Basic range check (reasonable cooking temperatures)
        if temp < -10 or temp > 600:  # Fahrenheit range
            return False
            
        # Check for sudden large changes (could indicate sensor issues)
        if last_valid_temp is not None:
            temp_change = abs(temp - last_valid_temp)
            if temp_change > 100:  # 100°F sudden change is suspicious
                return False
                
        return True
    
    def get_connection_quality(self, probe_uuid):
        """Calculate connection quality score (0-100)"""
        state = self.get_probe_state(probe_uuid)
        
        if len(state['connection_history']) < 2:
            return 50  # Unknown quality
            
        # Calculate recent connection stability
        recent_events = state['connection_history'][-5:]  # Last 5 events
        connected_count = sum(1 for event in recent_events if event['connected'])
        connection_ratio = connected_count / len(recent_events)
        
        # Factor in consecutive failures
        failure_penalty = min(state['consecutive_failures'] * 20, 80)
        
        quality = int((connection_ratio * 100) - failure_penalty)
        return max(0, min(100, quality))

class TraegerGrillMonitor:
    def __init__(self, client, grill_id, async_add_devices, probe_entity = None):
        self.client = client
        self.grill_id = grill_id
        self.async_add_devices = async_add_devices
        self.probe_entity = probe_entity
        self.accessory_status = {}
        self.device_state = self.client.get_state_for_device(self.grill_id)
        # Initialize probe reliability manager
        if not hasattr(client, 'probe_reliability'):
            client.probe_reliability = TraegerProbeReliabilityManager()
        self.grill_add_accessories()
        self.client.set_callback_for_grill(self.grill_id, self.grill_monitor_internal)

    def grill_monitor_internal(self):
        self.device_state = self.client.get_state_for_device(self.grill_id)
        self.grill_add_accessories()

    def grill_add_accessories(self):
        if self.device_state is None:
            return
        for accessory in self.device_state["acc"]:
            if accessory["type"] == "probe":
                if accessory["uuid"] not in self.accessory_status:
                    if self.probe_entity:
                        # FIXED: Use thread-safe call for async_add_devices
                        self.client.hass.loop.call_soon_threadsafe(
                            lambda: self.async_add_devices([self.probe_entity(self.client, self.grill_id, accessory["uuid"])])
                        )
                        self.accessory_status[accessory["uuid"]] = True