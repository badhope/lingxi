from core.hosting_configuration import HostingConfiguration

hosting_configuration = HostingConfiguration()


from data_app import DataApp


def init_app(app: DataApp):
    hosting_configuration.init_app(app)
