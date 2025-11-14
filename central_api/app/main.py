import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import trains, config

# Ensure config.yaml is present and loaded before app starts
CONFIG_PATH = os.getenv("CENTRAL_API_CONFIG_YAML", "/app/config.yaml")
if not os.path.exists(CONFIG_PATH):
    raise RuntimeError(f"Config file not found at {CONFIG_PATH}. Please mount config.yaml.")
else:
    print(f"[Startup] Found config.yaml at {CONFIG_PATH}")

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this as needed for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(config.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Model Train Control System API"}