from flask import Flask
from flask_cors import CORS

from .config import Config
from .extensions import db, migrate
from .routes.inventory import inventory_bp
from .routes.orders import orders_bp
from .routes.records import records_bp
from .routes.suppliers import suppliers_bp
from .seed import seed_data


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    Config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(inventory_bp, url_prefix="/api/inventory")
    app.register_blueprint(orders_bp, url_prefix="/api/orders")
    app.register_blueprint(suppliers_bp, url_prefix="/api/suppliers")
    app.register_blueprint(records_bp, url_prefix="/api/records")

    @app.get("/api/health")
    def health_check():
        return {"status": "ok"}

    with app.app_context():
        db.create_all()
        seed_data()

    return app
