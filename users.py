from db import db
from flask import session, request, abort
from werkzeug.security import check_password_hash, generate_password_hash
import os

def login(username, password):
    sql = "SELECT id, password FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()
    if not user:
        return False
    else:
        if check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user_name"] = username
            session["csrf"] = os.urandom(16).hex()
            session["coef"] = 1
            return True
        else:
            return False

def register(username, password):
    hash_value = generate_password_hash(password)
    try:
        sql = "INSERT INTO users (username, password) VALUES (:username, :password)"
        db.session.execute(sql, {"username":username, "password":hash_value})
        db.session.commit()
    except:
        return False
    return login(username, password)

def user_id():
    return session.get("user_id", 0)

def logout():
    del session["user_id"]

def user_name():
    return session.get("username")

def check_csrf():
    if session["csrf"] != request.form["csrf"]:
        abort(403)


