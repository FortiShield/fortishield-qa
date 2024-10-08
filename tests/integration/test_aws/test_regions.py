import os

import pytest
from fortishield_testing import T_10, T_20, TEMPLATE_DIR, TEST_CASES_DIR, global_parameters
from fortishield_testing.modules.aws import (  # noqa: F401
    AWS_SERVICES_DB_PATH,
    RANDOM_ACCOUNT_ID,
    event_monitor,
    local_internal_options
)
from fortishield_testing.modules.aws.db_utils import (
    get_multiple_s3_db_row,
    get_multiple_service_db_row,
    s3_db_exists,
    table_exists_or_has_values,
)
from fortishield_testing.tools.configuration import (
    get_test_cases_data,
    load_configuration_template,
)

pytestmark = [pytest.mark.server]


# Generic vars
MODULE = 'regions_test_module'
TEST_DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
CONFIGURATIONS_PATH = os.path.join(TEST_DATA_PATH, TEMPLATE_DIR, MODULE)
TEST_CASES_PATH = os.path.join(TEST_DATA_PATH, TEST_CASES_DIR, MODULE)

# ---------------------------------------------------- TEST_PATH -------------------------------------------------------
t1_configurations_path = os.path.join(CONFIGURATIONS_PATH, 'bucket_configuration_regions.yaml')
t1_cases_path = os.path.join(TEST_CASES_PATH, 'cases_bucket_regions.yaml')

t1_configuration_parameters, t1_configuration_metadata, t1_case_ids = get_test_cases_data(t1_cases_path)
t1_configurations = load_configuration_template(
    t1_configurations_path, t1_configuration_parameters, t1_configuration_metadata
)


