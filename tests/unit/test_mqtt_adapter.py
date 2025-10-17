import pytest
from central_api.app.services.mqtt_adapter import MQTTAdapter

@pytest.fixture
def mqtt_adapter():
    return MQTTAdapter()

def test_publish_command(mqtt_adapter, mocker):
    mock_publish = mocker.patch('central_api.app.services.mqtt_adapter.paho.mqtt.publish.single')
    command = {"speed": 50}
    mqtt_adapter.publish_command("train/1/commands", command)
    mock_publish.assert_called_once_with("train/1/commands", payload='{"speed": 50}', qos=1)

def test_subscribe_to_status(mqtt_adapter, mocker):
    mock_subscribe = mocker.patch('central_api.app.services.mqtt_adapter.paho.mqtt.subscribe')
    mqtt_adapter.subscribe_to_status("train/1/status")
    mock_subscribe.assert_called_once_with("train/1/status", mqtt_adapter.on_status_message)

def test_on_status_message(mqtt_adapter):
    message = {"speed": 50, "voltage": 12}
    mqtt_adapter.on_status_message(None, None, message)
    assert mqtt_adapter.status["speed"] == 50
    assert mqtt_adapter.status["voltage"] == 12