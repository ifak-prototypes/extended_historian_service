import os
import time
from ehs.ehsx import EHSClient, ChannelAddress

# initialize some variables
script_dir = os.path.dirname(os.path.abspath(__file__))

# initialize EHS
ehs = EHSClient(script_dir)

# get information about channels
channels = ehs.get_channels()
channels = sorted(channels, key=lambda channel: channel.__str__())
for number, channel in enumerate(channels):
    print(number, channel)

# get current values
values = ehs.get_values([channels[4], channels[5], channels[0]])
print(values[0], type(values[0]))
print(values[1], type(values[1]))
print(values[2], type(values[2]))

# get time series
now = time.time_ns()
ten_minutes_before = now - 10*60*1_000_000_000  # ... nanoseconds based
histories = ehs.get_histories([channels[4]], begin_inclusive=ten_minutes_before, end_exclusive=now)
for number, v in enumerate(histories[0]):
    time_, value = v
    print("{}\t{}\t{}".format(number, time_, value))