@pytest.mark.tier(level=0)
@pytest.mark.parametrize('configuration, metadata', zip(t1_configurations, t1_configuration_metadata), ids=t1_case_ids)
def test_regions(
    configuration, metadata, load_fortishield_basic_configuration, set_fortishield_configuration, clean_s3_cloudtrail_db,
    configure_local_internal_options_function, truncate_monitored_files, restart_fortishield_function, file_monitoring
):
    """
    description: Only the logs for the specified region are processed.
    test_phases:
        - setup:
            - Load Fortishield light configuration.
            - Apply ossec.conf configuration changes according to the configuration template and use case.
            - Apply custom settings in local_internal_options.conf.
            - Truncate fortishield logs.
            - Restart fortishield-manager service to apply configuration changes.
        - test:
            - Check in the ossec.log that a line has appeared calling the module with correct parameters.
            - If a region that does not exist was specified, make sure that a message is displayed in the ossec.log
              warning the user.
            - Check the expected number of events were forwarded to analysisd, only logs stored in the bucket
              for the specified region.
            - Check the database was created and updated accordingly.
        - teardown:
            - Truncate fortishield logs.
            - Restore initial configuration, both ossec.conf and local_internal_options.conf.
            - Delete the uploaded file.
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
        - clean_s3_cloudtrail_db:
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
        - Check the expected number of events were forwarded to analysisd.
        - Check the database was created and updated accordingly, using the correct path for each entry.
    input_description:
        - The `configuration_regions` file provides the module configuration for this test.
        - The `cases_regions` file provides the test cases.
    """
    bucket_name = metadata['bucket_name']
    bucket_type = metadata['bucket_type']
    only_logs_after = metadata['only_logs_after']
    regions = metadata['regions']
    expected_results = metadata['expected_results']
    pattern = fr".*DEBUG: \+\+\+ No logs to process in bucket: {RANDOM_ACCOUNT_ID}/{regions}"

    parameters = [
        'wodles/aws/aws-s3',
        '--bucket', bucket_name,
        '--aws_profile', 'qa',
        '--only_logs_after', only_logs_after,
        '--regions', regions,
        '--type', bucket_type,
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

    if expected_results:
        log_monitor.start(
            timeout=T_20,
            callback=event_monitor.callback_detect_event_processed,
            error_message='The AWS module did not process the expected number of events',
            accum_results=expected_results
        ).result()
    else:
        with pytest.raises(TimeoutError):
            log_monitor.start(
                timeout=global_parameters.default_timeout,
                callback=event_monitor.callback_detect_event_processed,
            ).result()

        log_monitor.start(
            timeout=T_10,
            callback=event_monitor.make_aws_callback(pattern),
            error_message='The AWS module did not show correct message about non-existent region'
        ).result()

    assert s3_db_exists()

    if expected_results:
        regions_list = regions.split(",")
        for row in get_multiple_s3_db_row(table_name=bucket_type):
            if hasattr(row, "aws_region"):
                assert row.aws_region in regions_list
            else:
                assert row.log_key.split("/")[3] in regions_list
    else:
        assert not table_exists_or_has_values(table_name=bucket_type)


# -------------------------------------------- TEST_CLOUDWATCH_REGIONS -------------------------------------------------
t2_configurations_path = os.path.join(CONFIGURATIONS_PATH, 'cloudwatch_configuration_regions.yaml')
t2_cases_path = os.path.join(TEST_CASES_PATH, 'cases_cloudwatch_regions.yaml')

t2_configuration_parameters, t2_configuration_metadata, t2_case_ids = get_test_cases_data(t2_cases_path)
configurations = load_configuration_template(
    t2_configurations_path, t2_configuration_parameters, t2_configuration_metadata
)


@pytest.mark.tier(level=0)
@pytest.mark.parametrize('configuration, metadata', zip(configurations, t2_configuration_metadata), ids=t2_case_ids)
def test_cloudwatch_regions(
    configuration, metadata, load_fortishield_basic_configuration, set_fortishield_configuration, clean_aws_services_db,
    configure_local_internal_options_function, truncate_monitored_files, restart_fortishield_function, file_monitoring
):
    """
    description: Only the logs for the specified region are processed.
    test_phases:
        - setup:
            - Load Fortishield light configuration.
            - Apply ossec.conf configuration changes according to the configuration template and use case.
            - Apply custom settings in local_internal_options.conf.
            - Truncate fortishield logs.
            - Restart fortishield-manager service to apply configuration changes.
        - test:
            - Check in the ossec.log that a line has appeared calling the module with correct parameters.
            - If a region that does not exist was specified, make sure that a message is displayed in the ossec.log
              warning the user.
            - Check the expected number of events were forwarded to analysisd, only logs stored in the bucket
              for the specified region.
            - Check the database was created and updated accordingly.
        - teardown:
            - Truncate fortishield logs.
            - Restore initial configuration, both ossec.conf and local_internal_options.conf.
            - Delete the uploaded file.
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
        - Check the expected number of events were forwarded to analysisd.
        - Check the database was created and updated accordingly, using the correct path for each entry.
    input_description:
        - The `configuration_regions` file provides the module configuration for this test.
        - The `cases_regions` file provides the test cases.
    """
    service_type = metadata['service_type']
    log_group_name = metadata.get('log_group_name')
    only_logs_after = metadata['only_logs_after']
    regions: str = metadata['regions']
    expected_results = metadata['expected_results']
    regions_list = regions.split(",")

    parameters = [
        'wodles/aws/aws-s3',
        '--service', service_type,
        '--aws_profile', 'qa',
        '--only_logs_after', only_logs_after,
        '--regions', regions,
        '--aws_log_groups', log_group_name,
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

    if expected_results:
        log_monitor.start(
            timeout=T_20,
            callback=event_monitor.callback_detect_service_event_processed(expected_results, service_type),
            error_message='The AWS module did not process the expected number of events',
            accum_results=len(regions_list)
        ).result()
    else:
        pattern = (
            r'DEBUG: \+\+\+ \d+ events collected and processed in' if service_type == 'inspector'
            else r'DEBUG: \+\+\+ Sent \d+ events to Analysisd'
        )
        with pytest.raises(TimeoutError):
            log_monitor.start(
                timeout=global_parameters.default_timeout,
                callback=event_monitor.make_aws_callback(pattern),
            ).result()

        log_monitor.start(
            timeout=global_parameters.default_timeout,
            callback=event_monitor.make_aws_callback(
                fr".*\+\+\+ ERROR: The region '{regions}' is not a valid one."
            ),
            error_message='The AWS module did not show correct message non-existent region'
        ).result()

    table_name = 'cloudwatch_logs'

    if expected_results:
        assert table_exists_or_has_values(table_name=table_name, db_path=AWS_SERVICES_DB_PATH)
        for row in get_multiple_service_db_row(table_name=table_name):
            assert (getattr(row, 'region', None) or getattr(row, 'aws_region')) in regions_list
    else:
        assert not table_exists_or_has_values(table_name=table_name, db_path=AWS_SERVICES_DB_PATH)


# ------------------------------------------ TEST_INSPECTOR_PATH -------------------------------------------------------
t3_configurations_path = os.path.join(CONFIGURATIONS_PATH, 'inspector_configuration_regions.yaml')
t3_cases_path = os.path.join(TEST_CASES_PATH, 'cases_inspector_regions.yaml')

t3_configuration_parameters, t3_configuration_metadata, t3_case_ids = get_test_cases_data(t3_cases_path)
configurations = load_configuration_template(
    t3_configurations_path, t3_configuration_parameters, t3_configuration_metadata
)


@pytest.mark.tier(level=0)
@pytest.mark.parametrize('configuration, metadata', zip(configurations, t3_configuration_metadata), ids=t3_case_ids)
def test_inspector_regions(
    configuration, metadata, load_fortishield_basic_configuration, set_fortishield_configuration, clean_aws_services_db,
    configure_local_internal_options_function, truncate_monitored_files, restart_fortishield_function, file_monitoring
):
    """
    description: Only the logs for the specified region are processed.
    test_phases:
        - setup:
            - Load Fortishield light configuration.
            - Apply ossec.conf configuration changes according to the configuration template and use case.
            - Apply custom settings in local_internal_options.conf.
            - Truncate fortishield logs.
            - Restart fortishield-manager service to apply configuration changes.
        - test:
            - Check in the ossec.log that a line has appeared calling the module with correct parameters.
            - If a region that does not exist was specified, make sure that a message is displayed in the ossec.log
              warning the user.
            - Check the expected number of events were forwarded to analysisd, only logs stored in the bucket
              for the specified region.
            - Check the database was created and updated accordingly.
        - teardown:
            - Truncate fortishield logs.
            - Restore initial configuration, both ossec.conf and local_internal_options.conf.
            - Delete the uploaded file.
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
        - Check the expected number of events were forwarded to analysisd.
        - Check the database was created and updated accordingly, using the correct path for each entry.
    input_description:
        - The `configuration_regions` file provides the module configuration for this test.
        - The `cases_regions` file provides the test cases.
    """
    service_type = metadata['service_type']
    only_logs_after = metadata['only_logs_after']
    regions: str = metadata['regions']
    expected_results = metadata['expected_results']
    regions_list = regions.split(",")

    parameters = [
        'wodles/aws/aws-s3',
        '--service', service_type,
        '--aws_profile', 'qa',
        '--only_logs_after', only_logs_after,
        '--regions', regions,
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

    if expected_results:
        log_monitor.start(
            timeout=T_20,
            callback=event_monitor.callback_detect_service_event_processed(expected_results, service_type),
            error_message='The AWS module did not process the expected number of events',
            accum_results=len(regions_list)
        ).result()
    else:
        pattern = (
            r'DEBUG: \+\+\+ \d+ events collected and processed in' if service_type == 'inspector'
            else r'DEBUG: \+\+\+ Sent \d+ events to Analysisd'
        )
        with pytest.raises(TimeoutError):
            log_monitor.start(
                timeout=global_parameters.default_timeout,
                callback=event_monitor.make_aws_callback(pattern),
            ).result()

        log_monitor.start(
            timeout=global_parameters.default_timeout,
            callback=event_monitor.make_aws_callback(
                fr".*\+\+\+ ERROR: The region '{regions}' is not a valid one."
            ),
            error_message='The AWS module did not show correct message non-existent region'
        ).result()

    table_name = 'aws_services'

    if expected_results:
        assert table_exists_or_has_values(table_name=table_name, db_path=AWS_SERVICES_DB_PATH)
        for row in get_multiple_service_db_row(table_name=table_name):
            assert (getattr(row, 'region', None) or getattr(row, 'aws_region')) in regions_list
    else:
        assert not table_exists_or_has_values(table_name=table_name, db_path=AWS_SERVICES_DB_PATH)
