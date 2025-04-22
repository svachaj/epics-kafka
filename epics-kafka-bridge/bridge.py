import asyncio
import json
import os

from aioca.client import Client as EpicsClient
from aiokafka import AIOKafkaProducer

# Hard-coded list of Process Variables (PVs) to monitor
PVS = [
    "AI_0",
    "AI_1",
    "AI_2",
    "AI_3",
    "AI_4",
    "AI_5",
    "AI_6",
    "AI_7",
    "AI_8",
    "AI_9",
    "AI_10",
    # add more PV names here
]

# Kafka bootstrap servers, default to env var or fallback
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")


async def monitor_and_publish(producer: AIOKafkaProducer, pv: str):
    """
    Monitor a single EPICS PV and publish any updates to Kafka.
    Topic name == PV name.
    """
    # Create and initialize EPICS client
    async with EpicsClient() as client:
        monitor = await client.monitor(pv)
        async for reading in monitor:
            # Build payload
            payload = {"pv": pv, "value": reading.value, "timestamp": reading.timestamp}
            # Serialize to JSON bytes
            data = json.dumps(payload).encode("utf-8")
            # Send to Kafka topic named after PV
            await producer.send_and_wait(topic=pv, value=data)
            print(f"Published update for {pv}: {payload}")


async def main():
    # Initialize Kafka producer
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    try:
        # Launch monitor tasks for each PV
        tasks = [monitor_and_publish(producer, pv) for pv in PVS]
        await asyncio.gather(*tasks)
    finally:
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
