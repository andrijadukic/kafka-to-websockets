import argparse
import json
import time
import uuid
from dataclasses import dataclass

from confluent_kafka import Producer
from faker import Faker

F = Faker()


@dataclass(frozen=True)
class SensorReading:
    sensorId: str
    temperature: float

    @classmethod
    def next_random(cls) -> "SensorReading":
        return cls(sensorId=str(uuid.uuid4()), temperature=F.random.uniform(-20, 40))


def reading_generator(n: int):
    for i in range(n):
        yield SensorReading.next_random()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap-servers", type=str, default="localhost:9094")
    parser.add_argument("--topic", type=str, default="telemetry")
    parser.add_argument("-n", type=int, default=20)
    parser.add_argument("-i", "--interval", type=float, default=1.0)

    args = parser.parse_args()

    producer = Producer({"bootstrap.servers": args.bootstrap_servers})

    for reading in reading_generator(args.n):
        data = json.dumps({"sensorId": reading.sensorId, "temperature": reading.temperature})
        producer.produce(args.topic, value=data)
        time.sleep(args.interval)

    producer.flush()


if __name__ == '__main__':
    main()
