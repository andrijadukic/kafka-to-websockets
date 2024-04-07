import argparse
import json
import time
from dataclasses import dataclass

from confluent_kafka import Producer
from faker import Faker

F = Faker()

VIN_POOL = [
    "5NPDH4AE9DH387622",
    "2D8HN44E49R661441",
    "1GKKRRKD1EJ173860",
    "WBADD6328WGT68767",
    "5GZEV33718J150902"
]

TIRE_POSITIONS = [
    "front-left",
    "front-right",
    "rear-left",
    "rear-right"
]


@dataclass(frozen=True)
class SensorReading:
    timestamp: int
    vin: str
    tire_position: str
    pressure: float
    temperature: float

    @classmethod
    def next_random(cls) -> "SensorReading":
        return cls(
            timestamp=round(time.time() * 1000),
            vin=F.random.choice(VIN_POOL),
            tire_position=F.random.choice(TIRE_POSITIONS),
            pressure=round(F.random.uniform(140, 800), 3),
            temperature=round(F.random.uniform(-10, 70), 3)
        )


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
        data = json.dumps(
            {
                "timestamp": reading.timestamp,
                "vin": reading.vin,
                "tire_position": reading.tire_position,
                "pressure": reading.pressure,
                "temperature": reading.temperature
            }
        )
        producer.produce(args.topic, value=data)
        time.sleep(args.interval)

    producer.flush()


if __name__ == '__main__':
    main()
