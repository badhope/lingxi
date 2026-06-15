from flask_orjson import OrjsonProvider

from data_app import DataApp


def init_app(app: DataApp):
    """Initialize Flask-Orjson extension for faster JSON serialization"""
    app.json = OrjsonProvider(app)
