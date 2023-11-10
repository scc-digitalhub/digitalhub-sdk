FROM python:3.10-slim

# Repo info
LABEL org.opencontainers.image.source=https://github.com/scc-digitalhub/digitalhub-core

# Set working dir
WORKDIR /digitalhub-core/

# Copy and install sdk-dbt and sdk
COPY ./sdk ./lib
RUN chmod -R 775 /digitalhub-core/lib
RUN pip3 install -e ./lib/modules/sdk-dbt
RUN pip3 install -e ./lib

# Copy wrapper and set entry point
COPY wrapper.py /digitalhub-core/

# Create the new user and set it as the default user
RUN adduser --disabled-password --gecos "" dhcore
RUN chown -R dhcore: /digitalhub-core
USER dhcore

ENTRYPOINT ["python", "wrapper.py"]