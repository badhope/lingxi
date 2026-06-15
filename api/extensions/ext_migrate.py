from data_app import DataApp


def init_app(app: DataApp):
    import flask_migrate

    from extensions.ext_database import db

    flask_migrate.Migrate(app, db)
