from data_app import DataApp


def init_app(app: DataApp):
    from events import event_handlers  # noqa: F401
