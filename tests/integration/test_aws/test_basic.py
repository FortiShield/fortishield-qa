import os

import pytest
from fortishield_testing import TEMPLATE_DIR, TEST_CASES_DIR, global_parameters
from fortishield_testing.modules.aws import event_monitor, local_internal_options  # noqa: F401
from fortishield_testing.tools.configuration import (
    get_test_cases_data,
    load_configuration_template,
)

pytestmark = [pytest.mark.server]


# Generic vars
MODULE = 'basic_test_module'
TEST_DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
CONFIGURATIONS_PATH = os.path.join(TEST_DATA_PATH, TEMPLATE_DIR, MODULE)
TEST_CASES_PATH = os.path.join(TEST_DATA_PATH, TEST_CASES_DIR, MODULE)

# -------------------------------------------- TEST_BUCKET_DEFAULTS ----------------------------------------------------
# Configuration and cases data
t1_configurations_path = os.path.join(CONFIGURATIONS_PATH, 'bucket_configuration_defaults.yaml')
t1_cases_path = os.path.join(TEST_CASES_PATH, 'cases_bucket_defaults.yaml')

# Enabled test configurations
t1_configuration_parameters, t1_configuration_metadata, t1_case_ids = get_test_cases_data(t1_cases_path)
t1_configurations = load_configuration_template(
    t1_configurations_path, t1_configuration_parameters, t1_configuration_metadata
)


@pytest.mark.tier(level=0)
@pytest.mark.parametrize('configuration, metadata', zip(t1_configurations, t1_configuration_metadata), ids=t1_case_ids)
def test_bucket_defaults(
    configuration, metadata, load_fortishield_basic_configuration, set_fortishield_configuration, clean_s3_cloudtrail_db,
    configure_local_internal_options_function, truncate_monitored_files, restart_fortishield_function, file_monitoring
):
    """
    description: The module is invoked with the expected parameters and no error occurs.
    test_phases:
        - setup:
            - Load Fortishield light configuration.
            - Apply ossec.conf configuration changes according to the configuration template and use case.
            - Apply custom settings in local_internal_options.conf.
            - Truncate fortishield logs.
            - Restart fortishield-manager service to apply configuration changes.
        - test:
            - Check in the ossec.log that a line has appeared calling the module with correct parameters.
            - Check in the ossec.log that no errors occurs.
        - teardown:
            - Truncate fortishield logs.
            - Restore initial configuration, both ossec.conf and local_internal_options.conf.
    fortishield_min_version: 4.6.0
    parameters:
        - configuration:
            type: dict
            brief: Get configurations from the module.
        - metadata:
            type: dict
            brief: Get metadata from the module.
        - load_fortishield_basic_configuration:
            type: fixture
            brief: Load basic fortishield configuration.
        - set_fortishield_configuration:
            type: fixture
            brief: Apply changes to the ossec.conf configuration.
        - configure_local_internal_options_function:
            type: fixture
            brief: Apply changes to the local_internal_options.conf configuration.
        - truncate_monitored_files:
            type: fixture
            brief: Truncate fortishield logs.
        - restart_fortishield_daemon_function:
            type: fixture
            brief: Restart the fortishield service.
        - file_monitoring:
            type: fixture
            brief: Handle the monitoring of a specified file.
    assertions:
        - Check in the log that the module was called with correct parameters.
        - Check in the log that no errors occurs.
    input_description:
        - The `configuration_defaults` file provides the module configuration for this test.
        - The `cases_defaults` file provides the test cases.
    """
    parameters = [
        'wodles/aws/aws-s3',
        '--bucket', metadata['bucket_name'],
        '--aws_profile', 'qa',
        '--type', metadata['bucket_type'],
        '--debug', '2'
    ]

    # Check AWS module started
    log_monitor.start(
        timeout=global_parameters.default_timeout,
        callback=event_monitor.callback_detect_aws_module_start,
        error_message='The AWS module did not start as expected',
    ).result()

    # Check command was called correctly
    log_monitor.start(
        timeout=global_parameters.default_timeout,
        callback=event_monitor.callback_detect_aws_module_called(parameters),
        error_message='The AWS module was not called with the correct parameters',
    ).result()

    # Detect any ERROR message
    with pytest.raises(TimeoutError):
        log_monitor.start(
            timeout=global_parameters.default_timeout,
            callback=event_monitor.callback_detect_all_aws_err,
        ).result()


