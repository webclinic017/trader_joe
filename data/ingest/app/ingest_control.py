import asyncio
from typing import Any, Coroutine, Dict, List

from kafka import KafkaProducer

from common.enums.data_stock import DataSource
from common.environment import get_env_var
from common.kafka.kafka_tools import (
    flush_messages_async,
    get_producer,
    send_message_async
)
from common.kafka.topics import TopicTyping
from common.logging import get_logger
from common.worker_pool import SharedWorkerPool
from schemas.store_broker_data import DataRequest

from .brokers.alpaca.broker_api import get_market_data as alpaca_market_data

log = get_logger(__name__)

# Configure Kafka Producer
BROKER_NAME = get_env_var("BROKER_NAME")
BROKER_PORT = get_env_var("BROKER_PORT", is_num=True)
BROKER_CONN_TIMEOUT = get_env_var("BROKER_CONN_TIMEOUT", is_num=True)


def verify_code_mapping():
    # TODO on start up verify that all enums are present
    pass


async def send_on_receive(producer: KafkaProducer, data_request: Coroutine[Any, Any, Dict[TopicTyping, List[str]]]):
    topic_map = await data_request
    for topic, data in topic_map.items():
        log.debug("sending to: %s", topic.value)
        send_message_async(SharedWorkerPool.get_instance(), producer, topic.value, data)


def store_retrieve_stock(request: DataRequest):
    producer: KafkaProducer = get_producer(BROKER_NAME, BROKER_PORT, BROKER_CONN_TIMEOUT)
    if request.source is DataSource.ALPACA_API:
        data_request = alpaca_market_data(SharedWorkerPool.get_instance(), request)
        asyncio.create_task(send_on_receive(producer, data_request))
    # TODO Other Brokers
    flush_messages_async(SharedWorkerPool.get_instance(), producer)


def store_retrieve_crypto(request: DataRequest):
    pass


def store_retrieve_option(request: DataRequest):
    pass
