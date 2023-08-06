import asyncio
import logging
from asyncua import Server
from random import randint, uniform, choice

# Setup logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
_logger = logging.getLogger("asyncua")

class CruiseServiceSimulator:
    def __init__(self):
        self.server = Server()
        self.endpoint = "opc.tcp://0.0.0.0:4840/freeopcua/server/"
        
    async def initialize_services(self):
        await self.server.init()
        self.server.set_endpoint(self.endpoint)
        
        # setup our own namespace
        uri = "http://examples.freeopcua.github.io"
        self.namespace_index = await self.server.register_namespace(uri)

        # add engine room object to the server
        self.root = await self.server.nodes.objects.add_object(self.namespace_index, "EngineRoom")

        # Restaurant names and initial settings
        self.restaurant_names = ["Le Gourmet", "Ocean's Delight", "Nautical Bites", "Deck Dining", "Mariner's Munchies"]
        self.restaurant_name = choice(self.restaurant_names)
        self.restaurant_name_node = await self.root.add_variable(self.namespace_index, "RestaurantName", self.restaurant_name)
        self.restaurant_occupancy = await self.root.add_variable(self.namespace_index, "RestaurantOccupancy", 50)

        # Pool locations and initial settings
        self.pool_locations = ["Front Deck", "Rear Deck", "Mid-Ship", "Starboard Side", "Port Side"]
        self.pool_location = choice(self.pool_locations)
        self.pool_location_node = await self.root.add_variable(self.namespace_index, "PoolLocation", self.pool_location)
        self.pool_temperature = await self.root.add_variable(self.namespace_index, "PoolTemperature", 28.0)

        await self.restaurant_name_node.set_writable()
        await self.restaurant_occupancy.set_writable()
        await self.pool_location_node.set_writable()
        await self.pool_temperature.set_writable()

        _logger.info(f"Services initialized with Restaurant: {self.restaurant_name} and Pool Location: {self.pool_location}")

    async def simulate_services(self):
        # Simulate random changes in restaurant occupancy and pool temperature
        restaurant_change = randint(-5, 5)
        
        new_occupancy = await self.restaurant_occupancy.read_value() + restaurant_change
        new_occupancy = max(0, min(100, new_occupancy))
        await self.restaurant_occupancy.set_value(new_occupancy)

        pool_temp_change = uniform(-0.5, 0.5)
        new_temperature = await self.pool_temperature.read_value() + pool_temp_change
        await self.pool_temperature.set_value(new_temperature)

        _logger.info(f"Updated Restaurant Occupancy: {new_occupancy}% and Pool Temperature: {new_temperature:.2f}°C")
        await asyncio.sleep(5)

    async def run(self):
        await self.initialize_services()
        
        async with self.server:
            while True:
                await self.simulate_services()
                await asyncio.sleep(1)

if __name__ == "__main__":
    simulator = CruiseServiceSimulator()
    asyncio.run(simulator.run())
