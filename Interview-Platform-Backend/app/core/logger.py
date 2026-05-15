import logging
import os

import watchtower
import boto3
from app.core.config import (
    AWS_REGION,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    CLOUDWATCH_LOG_GROUP,
    CLOUDWATCH_LOG_STREAM
)


def setup_logger():

    logger = logging.getLogger(
        "ai-interview-simulator"
    )

    log_level = os.getenv(
        "LOG_LEVEL",
        "INFO"
    ).upper()

    logger.setLevel(
        getattr(
            logging,
            log_level,
            logging.INFO
        )
    )

    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        (
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        )
    )

    # Console logging
    console_handler = logging.StreamHandler()

    console_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        console_handler
    )

    if not all(
        [
            AWS_REGION,
            AWS_ACCESS_KEY_ID,
            AWS_SECRET_ACCESS_KEY,
            CLOUDWATCH_LOG_GROUP,
            CLOUDWATCH_LOG_STREAM
        ]
    ):
        logger.warning(
            "cloudwatch_logging_disabled reason=missing_configuration"
        )
        return logger

    # AWS client
    boto3_client = boto3.client(
        "logs",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

    # CloudWatch logging
    cloudwatch_handler = (
        watchtower.CloudWatchLogHandler(
            boto3_client=boto3_client,
            log_group_name=CLOUDWATCH_LOG_GROUP,
            log_stream_name=CLOUDWATCH_LOG_STREAM
        )
    )

    cloudwatch_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        cloudwatch_handler
    )

    return logger


logger = setup_logger()
