# Import necessary libraries and modules
import os
from flask import Flask
from flask_smorest import Api
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import redis
from rq import Queue

# Initialize Flask app, SQLAlchemy, Migrate, and Flask-Smorest API
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///tasks.db')
app.config['POSTGRES_PASSWORD'] = "berkeley153B"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Swagger/OpenAPI configuration
app.config["API_TITLE"] = "Production Task Manager API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

# Initialize Flask-Smorest API
api = Api(app)


# Import tasks and categories blueprints to register them with the api
from .routes.tasks import tasks_blp
from .routes.categories import categories_blp

# Register blueprints with the api
api.register_blueprint(tasks_blp)
api.register_blueprint(categories_blp)

# Redis connection and the notiifications queue for background jobs
redis_conn = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
queue = Queue('notifications', connection=redis_conn)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)