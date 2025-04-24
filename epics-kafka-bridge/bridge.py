import asyncio
import json
import os

from aioca import camonitor
from aiokafka import AIOKafkaProducer

"""epics-kafka-bridge

Continuously monitors a hard‑coded list of EPICS PVs and publishes every
update to Kafka.  The JSON message layout is aligned with the Go gateway’s
PVMessage struct:

{
  "type": "pv",
  "name": "AI_11",
  "value": 30.38,
  "severity": 0,
  "ok": true,
    "timestamp": 1697055600,
    "units": "mA"
}
"""

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
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

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------


def build_message(pv: str, reading) -> bytes:
    """Convert an aioca reading into the wire‑format expected by the gateway."""
    severity = getattr(reading, "severity", 0)
    msg = {
        "type": "pv",
        "name": pv,
        "value": reading,
        "severity": severity,
        "ok": severity == 0,
        "timestamp": getattr(reading, "timestamp", 0),
        "units": getattr(reading, "units", ""),
    }
    return json.dumps(msg).encode()


# ----------------------------------------------------------------------------
# Main logic
# ----------------------------------------------------------------------------


async def monitor_and_publish(producer: AIOKafkaProducer, pv: str):
    async def pv_callback(reading):
        data = build_message(pv, reading)
        await producer.send_and_wait(topic=pv, value=data)

        print(f"Published update for {pv} -> {data}")

    # Subscribe to the PV with the callback
    subscription = camonitor(pv, pv_callback, format=1, notify_disconnect=True)

    # Keep the subscription active
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        subscription.close()


async def main():
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    try:
        tasks = [monitor_and_publish(producer, pv) for pv in PVS]
        await asyncio.gather(*tasks)
    finally:
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
