
FROM python:3.9-slim

LABEL name="Community bot container" \
      version="1.0" \
      maintainer="Mikhail Solovyanov <" \
      description="This is the Dockerfile for t.me/how_was_your_day_miksolo_bot app"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/* &&\
    apt-get clean
# Copy the requirements.txt file to the container before copying the rest of the code
COPY requirements.txt /app

RUN pip3 install -r requirements.txt

COPY telegram_bot_app /app

COPY .env /



ENTRYPOINT ["python3", "bot.py"]