import argparse
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from modules.allocation import Allocator, models


def parse_arguments():
    parser = argparse.ArgumentParser(description="Infrastructure providing tool")
    parser.add_argument("--provider", required=False, default=None)
    parser.add_argument("--size", required=False, default=None)
    parser.add_argument("--composite-name", required=False, default=None)
    parser.add_argument("--action", required=False, default='create')
    parser.add_argument("--custom-credentials", required=False, default=None)
    parser.add_argument("--track-output", required=False, default='/tmp/wazuh-qa/track.yml')
    parser.add_argument("--inventory-output", required=False, default='/tmp/wazuh-qa/inventory.yml')
    parser.add_argument("--working-dir", required=False, default='/tmp/wazuh-qa')
    return parser.parse_args()


def main():
    Allocator.run(models.InputPayload(**vars(parse_arguments())))


if __name__ == "__main__":
    main()