#!/usr/local/bin/python
"""Main app module
"""

import time
import sys
import os

import logs
import conf
import structlog

from conf import Configuration
from exchange import ExchangeInterface
from notification import Notifier
from behaviour import Behaviour
from web_interface import WebInterface

def main():
    """Initializes the application
    """
     # Load settings and create the config object
    config = Configuration()
    settings = config.settings

    # Set up logger
    logs.configure_logging(settings['log_level'], settings['log_mode'])
    logger = structlog.get_logger()

    # Configure and run configured behaviour.
    exchange_interface = ExchangeInterface(config.exchanges)
    notifier = Notifier(config.notifiers)

    behaviour = Behaviour(
        config,
        exchange_interface,
        notifier
    )
    web_interface = None
    if os.getenv('ENABLE_WEB_INTERFACE', 'true').lower() == 'true':
        web_interface = WebInterface(
            settings.get('web_interface_port', 8887),
            config_path=os.getenv('CONFIG_PATH', 'config.yml'),
            state_path=os.getenv('STATE_PATH')
        )
        web_interface.start()

    while True:
        latest = behaviour.run(settings['market_pairs'], settings['output_mode'])
        if web_interface:
            web_interface.update(latest)
        logger.info("Sleeping for %s seconds", settings['update_interval'])
        time.sleep(settings['update_interval'])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
