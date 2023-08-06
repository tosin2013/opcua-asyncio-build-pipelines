import asyncio
import logging
from asyncua import Server, ua
from random import randint, uniform, choice

# Setup logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CruiseServiceSimulator:
    def __init__(self):
        self.server = Server()
        self.server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
        self.namespace_index = 0  # Will be set during async initialization
        self.root = None  # Will be set during async initialization
        logging.info("CruiseServiceSimulator initialized.")

    async def initialize_services(self):
        self.namespace_index = await self.server.register_namespace("CruiseServices")
        self.root = await self.server.nodes.objects.add_object(self.namespace_index, "CruiseServices")
        
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

        logging.info(f"Services initialized with Restaurant: {self.restaurant_name} and Pool Location: {self.pool_location}")

    async def simulate_services(self):
        while True:
            # Simulate random changes in restaurant occupancy and pool temperature
            restaurant_change = randint(-5, 5)
            pool_temp_change = uniform(-0.5, 0.5)

            new_occupancy = self.restaurant_occupancy.get_value() + restaurant_change
            new_occupancy = max(0, min(100, new_occupancy))
            await self.restaurant_occupancy.set_value(new_occupancy)

            new_temperature = self.pool_temperature.get_value() + pool_temp_change
            await self.pool_temperature.set_value(new_temperature)

            logging.info(f"Updated Restaurant Occupancy: {new_occupancy}% and Pool Temperature: {new_temperature:.2f}°C")
            await asyncio.sleep(5)

    async def run(self):
        await self.initialize_services()
        logging.info("Starting OPC UA server.")

        async with self.server:
            # Continuously update services while the server is running
            while True:
                await self.simulate_services()
                await asyncio.sleep(1)

if __name__ == "__main__":
    simulator = CruiseServiceSimulator()
    asyncio.run(simulator.run())
