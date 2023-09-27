import asyncio
import logging
import random
import requests
from asyncua import Server, ua
from aiokafka import AIOKafkaProducer
from prometheus_client import start_http_server, Gauge
import os
import json
from datetime import datetime, timedelta

KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:9092")

train_names = ["Express", "Bullet", "Freight", "Local", "Shinkansen", "Metro", "Monorail", "Maglev", "Intercity", "High-speed"]
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", random.choice(train_names))

# Initialize Prometheus metrics
TRAIN_SPEED_GAUGE = Gauge('train_speed', 'Train Speed')
TRAIN_ACCELERATION_GAUGE = Gauge('train_acceleration', 'Train Acceleration')
TRAIN_BRAKING_GAUGE = Gauge('train_braking', 'Train Braking')
OUTSIDE_TEMP_GAUGE = Gauge('outside_temperature', 'Outside Temperature')
HUMIDITY_GAUGE = Gauge('humidity', 'Humidity')
WIND_SPEED_GAUGE = Gauge('wind_speed', 'Wind Speed')

# Get environment variables
COLLECT_WEATHER_DATA = os.environ.get("COLLECT_WEATHER_DATA", "False").lower() == "true"
OPENWEATHERMAP_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY", "")
CITY_NAME = os.environ.get("CITY_NAME", "")

async def produce_to_kafka(data):
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKER)
    await producer.start()
    try:
        await producer.send(KAFKA_TOPIC, json.dumps(data).encode('utf-8'))
    finally:
        await producer.stop()

async def main():
    _logger = logging.getLogger("asyncua")

    # Start Prometheus server
    start_http_server(8000)

    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # setup our own namespace
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    # add train object to the server
    myobj = await server.nodes.objects.add_object(idx, "Train")

    # add train variables
    train_speed = await myobj.add_variable(idx, "TrainSpeed", 0.0)
    train_acceleration = await myobj.add_variable(idx, "TrainAcceleration", 0.0)
    train_braking = await myobj.add_variable(idx, "TrainBraking", 0.0)

    # add environmental variables
    outside_temp = await myobj.add_variable(idx, "OutsideTemperature", 25.0)
    humidity = await myobj.add_variable(idx, "Humidity", 70.0)
    wind_speed = await myobj.add_variable(idx, "WindSpeed", 15.0)

    # make the variables writable by clients
    await train_speed.set_writable()
    await train_acceleration.set_writable()
    await train_braking.set_writable()
    await outside_temp.set_writable()
    await humidity.set_writable()
    await wind_speed.set_writable()

    _logger.info("Starting server!")

    start_time = datetime.now()

    async with server:
        while True:
            await asyncio.sleep(1)

            current_train_speed = await train_speed.get_value()
            current_train_acceleration = await train_acceleration.get_value()
            current_train_braking = await train_braking.get_value()

            # Update train speed, acceleration, and braking
            new_train_speed = max(min(current_train_speed + current_train_acceleration - current_train_braking, 300.0), 0.0)
            new_train_acceleration = random.uniform(-1.0, 1.0)
            new_train_braking = random.uniform(0.0, 1.0)

            await train_speed.write_value(new_train_speed)
            await train_acceleration.write_value(new_train_acceleration)
            await train_braking.write_value(new_train_braking)

            # Get current time and calculate elapsed time
            current_time = datetime.now()
            elapsed_time = current_time - start_time

            # Retrieve weather data if COLLECT_WEATHER_DATA is True
            if COLLECT_WEATHER_DATA:
                weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY_NAME}&appid={OPENWEATHERMAP_API_KEY}"
                response = requests.get(weather_url)
                if response.status_code == 200:
                    weather_data = response.json()
                    outside_temp_value = weather_data["main"]["temp"] - 273.15  # Convert from Kelvin to Celsius
                    humidity_value = weather_data["main"]["humidity"]
                    wind_speed_value = weather_data["wind"]["speed"]
                else:
                    _logger.warning(f"Failed to retrieve weather data: {response.status_code} {response.reason}")
                    outside_temp_value = await outside_temp.get_value()
                    humidity_value = await humidity.get_value()
                    wind_speed_value = await wind_speed.get_value()
            else:
                outside_temp_value = await outside_temp.get_value()
                humidity_value = await humidity.get_value()
                wind_speed_value = await wind_speed.get_value()

            # Send data to Kafka
            kafka_data = {
                "ElapsedTime": (start_time + elapsed_time).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "TrainSpeed": new_train_speed,
                "TrainAcceleration": new_train_acceleration,
                "TrainBraking": new_train_braking,
                "OutsideTemperature": outside_temp_value,
                "Humidity": humidity_value,
                "WindSpeed": wind_speed_value,
            }

            await produce_to_kafka(kafka_data)

            # Update Prometheus metrics
            TRAIN_SPEED_GAUGE.set(new_train_speed)
            TRAIN_ACCELERATION_GAUGE.set(new_train_acceleration)
            TRAIN_BRAKING_GAUGE.set(new_train_braking)
            OUTSIDE_TEMP_GAUGE.set(outside_temp_value)
            HUMIDITY_GAUGE.set(humidity_value)
            WIND_SPEED_GAUGE.set(wind_speed_value)

            _logger.info(f"Train conditions: Speed={new_train_speed}, Acceleration={new_train_acceleration}, Braking={new_train_braking}")
            _logger.info(f"Environmental conditions: Outside Temperature={outside_temp_value}, Humidity={humidity_value}, Wind Speed={wind_speed_value}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(), debug=True)