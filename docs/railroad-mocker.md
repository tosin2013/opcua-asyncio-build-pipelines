# Train Telemetry Simulator

## Overview
This application simulates a train by generating realistic telemetry data and publishing it to Kafka and Prometheus. It implements a PID controller to regulate the train's speed and acceleration/braking. The train parameters and environment data are also randomized for realistic variability.

## Usage
The app is designed to run in a Docker container. The following environment variables can be configured:

* `KAFKA_BROKER` - Kafka broker URL (default: localhost:9092)
* `KAFKA_TOPIC` - Kafka topic to publish to (default: random train name)
* `TARGET_SPEED` - Target speed for PID controller (km/h, default: 60)
* `SPEED_TOLERANCE` - Allowed variance around target speed (km/h, default: 5)
* `KP` - PID proportional gain (default: 1.0)
* `KI` - PID integral gain (default: 0.1)
* `KD` - PID derivative gain (default: 0.2)
* `COLLECT_WEATHER_DATA` - Set to True to retrieve live weather data (requires API key, default: False)
* `OPENWEATHERMAP_API_KEY` - API key for OpenWeatherMap
* `CITY_NAME` - City to retrieve weather for
  
The app publishes the following metrics to Kafka and Prometheus:

* Elapsed time
* Train speed
* Train acceleration
* Train braking
* Outside temperature
* Humidity
* Wind speed
* Primary suspension stiffness
* Secondary suspension stiffness
* Damping rate

Prometheus metrics are exposed on port 8000.

### Here is how you can modify the environment variables to change the speed behavior of the train simulator:

Changing Target Speed
The target speed that the PID controller tries to maintain is set by the TARGET_SPEED environment variable.

To change this, set TARGET_SPEED to your desired speed in km/h when launching the container.

For example, to set the target speed to 80 km/h:

Copy code

TARGET_SPEED=80
The train will now try to accelerate and brake to maintain a speed of 80 km/h.

Changing Speed Tolerance
The SPEED_TOLERANCE variable controls how much variance is allowed around the target speed. This is also set in km/h.

For example, to allow a wider range of 10 km/h around the target speed:

Copy code

SPEED_TOLERANCE=10
Tuning the PID Controller
The KP, KI, and KD variables control the proportional, integral, and derivative gains of the PID controller.

Increasing KP gives a stronger proportional response to speed changes.

Increasing KI causes the controller to respond more strongly if speed deviates over time.

Increasing KD causes the controller to respond more quickly to changes.

Tuning these gains allows customizing how aggressively the controller maintains speed and how quickly it responds to changes.

For example:

Copy code

KP=1.5
KI=0.2
KD=0.3
So in summary, the main environment variables to adjust speed are:

TARGET_SPEED: Set point
SPEED_TOLERANCE: Allowed variance
KP/KI/KD: Controller gains
By tuning these you can customize the speed profile and dynamics of the simulated train.