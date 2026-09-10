import logging
import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory
from flask_jwt_extended import JWTManager

from .models import db


def create_app(test_config=None):
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    app = Flask(__name__)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=(
            f"mysql+pymysql://{quote_plus(os.getenv('DATABASE_USER', 'root'))}:"
            f"{quote_plus(os.getenv('DATABASE_PASSWORD', ''))}@{os.getenv('DATABASE_HOST', 'localhost')}:"
            f"{os.getenv('DATABASE_PORT', '3306')}/{os.getenv('DATABASE_NAME', 'ticket_booking')}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY=os.getenv("JWT_SECRET"),
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=8),
    )
    if test_config:
        app.config.update(test_config)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app.logger.info("Ticket booking application starting")
    db.init_app(app)
    JWTManager(app)

    from .routes.auth import auth_bp
    from .routes.events import events_bp
    from .routes.bookings import bookings_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(events_bp, url_prefix="/api")
    app.register_blueprint(bookings_bp, url_prefix="/api/bookings")
    frontend_dir = Path(__file__).resolve().parents[2] / "frontend"

    # The frontend is intentionally static and may be served from another local port.
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return response

    @app.get("/health")
    def health():
        return jsonify(status="healthy")

    @app.get("/")
    def frontend_home():
        return send_from_directory(frontend_dir, "index.html")

    @app.get("/<path:filename>")
    def frontend_files(filename):
        """Serve the plain HTML, CSS, and JavaScript frontend during local development."""
        return send_from_directory(frontend_dir, filename)

    return app
