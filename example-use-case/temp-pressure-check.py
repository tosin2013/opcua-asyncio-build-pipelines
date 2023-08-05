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

    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)
    ns = "ns=2;s=freeopcua.Tags.pressure"
    ns2 = "ns=2;s=freeopcua.Tags.temperature"
    
    min_val = -0.5
    max_val = 0.6

    # populating our address space
    # server.nodes, contains links to very common nodes like objects and root
    myobj = await server.nodes.objects.add_object(idx, "MyObject")
    pressure = await myobj.add_variable(ns, "MyVariable", 10.5)
    temperature = await myobj.add_variable(ns2, "MyVariable", 26.7)
    # Set MyVariable to be writable by clients
    await pressure.set_writable()
    await temperature.set_writable()
    opcs = [ pressure, temperature ]
  
    _logger.info("Starting server!")
    async with server:
        while True:
            await asyncio.sleep(1)
            random_counter = random.uniform(min_val, max_val)
            for opc in opcs:
                new_val = await opc.get_value() + random_counter
                if(new_val>100.0):
                    new_val=100.0
                elif(new_val<0.0):
                    new_val=0.0
                _logger.info("Set value of %s to %.1f", opc, new_val)
                await opc.write_value(new_val)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(), debug=True)