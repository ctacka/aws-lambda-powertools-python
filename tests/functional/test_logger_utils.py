import io
import json
import logging
import random
import string
from enum import Enum

import pytest

from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import formatter, utils


@pytest.fixture
def stdout():
    return io.StringIO()


@pytest.fixture
def log_level():
    class LogLevel(Enum):
        NOTSET = 0
        INFO = 20
        WARNING = 30
        CRITICAL = 50

    return LogLevel


@pytest.fixture
def logger(stdout, log_level):
    def _logger():
        logging.basicConfig(stream=stdout, level=log_level.INFO.value)
        return logging.getLogger(name=service_name())

    return _logger


def capture_logging_output(stdout):
    return json.loads(stdout.getvalue().strip())


def capture_multiple_logging_statements_output(stdout):
    return [json.loads(line.strip()) for line in stdout.getvalue().split("\n") if line]


def service_name():
    chars = string.ascii_letters + string.digits
    return "".join(random.SystemRandom().choice(chars) for _ in range(15))


def test_copy_config_to_ext_loggers(stdout, logger, log_level):
    # GIVEN two external loggers and powertools logger initialized
    logger_1 = logger()
    logger_2 = logger()

    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from powertools logger to ALL external loggers
    # AND external loggers used
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger)
    msg = "test message1"
    logger_1.info(msg)
    logger_2.info(msg)
    logs = capture_multiple_logging_statements_output(stdout)

    # THEN all external loggers used Powertools handler, formatter and log level
    for index, logger in enumerate([logger_1, logger_2]):
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert isinstance(logger.handlers[0].formatter, formatter.LambdaPowertoolsFormatter)
        assert logger.level == log_level.INFO.value
        assert logs[index]["message"] == msg
        assert logs[index]["level"] == log_level.INFO.name


def test_copy_config_to_ext_loggers_include(stdout, logger, log_level):
    # GIVEN an external logger and powertools logger initialized
    logger = logger()
    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from powertools logger to INCLUDED external loggers
    # AND our external logger used
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger, include={logger.name})
    msg = "test message2"
    logger.info(msg)
    log = capture_logging_output(stdout)

    # THEN included external loggers used Powertools handler, formatter and log level.
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)
    assert isinstance(logger.handlers[0].formatter, formatter.LambdaPowertoolsFormatter)
    assert logger.level == log_level.INFO.value
    assert log["message"] == msg
    assert log["level"] == log_level.INFO.name


def test_copy_config_to_ext_loggers_wrong_include(stdout, logger, log_level):
    # GIVEN an external logger and powertools logger initialized
    logger = logger()
    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from powertools logger to INCLUDED NON EXISTING external loggers
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger, include={"non-existing-logger"})

    # THEN existing external logger is not modified
    assert not logger.handlers


def test_copy_config_to_ext_loggers_exclude(stdout, logger, log_level):
    # GIVEN an external logger and powertools logger initialized
    logger = logger()
    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from powertools logger to ALL BUT external logger
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger, exclude={logger.name})

    # THEN external logger is not modified
    assert not logger.handlers


def test_copy_config_to_ext_loggers_include_exclude(stdout, logger, log_level):
    # GIVEN two external loggers and powertools logger initialized
    logger_1 = logger()
    logger_2 = logger()

    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from powertools logger to INCLUDED external loggers
    # AND external logger_1 is also in EXCLUDE list
    utils.copy_config_to_registered_loggers(
        source_logger=powertools_logger, include={logger_1.name, logger_2.name}, exclude={logger_1.name}
    )
    msg = "test message3"
    logger_2.info(msg)
    log = capture_logging_output(stdout)

    # THEN logger_1 is not modified and Logger_2 used Powertools handler, formatter and log level
    assert not logger_1.handlers
    assert len(logger_2.handlers) == 1
    assert isinstance(logger_2.handlers[0], logging.StreamHandler)
    assert isinstance(logger_2.handlers[0].formatter, formatter.LambdaPowertoolsFormatter)
    assert logger_2.level == log_level.INFO.value
    assert log["message"] == msg
    assert log["level"] == log_level.INFO.name


def test_copy_config_to_ext_loggers_clean_old_handlers(stdout, logger, log_level):
    # GIVEN an external logger with handler and powertools logger initialized
    logger = logger()
    handler = logging.NullHandler()
    logger.addHandler(handler)
    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from powertools logger to ALL external loggers
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger)

    # THEN old logger's handler removed and Powertools configuration used instead
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)
    assert isinstance(logger.handlers[0].formatter, formatter.LambdaPowertoolsFormatter)


