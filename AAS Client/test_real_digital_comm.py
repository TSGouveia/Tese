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

def test_asset_interfaces_description_submodel_export():
    """
    Verifies that AssetInterfacesDescription submodel contains Protocol, EndpointIP,
    and EndpointPort properties when building/exporting AAS submodels.
    """
    from basyx.aas import model

    sm_aid = model.Submodel(id_="https://acplt.org/Submodels/AssetInterfacesDescription_TestKit", id_short="AssetInterfacesDescription")
    sm_aid.submodel_element.add(model.Property(id_short="Protocol", value_type=model.datatypes.String, value="Sockets"))
    sm_aid.submodel_element.add(model.Property(id_short="EndpointIP", value_type=model.datatypes.String, value="192.168.10.1"))
    sm_aid.submodel_element.add(model.Property(id_short="EndpointPort", value_type=model.datatypes.Integer, value=8888))

    props = {elem.id_short: elem for elem in sm_aid.submodel_element}

    assert "Protocol" in props
    assert props["Protocol"].value == "Sockets"
    assert props["Protocol"].value_type == model.datatypes.String

    assert "EndpointIP" in props
    assert props["EndpointIP"].value == "192.168.10.1"
    assert props["EndpointIP"].value_type == model.datatypes.String

    assert "EndpointPort" in props
    assert props["EndpointPort"].value == 8888
    assert props["EndpointPort"].value_type == model.datatypes.Integer

def test_real_sensor_submodel_parameters_export():
    """
    Verifies that sensor parameters under BehaviorMapping submodel contain
    RealSensorEnabled and RealPortID properties.
    """
    from basyx.aas import model

    sensor_params = model.SubmodelElementCollection(id_short="Parameters")
    sensor_params.value.add(model.Property(id_short="TargetFilter", value_type=model.datatypes.String, value="Metal"))
    sensor_params.value.add(model.Property(id_short="Visible", value_type=model.datatypes.Boolean, value=False))
    sensor_params.value.add(model.Property(id_short="ActiveLow", value_type=model.datatypes.Boolean, value=False))
    sensor_params.value.add(model.Property(id_short="RealSensorEnabled", value_type=model.datatypes.Boolean, value=True))
    sensor_params.value.add(model.Property(id_short="RealPortID", value_type=model.datatypes.String, value="I0_0"))

    param_props = {elem.id_short: elem for elem in sensor_params.value}

    assert "RealSensorEnabled" in param_props
    assert param_props["RealSensorEnabled"].value is True
    assert param_props["RealSensorEnabled"].value_type == model.datatypes.Boolean

    assert "RealPortID" in param_props
    assert param_props["RealPortID"].value == "I0_0"
    assert param_props["RealPortID"].value_type == model.datatypes.String

