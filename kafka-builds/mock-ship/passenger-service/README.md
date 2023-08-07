# Passenger Service Simulator

This script simulates the restaurant and pool services of a cruise ship. It uses the OPC UA protocol to expose the data to clients, and it also sends the data to a Kafka topic.

![20230806235744](https://i.imgur.com/Un9iD2M.png)
## Requirements

* asyncio
* logging
* json
* datetime
* os
* asyncua
* aiokafka

## Usage

```python
KAFKA_BROKER=your_kafka_broker_address:9092;  python cruise_service_simulator.py
```

The script will create a Kafka topic named `cruise_service_updates`. The data will be sent to the topic every second.

You can use a Kafka client to subscribe to the topic and receive the data.

## To-do
* Sync with ships found in the engine room monitoring script.

## Kafka topics

In order to run this script, you will need to create a Kafka topic named `cruise_service_updates`. You can do this using the following command:
```
kafka-topics --create --topic cruise_service_updates --bootstrap-server localhost:9092
```

Once you have created the Kafka topic, you can start the script. The script will send the data to the Kafka topic every second.

You can use a Kafka client to subscribe to the topic and receive the data.

## Documentation

The documentation for the OPC UA protocol can be found at: https://opcfoundation.org/UA/

The documentation for the Kafka protocol can be found at: https://kafka.apache.org/documentation/

## Credits

This script was created by Tosin Akinosho.