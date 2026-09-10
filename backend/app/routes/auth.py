from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash
from ..models import User, db

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name, email, password = data.get("name", "").strip(), data.get("email", "").strip().lower(), data.get("password", "")
    if not name or not email or len(password) < 6:
        return jsonify(error="Name, email, and a password of at least 6 characters are required"), 400
    if User.query.filter_by(email=email).first(): return jsonify(error="Email is already registered"), 409
    user = User(name=name, email=email, password_hash=generate_password_hash(password))
    db.session.add(user); db.session.commit()
    return jsonify(user=user.public()), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    user = User.query.filter_by(email=data.get("email", "").strip().lower()).first()
    if not user or not check_password_hash(user.password_hash, data.get("password", "")):
        return jsonify(error="Invalid email or password"), 401
    current_app.logger.info("User login: user_id=%s", user.id)
    return jsonify(access_token=create_access_token(identity=str(user.id)), user=user.public())
