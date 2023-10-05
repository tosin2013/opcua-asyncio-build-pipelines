# Train Telemetry Simulator

## Overview
This application simulates a train by generating realistic telemetry data and publishing it to Kafka and Prometheus. It implements a PID controller to regulate the train's speed and acceleration/braking. The train parameters and environment data are also randomized for realistic variability.

* [Code](../complete-builds/mock-railroad/railroad-mocker.py)
* [OpenShift Deployment](https://github.com/tosin2013/edge-anomaly-detection/tree/main/components/applications/mock-railroad/overlays)

## Research Paper
[Anomaly Detection Method in Railway Using Signal Processing and Deep Learning](https://www.mdpi.com/2076-3417/12/24/12901)

## Usage
The app is designed to run in a Docker container. The following environment variables can be configured:

* `KAFKA_BROKER` - Kafka broker URL (default: localhost:9092)
* `KAFKA_TOPIC` - Kafka topic to publish to (default: random train name)
* `TARGET_SPEED` - Target speed for PID controller (mph, default: 60)
* `SPEED_TOLERANCE` - Allowed variance around target speed (mph, default: 5)
* `KP` - PID proportional gain (default: 1.0)
* `KI` - PID integral gain (default: 0.1)
* `KD` - PID derivative gain (default: 0.2)
* `COLLECT_WEATHER_DATA` - Set to True to retrieve live weather data (requires API key, default: False)
* `OPENWEATHERMAP_API_KEY` - API key for OpenWeatherMap
* `CITY_NAME` - City to retrieve weather for
* `DEFAULT_TONNAGE` - Default train tonnage (default: 1000)
  
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
* Train tonnage

Prometheus metrics are exposed on port 8000.

### Here is how you can modify the environment variables to change the speed behavior of the train simulator:

**Changing Target Speed**
The target speed that the PID controller tries to maintain is set by the TARGET_SPEED environment variable.

To change this, set TARGET_SPEED to your desired speed in mph when launching the container.

For example, to set the target speed to 80 mph:
```
TARGET_SPEED=80
```

The train will now try to accelerate and brake to maintain a speed of 80 mph.

Changing Speed Tolerance
The `SPEED_TOLERANCE` variable controls how much variance is allowed around the target speed. This is also set in mph.

For example, to allow a wider range of 10 mph around the target speed:

```
SPEED_TOLERANCE=10
```

**Tuning the PID Controller**

The `KP`, `KI`, and `KD` variables control the proportional, integral, and derivative gains of the `PID` controller.

Increasing `KP` gives a stronger proportional response to speed changes.

Increasing `KI` causes the controller to respond more strongly if speed deviates over time.

Increasing `KD` causes the controller to respond more quickly to changes.

Tuning these gains allows customizing how aggressively the controller maintains speed and how quickly it responds to changes.

For example:
```
KP=1.5
KI=0.2
KD=0.3
```
