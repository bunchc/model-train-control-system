FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install build tools and dependencies
RUN apt-get update && apt-get install -y gcc \
	&& pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app/ .

# Command to run the application
CMD ["python", "main.py"]