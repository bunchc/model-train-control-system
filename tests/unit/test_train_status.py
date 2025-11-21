import pytest
from central_api.app.services.config_manager import ConfigManager
from central_api.app.models.schemas import TrainStatus
import tempfile
import os


@pytest.fixture
def temp_db():
    db_fd, db_path = tempfile.mkstemp()
    yield db_path
    os.close(db_fd)
    os.remove(db_path)


def test_update_and_get_train_status(temp_db):
    config = ConfigManager(db_path=temp_db)
    # Insert status
    config.update_train_status("train-1", 42, 12.5, 0.8, "section_A")
    status = config.get_train_status("train-1")
    assert isinstance(status, TrainStatus)
    assert status.train_id == "train-1"
    assert status.speed == 42
    assert status.voltage == 12.5
    assert status.current == 0.8
    assert status.position == "section_A"

    # Update status
    config.update_train_status("train-1", 0, 12.0, 0.0, "section_B")
    status = config.get_train_status("train-1")
    assert status.speed == 0
    assert status.position == "section_B"
