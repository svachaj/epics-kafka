#!/bin/bash

echo Start python simulator

# Start the Python simulator in the background
python3 /usr/EPICS/db/simulator.py &

echo "Starting EPICS IOC with custom DB"

# Load the database file and initialize the IOC
softIoc -d /usr/EPICS/db/test.db
iocInit
