import os
import time
from ehs.ehsx import EHSClient

# initialize some variables
script_dir = os.path.dirname(os.path.abspath(__file__))

# initialize EHS
ehs = EHSClient(script_dir)

# get information about channels
channels = ehs.get_channels()

# get current values
values = ehs.get_values([channels[0], channels[1]])

# get time series
now = time.time_ns()
ten_minutes_before = now - 10*60*1_000_000_000  # ... nanoseconds based
histories = ehs.get_histories([channels[0], channels[1]], ten_minutes_before, now)

