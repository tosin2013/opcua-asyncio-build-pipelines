import asyncio
import logging
import random
from asyncua import Server, ua

async def main():
    _logger = logging.getLogger("asyncua")

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

    # make the variables writable by clients
    await engine_temp.set_writable()
    await engine_pressure.set_writable()
    await engine_rpm.set_writable()
    await engine_fuel_consumption.set_writable()

    _logger.info("Starting server!")
    async with server:
        while True:
            # simulate changing engine room conditions
            await asyncio.sleep(1)
            await engine_temp.write_value(engine_temp.get_value() + random.uniform(-0.5, 0.5))
            await engine_pressure.write_value(max(0, engine_pressure.get_value() + random.uniform(-10, 10)))
            await engine_rpm.write_value(max(0, engine_rpm.get_value() + random.uniform(-10, 10)))
            await engine_fuel_consumption.write_value(max(0, engine_fuel_consumption.get_value() + random.uniform(-1, 1)))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
