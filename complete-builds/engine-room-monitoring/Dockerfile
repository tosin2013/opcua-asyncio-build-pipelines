# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container to /app
WORKDIR /app

# Add current directory files to /app in container
ADD engine-room-monitoring.py /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir asyncua aiokafka prometheus_client

# Make TCP port 4840 available to the world outside this container
EXPOSE 4840

# Define environment variable for verbose logging
ENV PYTHONUNBUFFERED=1

# Run main.py when the container launches
CMD ["python", "-u", "engine-room-monitoring.py"]
