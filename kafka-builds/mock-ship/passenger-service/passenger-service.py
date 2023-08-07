import asyncio
import logging
import json
import datetime
import os 
from asyncua import Server
from random import randint, uniform, choice
from aiokafka import AIOKafkaProducer

# Setup logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
_logger = logging.getLogger("asyncua")

class CruiseServiceSimulator:
    def __init__(self, kafka_bootstrap_servers):
        self.server = Server()
        self.endpoint = "opc.tcp://0.0.0.0:4840/freeopcua/server/"
        self.kafka_bootstrap_servers = kafka_bootstrap_servers

    async def initialize_services(self):
        await self.server.init()
        self.server.set_endpoint(self.endpoint)
        
        uri = "http://examples.freeopcua.github.io"
        self.namespace_index = await self.server.register_namespace(uri)
        self.root = await self.server.nodes.objects.add_object(self.namespace_index, "EngineRoom")

        self.restaurant_names = ["Le Gourmet", "Ocean's Delight", "Nautical Bites", "Deck Dining", "Mariner's Munchies"]
        self.restaurant_name = choice(self.restaurant_names)
        self.restaurant_name_node = await self.root.add_variable(self.namespace_index, "RestaurantName", self.restaurant_name)
        self.restaurant_occupancy = await self.root.add_variable(self.namespace_index, "RestaurantOccupancy", 50)

        self.pool_locations = ["Front Deck", "Rear Deck", "Mid-Ship", "Starboard Side", "Port Side"]
        self.pool_location = choice(self.pool_locations)
        self.pool_location_node = await self.root.add_variable(self.namespace_index, "PoolLocation", self.pool_location)
        self.pool_temperature = await self.root.add_variable(self.namespace_index, "PoolTemperature", 28.0)

        await self.restaurant_name_node.set_writable()
        await self.restaurant_occupancy.set_writable()
        await self.pool_location_node.set_writable()
        await self.pool_temperature.set_writable()

        _logger.info(f"Services initialized with Restaurant: {self.restaurant_name} and Pool Location: {self.pool_location}")

        # Initialize Kafka producer
        self.producer = AIOKafkaProducer(bootstrap_servers=self.kafka_bootstrap_servers)
        await self.producer.start()

    async def push_to_kafka(self, data: dict):
        kafka_data = {
            "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            "data": data
        }
        # Encode the JSON string to bytes before sending
        await self.producer.send("cruise_service_updates", value=json.dumps(kafka_data).encode('utf-8'))

    async def simulate_services(self):
        restaurant_change = randint(-5, 5)
        new_occupancy = await self.restaurant_occupancy.read_value() + restaurant_change
        new_occupancy = max(0, min(100, new_occupancy))
        await self.restaurant_occupancy.set_value(new_occupancy)

        pool_temp_change = uniform(-0.5, 0.5)
        new_temperature = await self.pool_temperature.read_value() + pool_temp_change
        await self.pool_temperature.set_value(new_temperature)

        _logger.info(f"Updated Restaurant Occupancy: {new_occupancy}% and Pool Temperature: {new_temperature:.2f}°C")

        # Send data to Kafka
        kafka_data = {
            "RestaurantName": self.restaurant_name,
            "RestaurantOccupancy": new_occupancy,
            "PoolLocation": self.pool_location,
            "PoolTemperature": new_temperature
        }
        await self.push_to_kafka(kafka_data)

        await asyncio.sleep(5)

    async def run(self):
        await self.initialize_services()
        async with self.server:
            while True:
                await self.simulate_services()
                await asyncio.sleep(1)

if __name__ == "__main__":
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_ADDRESS", "localhost:9092")
    simulator = CruiseServiceSimulator(KAFKA_BOOTSTRAP_SERVERS)
    asyncio.run(simulator.run())