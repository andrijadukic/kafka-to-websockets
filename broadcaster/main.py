import asyncio
import json
import uuid
from typing import Any
from urllib.parse import parse_qs
from urllib.parse import urlparse

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

CONNECTIONS: dict[WebSocketServerProtocol, dict[str, set]] = {}


async def handler(websocket: WebSocketServerProtocol) -> None:
    """
    The entrypoint into the websocket server.
    Connections are handled by adding them onto an in-memory set for use in the Kafka handler.
    Each call to this method lasts for as long as the client connection exists.

    Args:
        websocket: The object representing the client connection.
    """

    filters = parse_filter_conditions(websocket.path)
    CONNECTIONS[websocket] = filters
    try:
        await websocket.wait_closed()
    finally:
        del CONNECTIONS[websocket]


def parse_filter_conditions(path: str) -> dict[str, set] | None:
    """
    Takes a URL path and returns query parameters as a dictionary, where the values of each individual query
    are kept in a set. If the path doesn't contain a query parameter, None is returned instead.

    Args:
        path: The path part of the URL, potentially containing query parameters.

    Returns:
        A dictionary containing the query keys as keys and the values as values, kept in a set.
    """

    parsed_url = urlparse(path)
    raw_query = parse_qs(parsed_url.query)

    if len(raw_query) == 0:
        return None

    filters = {}
    for field_name, raw_values in raw_query.items():
        values = set()
        for raw_value in raw_values:
            parsed_values = [value.strip() for value in raw_value.split(",")]
            values.update(parsed_values)
        filters[field_name] = values

    return filters


async def decode_message(msg: KafkaMessage) -> tuple[dict[str, Any], bytes]:
    """
    Decodes a KafkaMessage for use in the Kafka handler.
    The message is decoded into a tuple, where the first element is a dictionary (assuming messages are valid JSON).
    The second element is a bytes object (the "raw" contents of the message).
    The motivation for returning both is optimization in the case the message in its original,
    serialized form can be of use (so that users don't need to again serialize into JSON).

    Args:
        msg: The KafkaMessage to decode. The assumption is that the message contents are valid JSON.

    Returns:
        A tuple containing the message deserialized into a dict and the raw message contents as bytes.
    """

    return json.loads(msg.body), msg.body


@broker.subscriber(
    settings.topics,
    group_id=f"websocket-server-consumer-{str(uuid.uuid4())}",
    auto_commit=False,
    decoder=decode_message,
)
async def broadcast(msg: tuple[dict[str, Any], bytes]) -> None:
    """
    The entrypoint into the Kafka handler.
    The handler first evaluates the active websocket connections for those that would be interested in
    receiving the current message, as dictated by the query parameters sent when establishing the connection,
    and then broadcasts the message as-is to all the determined recipients.

    Due to this server only making sense if the established client receives all messages, and the fact
    that a single client (e.g., web application) can only ever be connected to a single server instance,
    the underlying Kafka consumer doesn't use consumer group logic, but simply reads and forwards messages
    received in "real-time". Due to the current lack of support for this in the library that's used for
    interacting with Kafka, this group-less approach is "mimicked" by creating a random consumer group name
    and purposely turning off auto commit. With this approach, the consumer group name will never reach the actual
    broker (so that we don't unnecessarily create a bunch of unneeded consumer groups).

    Args:
        msg: The incoming Kafka message,
        received as a tuple containing the message deserialized into a dict and the raw message contents as bytes.
    """

    recipients = [
        client.send(msg[1])
        for client in determine_recipients(msg=msg[0], candidates=CONNECTIONS)
    ]
    await asyncio.gather(*recipients)


def determine_recipients(
        msg: dict[str, Any], candidates: dict[WebSocketServerProtocol, dict[str, set]]
) -> list[WebSocketServerProtocol]:
    """
    Determines the appropriate recipients for the given message, by looking into the filters for each candidate
    websocket connection. If an existing websocket connection doesn't have a filter defined, it's assumed
    to be "subscribed" to all Kafka messages.

    Args:
        msg: The incoming Kafka message, deserialized into a dict.
        candidates: A dictionary of established websocket connections,
        containing the respective filters for each connection.

    Returns:
        A list of WebSocketServerProtocol objects that are determined to be the appropriate recipients.
    """

    recipients = []
    for client, filters in candidates.items():
        is_recipient = True
        if filters is not None:
            for field_name, values in filters.items():
                if msg[field_name] not in values:
                    is_recipient = False
                    break
        if is_recipient:
            recipients.append(client)
    return recipients


async def main() -> None:
    """
    Entrypoint into the server.
    Spins up the WebSocket server and starts the Kafka handler.
    """
    async with serve(handler, "localhost", settings.websocket_port):
        app = FastStream(broker)
        await app.run()


if __name__ == "__main__":
    asyncio.run(main())
