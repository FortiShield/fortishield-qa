# Copyright (C) 2015-2021, Wazuh Inc.
# Created by Wazuh, Inc. <info@wazuh.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

import argparse
import os
from datetime import datetime

from wazuh_testing.qa_docs.lib.config import Config
from wazuh_testing.qa_docs.lib.index_data import IndexData
from wazuh_testing.qa_docs.lib.sanity import Sanity
from wazuh_testing.qa_docs.doc_generator import DocGenerator
from wazuh_testing.qa_docs import QADOCS_LOGGER
from wazuh_testing.tools.logging import Logging
from wazuh_testing.tools.exceptions import QAValueError

VERSION = '0.1'
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'qa_docs', 'config.yaml')
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'qa_docs', 'output')
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'qa_docs', 'log')
SEARCH_UI_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'qa_docs', 'search_ui')
qadocs_logger = Logging(QADOCS_LOGGER, 'INFO', True, os.path.join(LOG_PATH,
                        f"{datetime.today().strftime('%Y-%m-%d-%H:%M:%S')}-qa-docs.log"))


def set_qadocs_logger_level(logging_level):
    """Set the QADOCS logger lever depending on the level specified by the user.

    Args:
        logging_level (string): Level used to initialize the logger.
    """
    if logging_level is None:
        qadocs_logger.disable()
    else:
        qadocs_logger.set_level(logging_level)


def validate_parameters(parameters):
    """Validate the parameters that qa-docs recieves.

    Since `config.yaml` will be `schema.yaml`, it runs as config file is correct.
    So we only validate the parameters that the user introduces.

    Args:
        parameters: A list of input args.
    """
    qadocs_logger.debug('Validating input parameters')

    # Check if the directory where the tests are located exist
    if parameters.test_dir:
        if not os.path.exists(parameters.test_dir):
            raise QAValueError(f"{parameters.test_dir} does not exist. Tests directory not found.", qadocs_logger.error)

    # Check that test_input name exists
    if parameters.test_input:
        doc_check = DocGenerator(Config(CONFIG_PATH, parameters.test_dir, test_name=parameters.test_input))
        if doc_check.locate_test() is None:
            raise QAValueError(f"{parameters.test_input} not found.", qadocs_logger.error)

    qadocs_logger.debug('Input parameters validation successfully finished')


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-s', '--sanity-check', action='store_true', dest='sanity',
                        help="Run a sanity check")

    parser.add_argument('-v', '--version', action='store_true', dest="version",
                        help="Print qa-docs version")

    parser.add_argument('-t', action='store_true', dest='test_config',
                        help="Load test configuration.")

    parser.add_argument('-d', action='count', dest='debug_level',
                        help="Enable debug messages.")

    parser.add_argument('-I', dest='test_dir', required=True,
                        help="Path where tests are located.")

    parser.add_argument('-i', '--index-data', dest='index_name',
                        help="Indexes the data named as you specify as argument to elasticsearch.")

    parser.add_argument('-l', '--launch-ui', dest='launch_app',
                        help="Indexes the data named as you specify as argument and launch SearchUI.")

    parser.add_argument('-T', dest='test_input',
                        help="Parse the test that you pass as argument.")

    parser.add_argument('-o', dest='output_path',
                        help="Specifies the output directory for test parsed when -T is used.")

    parser.add_argument('-e', dest='test_exist',
                        help="Checks if test exists or not",)

    args = parser.parse_args()

    # Set the qa-docs logger level
    if args.debug_level:
        set_qadocs_logger_level('DEBUG')

    validate_parameters(args)

    # Print that test gave by the user(using `-e` option) exists or not.
    if args.test_exist:
        doc_check = DocGenerator(Config(CONFIG_PATH, args.test_dir, test_name=args.test_exist))
        if doc_check.locate_test() is not None:
            print("test exists")

    if args.version:
        print(f"qa-docs v{VERSION}")

    # Load configuration if you want to test it
    elif args.test_config:
        qadocs_logger.debug('Loading qa-docs configuration')
        Config(CONFIG_PATH, args.test_dir)
        qadocs_logger.debug('qa-docs configuration loaded')

    # Run a sanity check thru tests directory
    elif args.sanity:
        sanity = Sanity(Config(CONFIG_PATH, args.test_dir, OUTPUT_PATH))
        qadocs_logger.debug('Running sanity check')
        sanity.run()

    # Index the previous parsed tests into Elasticsearch
    elif args.index_name:
        qadocs_logger.debug(f"Indexing {args.index_name}")
        index_data = IndexData(args.index_name, Config(CONFIG_PATH, args.test_dir, OUTPUT_PATH))
        index_data.run()

    # Index the previous parsed tests into Elasticsearch and then launch SearchUI
    elif args.launch_app:
        qadocs_logger.debug(f"Indexing {args.index_name}")
        index_data = IndexData(args.launch_app, Config(CONFIG_PATH, args.test_dir, OUTPUT_PATH))
        index_data.run()
        os.chdir(SEARCH_UI_PATH)
        qadocs_logger.debug('Running SearchUI')
        os.system("ELASTICSEARCH_HOST=http://localhost:9200 npm start")

    # Parse tests
    else:
        if not args.test_exist:
            docs = DocGenerator(Config(CONFIG_PATH, args.test_dir, OUTPUT_PATH))

            # Parse single test
            if args.test_input:
                qadocs_logger.info(f"Parsing the following test(s) {args.test_input}")

                # When output path is specified by user, a json is generated within that path
                if args.output_path:
                    qadocs_logger.info(f"{args.test_input}.json is going to be generated in {args.output_path}")
                    docs = DocGenerator(Config(CONFIG_PATH, args.test_dir, args.output_path, args.test_input))
                else:
                    # When no output is specified, it is printed
                    docs = DocGenerator(Config(CONFIG_PATH, args.test_dir, test_name=args.test_input))
            else:
                qadocs_logger.info(f"Parsing all tests located in {args.test_dir}")

            qadocs_logger.info('Running QADOCS')
            docs.run()

    if __name__ == '__main__':
        main()
