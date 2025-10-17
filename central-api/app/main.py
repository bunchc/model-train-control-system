from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import trains

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
app.include_router(trains.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Model Train Control System API"}