# -------------------------------------------- TEST_CLOUDWATCH_DEFAULTS ------------------------------------------------
# Configuration and cases data
t2_configurations_path = os.path.join(CONFIGURATIONS_PATH, 'cloudwatch_configuration_defaults.yaml')
t2_cases_path = os.path.join(TEST_CASES_PATH, 'cases_cloudwatch_defaults.yaml')

# Enabled test configurations
t2_configuration_parameters, t2_configuration_metadata, t2_case_ids = get_test_cases_data(t2_cases_path)
configurations = load_configuration_template(
    t2_configurations_path, t2_configuration_parameters, t2_configuration_metadata
)


@pytest.mark.tier(level=0)
@pytest.mark.parametrize('configuration, metadata', zip(configurations, t2_configuration_metadata), ids=t2_case_ids)
def test_service_defaults(
    configuration, metadata, load_fortishield_basic_configuration, set_fortishield_configuration, clean_aws_services_db,
    configure_local_internal_options_function, truncate_monitored_files, restart_fortishield_function, file_monitoring
):
    """
    description: The module is invoked with the expected parameters and no error occurs.
    test_phases:
        - setup:
            - Load Fortishield light configuration.
            - Apply ossec.conf configuration changes according to the configuration template and use case.
            - Apply custom settings in local_internal_options.conf.
            - Truncate fortishield logs.
            - Restart fortishield-manager service to apply configuration changes.
        - test:
            - Check in the ossec.log that a line has appeared calling the module with correct parameters.
            - Check in the ossec.log that no errors occurs.
        - teardown:
            - Truncate fortishield logs.
            - Restore initial configuration, both ossec.conf and local_internal_options.conf.
    fortishield_min_version: 4.6.0
    parameters:
        - configuration:
            type: dict
            brief: Get configurations from the module.
        - metadata:
            type: dict
            brief: Get metadata from the module.
        - load_fortishield_basic_configuration:
            type: fixture
            brief: Load basic fortishield configuration.
        - set_fortishield_configuration:
            type: fixture
            brief: Apply changes to the ossec.conf configuration.
        - clean_aws_services_db:
            type: fixture
            brief: Delete the DB file before and after the test execution.
        - configure_local_internal_options_function:
            type: fixture
            brief: Apply changes to the local_internal_options.conf configuration.
        - truncate_monitored_files:
            type: fixture
            brief: Truncate fortishield logs.
        - restart_fortishield_daemon_function:
            type: fixture
            brief: Restart the fortishield service.
        - file_monitoring:
            type: fixture
            brief: Handle the monitoring of a specified file.
    assertions:
        - Check in the log that the module was called with correct parameters.
        - Check in the log that no errors occurs.
    input_description:
        - The `configuration_defaults` file provides the module configuration for this test.
        - The `cases_defaults` file provides the test cases.
    """
    log_groups = metadata.get('log_group_name')

    parameters = [
        'wodles/aws/aws-s3',
        '--service', metadata['service_type'],
        '--aws_profile', 'qa',
        '--regions', 'us-east-1',
        '--aws_log_groups', log_groups,
        '--debug', '2'
    ]

    # Check AWS module started
    log_monitor.start(
        timeout=global_parameters.default_timeout,
        callback=event_monitor.callback_detect_aws_module_start,
        error_message='The AWS module did not start as expected',
    ).result()

    # Check command was called correctly
    log_monitor.start(
        timeout=global_parameters.default_timeout,
        callback=event_monitor.callback_detect_aws_module_called(parameters),
        error_message='The AWS module was not called with the correct parameters',
    ).result()

    # Detect any ERROR message
    with pytest.raises(TimeoutError):
        log_monitor.start(
            timeout=global_parameters.default_timeout,
            callback=event_monitor.callback_detect_all_aws_err,
        ).result()


