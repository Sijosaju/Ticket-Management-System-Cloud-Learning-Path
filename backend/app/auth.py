from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from .models import User, db


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user = db.session.get(User, int(get_jwt_identity()))
        if not user or user.role != "admin":
            return jsonify(error="Administrator access required"), 403
        return fn(*args, **kwargs)
    return wrapper
