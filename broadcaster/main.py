import asyncio

from faststream import FastStream
from faststream.confluent import KafkaBroker, KafkaMessage
from pydantic import AnyUrl
from pydantic_settings import BaseSettings
from websockets import serve, WebSocketServerProtocol


class Settings(BaseSettings):
    bootstrap_servers: AnyUrl = AnyUrl("localhost:9094")
    topics: str
    websocket_port: int = 8080


settings = Settings()

broker = KafkaBroker(bootstrap_servers=str(settings.bootstrap_servers))

CONNECTIONS = set()


async def handler(websocket: WebSocketServerProtocol) -> None:
    CONNECTIONS.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        CONNECTIONS.remove(websocket)


async def decode_message(msg: KafkaMessage) -> bytes:
    return msg.body


@broker.subscriber(settings.topics, decoder=decode_message)
async def broadcast(message: bytes) -> None:
    for client in CONNECTIONS:
        await client.send(message)


async def main():
    async with serve(handler, "localhost", settings.websocket_port):
        app = FastStream(broker)
        await app.run()


if __name__ == "__main__":
    asyncio.run(main())
