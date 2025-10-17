from fastapi import FastAPI
from controllers import CommandController
from mqtt_client import MQTTClient

app = FastAPI()

# Initialize the MQTT client
mqtt_client = MQTTClient()

# Set up command controller
command_controller = CommandController(mqtt_client)

@app.on_event("startup")
async def startup_event():
    await mqtt_client.connect()
    mqtt_client.subscribe_to_topics()

@app.on_event("shutdown")
async def shutdown_event():
    await mqtt_client.disconnect()

@app.post("/command")
async def send_command(command: dict):
    response = await command_controller.handle_command(command)
    return response

@app.get("/status")
async def get_status():
    status = await command_controller.get_status()
    return status