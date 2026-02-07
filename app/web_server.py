"""Standalone web server entrypoint."""

import os
import time

import logs
import structlog

from conf import Configuration
from web_interface import WebInterface


def main():
    config = Configuration()
    settings = config.settings

    logs.configure_logging(settings['log_level'], settings['log_mode'])
    logger = structlog.get_logger()

    web_interface = WebInterface(
        settings.get('web_interface_port', 8887),
        config_path=os.getenv('CONFIG_PATH', 'config.yml'),
        state_path=os.getenv('STATE_PATH')
    )
    web_interface.start()

    while True:
        time.sleep(60)
        logger.debug('Web interface heartbeat')


if __name__ == "__main__":
    main()