# ------------------------------------------ TEST_INSPECTOR_DEFAULTS ---------------------------------------------------
# Configuration and cases data
t3_configurations_path = os.path.join(CONFIGURATIONS_PATH, 'inspector_configuration_defaults.yaml')
t3_cases_path = os.path.join(TEST_CASES_PATH, 'cases_inspector_defaults.yaml')

# Enabled test configurations
t3_configuration_parameters, t3_configuration_metadata, t3_case_ids = get_test_cases_data(t3_cases_path)
configurations = load_configuration_template(
    t3_configurations_path, t3_configuration_parameters, t3_configuration_metadata
)


@pytest.mark.tier(level=0)
@pytest.mark.parametrize('configuration, metadata', zip(configurations, t3_configuration_metadata), ids=t3_case_ids)
def test_inspector_defaults(
    configuration, metadata, load_fortishield_basic_configuration, set_fortishield_configuration, clean_aws_services_db,
    configure_local_internal_options_function, truncate_monitored_files, restart_fortishield_function, file_monitoring
):
    """
    description: The module is invoked with the expected parameters and no error occurs.
    test_phases:
        - setup:
            - Load Fortishield light configuration.
            - Apply ossec.conf configuration changes according to the configuration template and use case.
            - Apply custom settings in local_internal_options.conf.
            - Truncate fortishield logs.
            - Restart fortishield-manager service to apply configuration changes.
        - test:
            - Check in the ossec.log that a line has appeared calling the module with correct parameters.
            - Check in the ossec.log that no errors occurs.
        - teardown:
            - Truncate fortishield logs.
            - Restore initial configuration, both ossec.conf and local_internal_options.conf.
    fortishield_min_version: 4.6.0
    parameters:
        - configuration:
            type: dict
            brief: Get configurations from the module.
        - metadata:
            type: dict
            brief: Get metadata from the module.
        - load_fortishield_basic_configuration:
            type: fixture
            brief: Load basic fortishield configuration.
        - set_fortishield_configuration:
            type: fixture
            brief: Apply changes to the ossec.conf configuration.
        - clean_aws_services_db:
            type: fixture
            brief: Delete the DB file before and after the test execution.
        - configure_local_internal_options_function:
            type: fixture
            brief: Apply changes to the local_internal_options.conf configuration.
        - truncate_monitored_files:
            type: fixture
            brief: Truncate fortishield logs.
        - restart_fortishield_daemon_function:
            type: fixture
            brief: Restart the fortishield service.
        - file_monitoring:
            type: fixture
            brief: Handle the monitoring of a specified file.
    assertions:
        - Check in the log that the module was called with correct parameters.
        - Check in the log that no errors occurs.
    input_description:
        - The `configuration_defaults` file provides the module configuration for this test.
        - The `cases_defaults` file provides the test cases.
    """

    parameters = [
        'wodles/aws/aws-s3',
        '--service', metadata['service_type'],
        '--aws_profile', 'qa',
        '--regions', 'us-east-1',
        '--debug', '2'
    ]

    # Check AWS module started
    log_monitor.start(
        timeout=global_parameters.default_timeout,
        callback=event_monitor.callback_detect_aws_module_start,
        error_message='The AWS module did not start as expected',
    ).result()

    # Check command was called correctly
    log_monitor.start(
        timeout=global_parameters.default_timeout,
        callback=event_monitor.callback_detect_aws_module_called(parameters),
        error_message='The AWS module was not called with the correct parameters',
    ).result()

    # Detect any ERROR message
    with pytest.raises(TimeoutError):
        log_monitor.start(
            timeout=global_parameters.default_timeout,
            callback=event_monitor.callback_detect_all_aws_err,
        ).result()
