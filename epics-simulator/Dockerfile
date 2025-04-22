# Base image setup remains the same
FROM harbor.eli-beams.eu/dockerhub/rockylinux:9

# COPY set_local_mirror.sh .
# RUN chmod u+x set_local_mirror.sh; \
# ./set_local_mirror.sh; \
RUN dnf upgrade --refresh -y; \
    dnf install gcc git make perl -y;  \
    dnf install python3-pip -y; 

RUN mkdir -p /usr/EPICS/epics-base
WORKDIR /usr/EPICS/epics-base
COPY ./base-7.0.8.tar.gz .

RUN tar -xf base-7.0.8.tar.gz --strip-components=1; \
    make

RUN echo "export EPICS_BASE=/usr/EPICS/epics-base" >> /root/.bashrc; \
    echo "export EPICS_HOST_ARCH=\$(\${EPICS_BASE}/startup/EpicsHostArch)" >> /root/.bashrc; \
    echo "export PATH=\${EPICS_BASE}/bin/\${EPICS_HOST_ARCH}:\${PATH}" >> /root/.bashrc

ENV EPICS_BASE=/usr/EPICS/epics-base
ENV EPICS_HOST_ARCH=linux-x86_64
ENV PATH=${EPICS_BASE}/bin/${EPICS_HOST_ARCH}:${PATH}

# Copy the startup script and database file into the container
COPY startup_script.sh /usr/EPICS/startup_script.sh
COPY test.db /usr/EPICS/db/test.db
COPY simulator.py /usr/EPICS/db/simulator.py
COPY requirements.txt /usr/EPICS/db/requirements.txt
RUN chmod +x /usr/EPICS/startup_script.sh
RUN pip3 install --no-cache-dir -r /usr/EPICS/db/requirements.txt


# Use the custom startup script as the entrypoint
ENTRYPOINT ["/usr/EPICS/startup_script.sh"]


