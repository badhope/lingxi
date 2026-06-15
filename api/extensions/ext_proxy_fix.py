from configs import data_config
from data_app import DataApp


def init_app(app: DataApp):
    if data_config.RESPECT_XFORWARD_HEADERS_ENABLED:
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app, x_port=1)  # type: ignore[method-assign]
