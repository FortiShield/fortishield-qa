import argparse
import logging
from datetime import datetime
from os import makedirs
from os.path import join
from signal import signal, SIGTERM, SIGINT
from tempfile import gettempdir
from time import time

from fortishield_testing.tools.performance.statistic import StatisticMonitor, logger

METRICS_FOLDER = join(gettempdir(), 'fortishield_statistics')
CURRENT_SESSION = join(METRICS_FOLDER, datetime.now().strftime('%d-%m-%Y'), str(int(time())))
MONITOR_LIST = []


def shutdown_threads(signal_number, frame):
    logger.info('Attempting to shutdown all monitor threads')
    for monitor in MONITOR_LIST:
        monitor.shutdown()
    logger.info('Process finished')


def get_script_arguments():
    parser = argparse.ArgumentParser(usage="%(prog)s [options]", description="Fortishield statistics collector",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-t', '--target', dest='target_list', required=True, type=str, nargs='+', action='store',
                        help='Type the statistics target to collect separated by whitespace. '
                             'Targets: agent, logcollector, remote and analysis.')
    parser.add_argument('-s', '--sleep', dest='sleep_time', type=float, default=5, action='store',
                        help='Type the time in seconds between each entry.')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true', default=False,
                        help='Enable debug level logging.')
    parser.add_argument('--store', dest='store_path', action='store', default=gettempdir(),
                        help=f"Path to store the CSVs with the data. Default {gettempdir()}.")

    return parser.parse_args()


def main():
    signal(SIGTERM, shutdown_threads)
    signal(SIGINT, shutdown_threads)

    options = get_script_arguments()

    makedirs(CURRENT_SESSION)
    logging.basicConfig(filename=join(METRICS_FOLDER, 'fortishield-statistics.log'), filemode='a',
                        format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y/%m/%d %H:%M:%S',
                        level=logging.INFO)
    options.debug and logger.setLevel(logging.DEBUG)
    logger.info(f'Started new session: {CURRENT_SESSION}')

    for target in options.target_list:
        monitor = StatisticMonitor(target=target, time_step=options.sleep_time, dst_dir=options.store_path)
        monitor.start()
        MONITOR_LIST.append(monitor)


if __name__ == '__main__':
    main()
