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
# Constants for realistic behavior
TARGET_SPEED = int(os.environ.get("TARGET_SPEED", 60.0))  # The speed the train tries to maintain
MIN_INITIAL_SPEED = int(os.environ.get("MIN_INITIAL_SPEED", 45.0 )) # Minimum initial speed
MAX_INITIAL_SPEED = int(os.environ.get("MAX_INITIAL_SPEED", 65.0))  # Maximum initial speed
SPEED_TOLERANCE = int(os.environ.get("SPEED_TOLERANCE", 5.00))   # The tolerance around the target speed
MIN_INITIAL_ACCELERATION =  int(os.environ.get("SPEED_TOLERANCE", -5.0))  # Minimum initial acceleration (negative for deceleration)
MAX_INITIAL_ACCELERATION =  int(os.environ.get("SPEED_TOLERANCE", 5.0))   # Maximum initial acceleration
DEFAULT_TONNAGE = float(os.environ.get("DEFAULT_TONNAGE", 1000.0))  # Default train tonnage in tons
TONNAGE_CHANGE_INTERVAL = int(os.environ.get("TONNAGE_CHANGE_INTERVAL", 180))  # Defaults to 3 minutes if not set

# Override with environment variables if available
acceleration_duration = int(os.environ.get("ACCELERATION_DURATION", 300))# Duration of acceleration in seconds (adjust as needed)
acceleration_timer = int(os.environ.get("ACCELERATION_TIMER", 2))  # Timer for acceleration phase

train_names = ["Express", "Bullet", "Freight", "Local", "Shinkansen", "Metro", "Monorail", "Maglev", "Intercity", "High-speed"]
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", random.choice(train_names))

# Initialize Prometheus metrics
TRAIN_SPEED_GAUGE = Gauge('train_speed', 'Train Speed')
TRAIN_ACCELERATION_GAUGE = Gauge('train_acceleration', 'Train Acceleration')
TRAIN_BRAKING_GAUGE = Gauge('train_braking', 'Train Braking')
OUTSIDE_TEMP_GAUGE = Gauge('outside_temperature', 'Outside Temperature')
HUMIDITY_GAUGE = Gauge('humidity', 'Humidity')
WIND_SPEED_GAUGE = Gauge('wind_speed', 'Wind Speed')
PRIMARY_SUSPENSION_STIFFNESS_GAUGE = Gauge('primary_suspension_stiffness', 'Primary Suspension Stiffness')
SECONDARY_SUSPENSION_STIFFNESS_GAUGE = Gauge('secondary_suspension_stiffness', 'Secondary Suspension Stiffness')
DAMPING_RATE_GAUGE = Gauge('damping_rate', 'Damping Rate')
TRAIN_TONNAGE = Gauge('train_tonnage', 'Train Tonnage')

# Get environment variables
COLLECT_WEATHER_DATA = os.environ.get("COLLECT_WEATHER_DATA", "False").lower() == "true"
OPENWEATHERMAP_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY", "")
CITY_NAME = os.environ.get("CITY_NAME", "")

# Define PID controller parameters with default values
kp = float(os.environ.get("KP", 1.0))  # Proportional gain
ki = float(os.environ.get("KI", 0.1))  # Integral gain
kd = float(os.environ.get("KD", 0.2))  # Derivative gain

# Initialize PID controller variables
integral_error = 0.0
previous_error = 0.0


def calculate_primary_suspension_stiffness(speed):
    # Define a linear relationship between speed and primary suspension stiffness
    # Adjust these parameters as needed to match your desired behavior
    stiffness_at_zero_speed = 30000.0  # N/m
    stiffness_at_max_speed = 20000.0  # N/m
    max_speed = 80.0  # Maximum speed in km/h

    # Interpolate the stiffness based on speed
    return stiffness_at_zero_speed + (stiffness_at_max_speed - stiffness_at_zero_speed) * (speed / max_speed)

def calculate_secondary_suspension_stiffness(speed):
    # Define a linear relationship between speed and secondary suspension stiffness
    # Adjust these parameters as needed to match your desired behavior
    stiffness_at_zero_speed = 15000.0  # N/m
    stiffness_at_max_speed = 10000.0  # N/m
    max_speed = 80.0  # Maximum speed in km/h

    # Interpolate the stiffness based on speed
    return stiffness_at_zero_speed + (stiffness_at_max_speed - stiffness_at_zero_speed) * (speed / max_speed)

