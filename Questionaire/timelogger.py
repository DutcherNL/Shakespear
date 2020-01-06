from django.utils.timezone import now

# get now datetime based upon django settings.py TZ_INFO


class TimeLogger:
    def __init__(self):
        self.time = None
        self.reset_time()

    def reset_time(self):
        self.time = now()

    def log(self, name):
        dif = now() - self.time
        dif_ms = dif.microseconds
        print("{name}: {time}".format(name=name, time=dif_ms))


logger = TimeLogger()