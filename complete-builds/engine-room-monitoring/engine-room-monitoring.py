## To-do add weather api and geo spacial data so it can track the weather and location of the ship
import asyncio
import logging
import random
from asyncua import Server, ua
from aiokafka import AIOKafkaProducer
from prometheus_client import start_http_server, Gauge
import os
import json


KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:9092")
ship_names = ["Titanic", "QueenMary", "Olympic", "Lusitania", "Britannic", "Aurora", "Polaris", "Voyager", "Endeavor", "Nautilus"]
KAFKA_TOPIC = random.choice(ship_names)

# Initialize Prometheus metrics
ENGINE_TEMP_GAUGE = Gauge('engine_temperature', 'Engine Temperature')
ENGINE_PRESSURE_GAUGE = Gauge('engine_pressure', 'Engine Pressure')
ENGINE_RPM_GAUGE = Gauge('engine_rpm', 'Engine RPM')
ENGINE_FUEL_CONSUMPTION_GAUGE = Gauge('engine_fuel_consumption', 'Engine Fuel Consumption')
OUTSIDE_TEMP_GAUGE = Gauge('outside_temperature', 'Outside Temperature')
HUMIDITY_GAUGE = Gauge('humidity', 'Humidity')
WIND_SPEED_GAUGE = Gauge('wind_speed', 'Wind Speed')
WAVE_HEIGHT_GAUGE = Gauge('wave_height', 'Wave Height')

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

    # add engine room object to the server
    myobj = await server.nodes.objects.add_object(idx, "EngineRoom")

    # add engine room variables
    engine_temp = await myobj.add_variable(idx, "EngineTemperature", 80.0)
    engine_pressure = await myobj.add_variable(idx, "EnginePressure", 1000.0)
    engine_rpm = await myobj.add_variable(idx, "EngineRPM", 1000.0)
    engine_fuel_consumption = await myobj.add_variable(idx, "EngineFuelConsumption", 200.0)

    # add environmental variables
    outside_temp = await myobj.add_variable(idx, "OutsideTemperature", 25.0)
    humidity = await myobj.add_variable(idx, "Humidity", 70.0)
    wind_speed = await myobj.add_variable(idx, "WindSpeed", 15.0)
    wave_height = await myobj.add_variable(idx, "WaveHeight", 1.0)

    # make the variables writable by clients
    await engine_temp.set_writable()
    await engine_pressure.set_writable()
    await engine_rpm.set_writable()
    await engine_fuel_consumption.set_writable()
    await outside_temp.set_writable()
    await humidity.set_writable()
    await wind_speed.set_writable()
    await wave_height.set_writable()

    _logger.info("Starting server!")

    async with server:
        while True:
            await asyncio.sleep(1)

            current_engine_rpm = await engine_rpm.get_value()
            fuel_increase = current_engine_rpm * 0.001  # adjust this factor to control how much the fuel consumption increases

            new_engine_temp = min(await engine_temp.get_value() + random.uniform(-0.5, 0.5), 120.0)
            new_engine_pressure = max(min(await engine_pressure.get_value() + random.uniform(-10, 10), 1500.0), 0.0)
            new_engine_rpm = max(min(current_engine_rpm + random.uniform(-10, 10), 5000.0), 0.0)
            new_engine_fuel = max(await engine_fuel_consumption.get_value() + fuel_increase, 0.0)

            await engine_temp.write_value(new_engine_temp)
            await engine_pressure.write_value(new_engine_pressure)
            await engine_rpm.write_value(new_engine_rpm)
            await engine_fuel_consumption.write_value(new_engine_fuel)

            new_outside_temp = await outside_temp.get_value() + random.uniform(-1, 1)
            new_humidity = max(min(await humidity.get_value() + random.uniform(-5, 5), 100.0), 0.0)
            new_wind_speed = max(await wind_speed.get_value() + random.uniform(-1, 1), 0.0)
            new_wave_height = max(await wave_height.get_value() + random.uniform(-0.2, 0.2), 0.0)

            await outside_temp.write_value(new_outside_temp)
            await humidity.write_value(new_humidity)
            await wind_speed.write_value(new_wind_speed)
            await wave_height.write_value(new_wave_height)

            # Send data to Kafka
            kafka_data = {
                "EngineTemperature": new_engine_temp,
                "EnginePressure": new_engine_pressure,
                "EngineRPM": new_engine_rpm,
                "EngineFuelConsumption": new_engine_fuel,
                "OutsideTemperature": new_outside_temp,
                "Humidity": new_humidity,
                "WindSpeed": new_wind_speed,
                "WaveHeight": new_wave_height
            }

            await produce_to_kafka(kafka_data)

            # Update Prometheus metrics
            ENGINE_TEMP_GAUGE.set(new_engine_temp)
            ENGINE_PRESSURE_GAUGE.set(new_engine_pressure)
            ENGINE_RPM_GAUGE.set(new_engine_rpm)
            ENGINE_FUEL_CONSUMPTION_GAUGE.set(new_engine_fuel)
            OUTSIDE_TEMP_GAUGE.set(new_outside_temp)
            HUMIDITY_GAUGE.set(new_humidity)
            WIND_SPEED_GAUGE.set(new_wind_speed)
            WAVE_HEIGHT_GAUGE.set(new_wave_height)

            _logger.info(f"Engine room conditions: Temperature={new_engine_temp}, Pressure={new_engine_pressure}, RPM={new_engine_rpm}, Fuel Consumption={new_engine_fuel}")
            _logger.info(f"Environmental conditions: Outside Temperature={new_outside_temp}, Humidity={new_humidity}, Wind Speed={new_wind_speed}, Wave Height={new_wave_height}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(), debug=True)
