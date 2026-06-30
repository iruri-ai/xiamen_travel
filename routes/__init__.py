from routes.attractions import attractions_bp
from routes.weather import weather_bp
from routes.comments import comments_bp
from routes.favorites import favorites_bp
from routes.routes import routes_bp
from routes.tags import tags_bp

def register_blueprints(app):
    app.register_blueprint(attractions_bp, url_prefix='/api/attractions')
    app.register_blueprint(weather_bp, url_prefix='/api/weather')
    app.register_blueprint(comments_bp, url_prefix='/api/comments')
    app.register_blueprint(favorites_bp, url_prefix='/api/favorites')
    app.register_blueprint(routes_bp, url_prefix='/api/routes')
    app.register_blueprint(tags_bp, url_prefix='/api/tags')