def test_copy_config_to_ext_loggers_custom_log_level(stdout, logger, log_level):
    # GIVEN an external logger and powertools logger initialized
    logger = logger()
    powertools_logger = Logger(service=service_name(), level=log_level.CRITICAL.value, stream=stdout)
    level = log_level.WARNING.name

    # WHEN configuration copied from powertools logger to INCLUDED external logger
    # AND external logger used with custom log_level
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger, include={logger.name}, log_level=level)
    msg = "test message4"
    logger.warning(msg)
    log = capture_logging_output(stdout)

    # THEN external logger used Powertools handler, formatter and CUSTOM log level.
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)
    assert isinstance(logger.handlers[0].formatter, formatter.LambdaPowertoolsFormatter)
    assert powertools_logger.level == log_level.CRITICAL.value
    assert logger.level == log_level.WARNING.value
    assert log["message"] == msg
    assert log["level"] == log_level.WARNING.name


def test_copy_config_to_ext_loggers_should_not_break_append_keys(stdout, log_level):
    # GIVEN powertools logger initialized
    powertools_logger = Logger(service=service_name(), level=log_level.INFO.value, stream=stdout)

    # WHEN configuration copied from powertools logger to ALL external loggers
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger)

    # THEN append_keys should not raise an exception
    powertools_logger.append_keys(key="value")


def test_copy_config_to_ext_loggers_child_loggers_append_before_work(stdout):
    # GIVEN powertools logger AND  child initialized AND

    # GIVEN Loggers are initialized
    # create child logger before parent to mimick
    # importing logger from another module/file
    # as loggers are created in global scope
    service = service_name()
    child = Logger(stream=stdout, service=service, child=True)
    parent = Logger(stream=stdout, service=service)

    # WHEN a child Logger adds an additional key AND parent logger adds additional key
    child.structure_logs(append=True, customer_id="value")
    parent.structure_logs(append=True, user_id="value")
    # WHEN configuration copied from powertools logger
    # AND powertools logger and child logger used
    utils.copy_config_to_registered_loggers(source_logger=parent)
    parent.warning("Logger message")
    child.warning("Child logger message")

    # THEN payment_id key added to both powertools logger and child logger
    parent_log, child_log = capture_multiple_logging_statements_output(stdout)
    assert "customer_id" in parent_log
    assert "customer_id" in child_log
    assert "user_id" in parent_log
    assert "user_id" in child_log
    assert child.parent.name == service


def test_copy_config_to_ext_loggers_child_loggers_append_after_works(stdout):
    # GIVEN powertools logger AND  child initialized AND

    # GIVEN Loggers are initialized
    # create child logger before parent to mimick
    # importing logger from another module/file
    # as loggers are created in global scope
    service = service_name()
    child = Logger(stream=stdout, service=service, child=True)
    parent = Logger(stream=stdout, service=service)

    # WHEN a child Logger adds an additional key AND parent logger adds additional key
    # AND configuration copied from powertools logger
    # AND powertools logger and child logger used
    utils.copy_config_to_registered_loggers(source_logger=parent)
    child.structure_logs(append=True, customer_id="value")
    parent.structure_logs(append=True, user_id="value")
    parent.warning("Logger message")
    child.warning("Child logger message")

    # THEN payment_id key added to both powertools logger and child logger
    parent_log, child_log = capture_multiple_logging_statements_output(stdout)
    assert "customer_id" in parent_log
    assert "customer_id" in child_log
    assert "user_id" in parent_log
    assert "user_id" in child_log
    assert child.parent.name == service


def test_copy_config_to_ext_loggers_no_duplicate_logs(stdout, logger, log_level):
    # GIVEN an root logger, external logger and powertools logger initialized

    root_logger = logging.getLogger()
    handler = logging.StreamHandler(stdout)
    formatter = logging.Formatter('{"message": "%(message)s"}')
    handler.setFormatter(formatter)
    root_logger.handlers = [handler]

    logger = logger()

    powertools_logger = Logger(service=service_name(), level=log_level.CRITICAL.value, stream=stdout)
    level = log_level.WARNING.name

    # WHEN configuration copied from powertools logger
    # AND external logger used with custom log_level
    utils.copy_config_to_registered_loggers(source_logger=powertools_logger, include={logger.name}, log_level=level)
    msg = "test message4"
    logger.warning(msg)

    # THEN no root logger logs AND log is not duplicated
    logs = capture_multiple_logging_statements_output(stdout)
    assert not {"message": msg} in logs
    assert sum(msg in log.values() for log in logs) == 1
