from core.extension.extension import Extension
from data_app import DataApp


def init_app(app: DataApp):
    code_based_extension.init()


code_based_extension = Extension()
