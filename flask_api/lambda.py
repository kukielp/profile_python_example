from flask_lambda import FlaskLambda
from app import app

http_server = create_app(FlaskLambda)