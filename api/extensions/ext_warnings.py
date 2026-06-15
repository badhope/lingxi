from data_app import DataApp


def init_app(app: DataApp):
    import warnings

    warnings.simplefilter("ignore", ResourceWarning)
