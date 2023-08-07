# README

This script simulates the engine room and environmental conditions of a ship. It uses the OPC UA protocol to expose the data to clients, and it also sends the data to a Kafka topic.

## Requirements

* asyncio
* logging
* random
* asyncua
* aiokafka

## Usage

```python
KAFKA_BROKER=your_kafka_broker_address:9092 python3 engine_room_simulator.py
```


The script will create a Kafka topic with the name of the ship. The data will be sent to the topic every second.

You can use a Kafka client to subscribe to the topic and receive the data.

## To-do

* Add Key to kafka producer.
* Add weather api and geo spacial data so it can track the weather and location of the ship.

## Credits

This script was created by Tosin.

## Kafka topics

In order to run this script, you will need to create a Kafka topic for each ship. The name of the topic should be the name of the ship. For example, if the ship is called "Titanic", the topic name should be "Titanic". Change the script if you would like to add ship names.

For each ship in the create a kafka topic 
*  Titanic
*  QueenMary
*  Olympic
*  Lusitania
*  Britannic
*  Aurora
*  Polaris
*  Voyager
*  Endeavor
*  Nautilus


Once you have created the Kafka topic, you can start the script. The script will send the data to the Kafka topic every second. This can be changed by updating the script.

You can use a Kafka client to subscribe to the topic and receive the data.