def calculate_damping_rate(speed):
    # Define a linear relationship between speed and damping rate
    # Adjust these parameters as needed to match your desired behavior
    damping_at_zero_speed = 2000.0  # Ns/m
    damping_at_max_speed = 1000.0  # Ns/m
    max_speed = 80.0  # Maximum speed in km/h

    # Interpolate the damping rate based on speed
    return damping_at_zero_speed + (damping_at_max_speed - damping_at_zero_speed) * (speed / max_speed)


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

    # Generate a random initial speed within the specified range
    initial_speed_int = random.randint(MIN_INITIAL_SPEED, MAX_INITIAL_SPEED)
    initial_acceleration_int = random.randint(MIN_INITIAL_ACCELERATION, MAX_INITIAL_ACCELERATION)

    # Convert the initial speed to a floating-point number
    initial_speed = float(initial_speed_int)
    initial_acceleration = float(initial_acceleration_int)


    # add train variables
    train_speed = await myobj.add_variable(idx, "TrainSpeed", initial_speed)
    train_acceleration = await myobj.add_variable(idx, "TrainAcceleration", initial_acceleration)
    train_braking = await myobj.add_variable(idx, "TrainBraking", 0.0)

    # add environmental variables
    outside_temp = await myobj.add_variable(idx, "OutsideTemperature", 25.0)
    humidity = await myobj.add_variable(idx, "Humidity", 70.0)
    wind_speed = await myobj.add_variable(idx, "WindSpeed", 15.0)
    global integral_error, previous_error, acceleration_timer, acceleration_duration
    # Define realistic train car parameters
    train_mass = 50000.0  # Mass of the train car in kilograms
    train_inertia = 500000.0  # Inertia of the train car in kg*m^2
    train_tonnage = await myobj.add_variable(idx, "TrainTonnage", DEFAULT_TONNAGE)
    


    # Define realistic suspension parameters
    primary_suspension_stiffness = 30000.0  # Primary suspension stiffness in N/m
    secondary_suspension_stiffness = 15000.0  # Secondary suspension stiffness in N/m
    spring_travel = 0.1  # Spring travel in meters
    damping_rate = 2000.0  # Damping rate in Ns/m
    # Add suspension variables
    primary_suspension_stiffness_variable = await myobj.add_variable(idx, "PrimarySuspensionStiffness", primary_suspension_stiffness)
    secondary_suspension_stiffness_variable = await myobj.add_variable(idx, "SecondarySuspensionStiffness", secondary_suspension_stiffness)
    damping_rate_variable = await myobj.add_variable(idx, "DampingRate", damping_rate)

    # make the variables writable by clients
    await train_speed.set_writable()
    await train_acceleration.set_writable()
    await train_braking.set_writable()
    await outside_temp.set_writable()
    await humidity.set_writable()
    await wind_speed.set_writable()
    await primary_suspension_stiffness_variable.set_writable()
    await secondary_suspension_stiffness_variable.set_writable()
    await damping_rate_variable.set_writable()
    await train_tonnage.set_writable()


    _logger.info("Starting server!")

    start_time = datetime.now()

    # Initialize last_tonnage_change_time before entering the while loop
    last_tonnage_change_time = datetime.now()
    first_run = True  # flag to check if it's the first iteration of the loop

    async with server:
        while True:
            await asyncio.sleep(1)

            current_train_speed = await train_speed.get_value()

            # Then, inside your while loop:
            current_time = datetime.now()

            print(f"Current time: {current_time}")
            print(f"Last tonnage change time: {last_tonnage_change_time}")
            print(f"Time difference: {(current_time - last_tonnage_change_time).seconds}")
            print(f"First run: {first_run}")
            if first_run or (current_time - last_tonnage_change_time).seconds >= TONNAGE_CHANGE_INTERVAL:
                update_tonnage = random.uniform(0.8 * DEFAULT_TONNAGE, 1.2 * DEFAULT_TONNAGE)  # Vary tonnage by ±20%
                print(f"Updating tonnage at {current_time}")
                await train_tonnage.write_value(update_tonnage)
                new_tonnage = await train_tonnage.get_value()
                print(f"Updated tonnage to {update_tonnage}")
                last_tonnage_change_time = current_time  # reset the last change time
                first_run = False  # set the flag to False after the first run



            #current_train_acceleration = await train_acceleration.get_value()
            #current_train_braking = await train_braking.get_value()

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

            # Adjusted PID calculation with tonnage factor
            tonnage_factor = DEFAULT_TONNAGE / new_tonnage  # Assuming more tonnage means less acceleration
            current_speed_difference = TARGET_SPEED - current_train_speed
            proportional = kp * current_speed_difference * tonnage_factor
            integral_error += ki * current_speed_difference * tonnage_factor
            derivative_error = kd * (current_speed_difference - previous_error) * tonnage_factor

            # Calculate acceleration and braking
            new_train_acceleration = proportional + integral_error + derivative_error
            new_train_braking = 0  # You can adjust this as needed

             # Check if it's time to accelerate or decelerate
            if acceleration_timer <= acceleration_duration:
                # During acceleration phase, increase speed
                random_acceleration = random.uniform(1.0, 5.0)  # Random positive acceleration
                acceleration_timer += 1
            else:
                # During deceleration phase, decrease speed randomly
                random_acceleration = random.uniform(-1.0, 2.0)  # Random acceleration, can be negative
                # Optionally, reset the acceleration timer to simulate varying intervals
                acceleration_timer = random.randint(300, 600)  # Random duration for next acceleration phase

            # Apply some randomness to the acceleration
            new_train_acceleration = (
                proportional + integral_error + derivative_error + random_acceleration
            )

            # Limit acceleration and braking to reasonable values
            new_train_acceleration = max(min(new_train_acceleration, 1.0), -1.0)
            new_train_braking = max(min(new_train_braking, 1.0), 0.0)

            # Update train speed
            new_train_speed = max(min(current_train_speed + new_train_acceleration - new_train_braking, 80.0), 40.0)
            await train_speed.write_value(new_train_speed)

             # Update suspension stiffness and damping rates based on speed
            primary_suspension_stiffness = calculate_primary_suspension_stiffness(new_train_speed)
            secondary_suspension_stiffness = calculate_secondary_suspension_stiffness(new_train_speed)
            damping_rate = calculate_damping_rate(new_train_speed)

            await primary_suspension_stiffness_variable.write_value(primary_suspension_stiffness)
            await secondary_suspension_stiffness_variable.write_value(secondary_suspension_stiffness)
            await damping_rate_variable.write_value(damping_rate)


            # Update previous error for the next iteration
            previous_error = current_speed_difference

            # Send data to Kafka
            kafka_data = {
                "ElapsedTime": (start_time + elapsed_time).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "TrainSpeed": new_train_speed,
                "TrainAcceleration": new_train_acceleration,
                "TrainBraking": new_train_braking,
                "OutsideTemperature": outside_temp_value,
                "Humidity": humidity_value,
                "WindSpeed": wind_speed_value,
                "PrimarySuspensionStiffness": primary_suspension_stiffness,
                "SecondarySuspensionStiffness": secondary_suspension_stiffness,
                "DampingRate": damping_rate,
                "TrainTonnage": new_tonnage
            }

            await produce_to_kafka(kafka_data)

            # Update Prometheus metrics
            TRAIN_SPEED_GAUGE.set(new_train_speed)
            TRAIN_ACCELERATION_GAUGE.set(new_train_acceleration)
            TRAIN_BRAKING_GAUGE.set(new_train_braking)
            OUTSIDE_TEMP_GAUGE.set(outside_temp_value)
            HUMIDITY_GAUGE.set(humidity_value)
            WIND_SPEED_GAUGE.set(wind_speed_value)
            PRIMARY_SUSPENSION_STIFFNESS_GAUGE.set(primary_suspension_stiffness)
            SECONDARY_SUSPENSION_STIFFNESS_GAUGE.set(secondary_suspension_stiffness)
            DAMPING_RATE_GAUGE.set(damping_rate)
            TRAIN_TONNAGE.set(new_tonnage)

            _logger.info(f"Train conditions: Speed={new_train_speed}, Acceleration={new_train_acceleration}, primary_suspension_stiffness={primary_suspension_stiffness}, secondary_suspension_stiffness={secondary_suspension_stiffness}, damping_rate={damping_rate}, Train Tonnage={new_tonnage}")
            _logger.info(f"Environmental conditions: Outside Temperature={outside_temp_value}, Humidity={humidity_value}, Wind Speed={wind_speed_value}")




if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(), debug=True)
