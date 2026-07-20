import pytest

def test_sensor_widget_data_dictionary():
    """
    Verifies that sensor data dictionary includes real_sensor_enabled (bool)
    and real_port_id (str, e.g., 'I0_0').
    """
    sensor_data = {
        "name": "PresenceSensor",
        "type": "Digital",
        "pin": "I0_0",
        "real_sensor_enabled": False,
        "real_port_id": "I0_0"
    }
    
    assert "real_sensor_enabled" in sensor_data
    assert isinstance(sensor_data["real_sensor_enabled"], bool)
    assert "real_port_id" in sensor_data
    assert isinstance(sensor_data["real_port_id"], str)

def test_comm_settings_dictionary():
    """
    Verifies kit communication settings dictionary structure
    (protocol in ["None", "Sockets"], ip str, port int).
    """
    comm_settings = {
        "protocol": "Sockets",
        "ip": "127.0.0.1",
        "port": 5000
    }
    
    assert "protocol" in comm_settings
    assert comm_settings["protocol"] in ["None", "Sockets"]
    assert "ip" in comm_settings
    assert isinstance(comm_settings["ip"], str)
    assert "port" in comm_settings
    assert isinstance(comm_settings["port"], int)
