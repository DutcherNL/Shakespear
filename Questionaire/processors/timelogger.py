from django.utils.timezone import now

import time

# get now datetime based upon django settings.py TZ_INFO

"""
This timelogger was used to trace for optimisation metrics
I know, it's very basic. Don't judge me :P
~ Wouter
"""


class TimeLogger:
    def __init__(self):
        self.time = None
        self.reset_time()

    def reset_time(self):
        self.time = time.perf_counter()

    def log(self, name):
        dif = time.perf_counter() - self.time
        print(f'{name}: {round(dif, 4)} seconds')


logger = TimeLogger()
