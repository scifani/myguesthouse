FROM   ubuntu:jammy-20231211.1

# Install the necessary packages
RUN apt-get update && \
    apt-get install --no-upgrade --no-install-recommends -y python3 python3-pip tesseract-ocr && \
    rm -rf /var/lib/apt/lists/*

# Copy the source code
COPY ./registration /app/registration
COPY ./resources /app/resources
COPY ./requirements.txt /app/requirements.txt
COPY ./test_main.py /app/test_main.py

RUN pip3 install -r /app/requirements.txt