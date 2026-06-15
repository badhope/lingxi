import os
import time

from data_app import DataApp


def init_app(app: DataApp):
    os.environ["TZ"] = "UTC"
    # windows platform not support tzset
    if hasattr(time, "tzset"):
        time.tzset()
