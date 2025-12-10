import requests
import os

API_PORT = os.getenv("API_PORT", "8000")
BASE_URL = f"http://localhost:{API_PORT}/api/trains"


def test_end_to_end_train_control():
    # Step 1: List available trains
    response = requests.get(BASE_URL)
    assert response.status_code == 200
    trains = response.json()
    assert isinstance(trains, list) and len(trains) > 0

    # Step 2: Send command to start the first train
    train_id = trains[0]["id"]
    command_payload = {"speed": 50}
    command_response = requests.post(
        f"{BASE_URL}/{train_id}/command", json=command_payload
    )
    assert command_response.status_code == 200

    # Step 3: Check the status of the train
    status_response = requests.get(f"{BASE_URL}/{train_id}/status")
    assert status_response.status_code == 200
    status = status_response.json()
    assert status["speed"] == 50

    # Step 4: Send command to stop the train
    stop_command_payload = {"speed": 0}
    stop_command_response = requests.post(
        f"{BASE_URL}/{train_id}/command", json=stop_command_payload
    )
    assert stop_command_response.status_code == 200

    # Step 5: Verify the train has stopped
    status_response = requests.get(f"{BASE_URL}/{train_id}/status")
    assert status_response.status_code == 200
    status = status_response.json()
    assert status["speed"] == 0
