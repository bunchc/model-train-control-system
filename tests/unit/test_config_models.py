from central_api.app.models.schemas import (
    Plugin,
    EdgeController,
    Train,
    TrainPlugin,
    FullConfig,
)


def test_plugin_model():
    plugin = Plugin(
        name="stepper_hat",
        description="Stepper hat plugin",
        config={"port": 1, "enabled": True},
    )
    assert plugin.name == "stepper_hat"
    assert plugin.config["port"] == 1
    assert plugin.config["enabled"] is True

    train = Train(
        id="train-1",
        name="Durango Silverton",
        description="A train",
        model="K-28",
        plugin=TrainPlugin(name="stepper_hat", config={"port": 1}),
    )
    assert train.id == "train-1"
    assert train.plugin.name == "stepper_hat"
    assert train.plugin.config["port"] == 1

    train = Train(
        id="train-1",
        name="Durango Silverton",
        description="A train",
        model="K-28",
        plugin=TrainPlugin(name="stepper_hat", config={"port": 1}),
    )
    ec = EdgeController(
        id="ec1",
        name="Holiday Display",
        description="Edge controller",
        address="192.168.2.214",
        enabled=True,
        trains=[train],
    )
    assert ec.id == "ec1"
    assert ec.trains[0].name == "Durango Silverton"

    plugin = Plugin(
        name="stepper_hat",
        description="Stepper hat plugin",
        config={"port": 1, "enabled": True},
    )
    train = Train(
        id="train-1",
        name="Durango Silverton",
        description="A train",
        model="K-28",
        plugin=TrainPlugin(name="stepper_hat", config={"port": 1}),
    )
    ec = EdgeController(
        id="ec1",
        name="Holiday Display",
        description="Edge controller",
        address="192.168.2.214",
        enabled=True,
        trains=[train],
    )
    full_cfg = FullConfig(plugins=[plugin.dict()], edge_controllers=[ec.dict()])
    assert full_cfg.plugins[0].name == "stepper_hat"
    assert full_cfg.edge_controllers[0].id == "ec1"
