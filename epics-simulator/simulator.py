import time
import asyncio
import numpy as np
from aioca import caput

# Define PV names
bi_pvs = [f"BI_{i}" for i in range(500)]
ai_pvs = [f"AI_{i}" for i in range(20)]
wf_pvs = [f"WF_{i}" for i in range(50)]


async def update_bi():
    while True:
        tasks = [caput(pv, np.random.randint(0, 2)) for pv in bi_pvs]
        await asyncio.gather(*tasks)
        await asyncio.sleep(1)  # 1 Hz


async def update_ai():
    while True:
        tasks = [caput(pv, np.random.uniform(0, 100)) for pv in ai_pvs]
        await asyncio.gather(*tasks)
        await asyncio.sleep(0.5)  # 2 Hz


async def update_waveforms():
    while True:
        tasks = [caput(pv, np.random.uniform(0, 100, 1000).tolist()) for pv in wf_pvs]
        await asyncio.gather(*tasks)
        await asyncio.sleep(0.1)  # 10 Hz


async def main():
    await asyncio.gather(update_bi(), update_ai(), update_waveforms())


if __name__ == "__main__":
    # wait for 5s before starting the simulator
    time.sleep(5)
    # Start the simulator
    print("Starting EPICS simulator...")
    asyncio.run(main())
