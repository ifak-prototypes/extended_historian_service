# -*- coding: utf-8 -*-

"""An example application accessing the Extended Historian Service.
"""

import datetime
from ehs.ehsx import EHSClient
import os.path
import matplotlib
import matplotlib.pyplot as plt
import numpy
import time


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EHS = EHSClient(SCRIPT_DIR)


def run():
    """Use the EHS object to run the services."""

    print(EHS.ping())

    adapter_info_list = EHS.get_adapter_list()
    print(adapter_info_list)
    for adapter_info in adapter_info_list:
        print(adapter_info.can_provide_data)


    cfg = EHS.get_configuration()
    print(cfg)
    print(EHS.set_configuration(cfg))

    channels = EHS.get_channels()
    i = 0
    for c in channels:
        print(f"{i}: {c}")
        i += 1

    values = EHS.get_values([channels[0], channels[1]])
    print(values)


    now = time.time_ns()
    ten_minutes_before = now - 10*60*1_000_000_000  # ... nanoseconds based
    histories = EHS.get_histories([channels[0], channels[1]], ten_minutes_before, now)

    

    # prepare a plotting diagram
    time_series = histories[1]
    t_time_series = numpy.transpose(time_series)
    prep_dates = []
    for t in t_time_series[0]:
        prepdate = datetime.datetime.fromtimestamp(t / 1_000_000_000)
        prep_dates.append(prepdate)
    dates = matplotlib.dates.date2num(prep_dates)

    plt.plot_date(dates, t_time_series[1])
    plt.title("Machine HNA13-ZX23")
    plt.xlabel("Time")
    plt.ylabel("Workload")
    plt.show()

    # prepare a plotting diagram
    histories = EHS.get_histories([channels[4], channels[5]], ten_minutes_before, now)
    time_series = histories[1]
    t_time_series = numpy.transpose(time_series)
    prep_dates = []
    for t in t_time_series[0]:
        prepdate = datetime.datetime.fromtimestamp(t / 1_000_000_000)
        prep_dates.append(prepdate)
    dates = matplotlib.dates.date2num(prep_dates)

    plt.plot_date(dates, t_time_series[1])
    plt.title("Machine AHDev123")
    plt.xlabel("Time")
    plt.ylabel("Workload")
    plt.show()

if __name__ == "__main__":
    run()