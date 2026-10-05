from flask import Flask
from .database.db import init_db
def create_app():
 app=Flask(__name__); app.secret_key='change-this-secret'; init_db()
 from .routes import main; app.register_blueprint(main); return app
