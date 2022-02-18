import pytest


MAX_DIFFERENCE_ACK_KEEP_ALIVE = 20


def test_keep_alives(get_report):
    # Agent
    assert get_report['agents']['wazuh-agentd']['max_diff_ack_keep_alive'] < MAX_DIFFERENCE_ACK_KEEP_ALIVE, \
        f"Some agents keep alive interval surpassed {MAX_DIFFERENCE_ACK_KEEP_ALIVE} seconds maximun"

    # Manager
    keep_alives = get_report['managers']['wazuh-remoted']['keep_alives']

    max_differences = [keep_alives[agent]['max_difference'] for agent in keep_alives.keys()]
    assert max(max_differences) < MAX_DIFFERENCE_ACK_KEEP_ALIVE, \
        f"Some managers received keep-alives from agents at an interval that exceeded {MAX_DIFFERENCE_ACK_KEEP_ALIVE}" \
        + 'seconds maximun'
