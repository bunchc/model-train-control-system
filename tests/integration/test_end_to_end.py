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
    import time
    train_id = trains[0]["id"]
    command_payload = {"speed": 50}
    command_response = requests.post(
        f"{BASE_URL}/{train_id}/command", json=command_payload
    )
    assert command_response.status_code == 200

    # Wait for the command to take effect (polling with timeout)
    def poll_for_speed(expected_speed, timeout=5):
        start = time.time()
        while time.time() - start < timeout:
            status_response = requests.get(f"{BASE_URL}/{train_id}/status")
            if status_response.status_code == 200:
                status = status_response.json()
                if status.get("speed") == expected_speed:
                    return status
            time.sleep(0.5)
        # Final check after timeout
        status_response = requests.get(f"{BASE_URL}/{train_id}/status")
        assert status_response.status_code == 200
        status = status_response.json()
        assert status["speed"] == expected_speed
        return status

    # Step 3: Check the status of the train
    status = poll_for_speed(50, timeout=5)

    # Step 4: Send command to stop the train
    stop_command_payload = {"speed": 0}
    stop_command_response = requests.post(
        f"{BASE_URL}/{train_id}/command", json=stop_command_payload
    )
    assert stop_command_response.status_code == 200

    # Wait for the stop command to take effect (polling with timeout)
    status = poll_for_speed(0, timeout=5)
