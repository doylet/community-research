import os
from flask import Flask

from .config import get_runtime_config, validate_runtime_config

def create_app():

    validate_runtime_config(get_runtime_config())

    root_dir = os.path.abspath(os.path.dirname(__file__))
    base_dir = os.path.dirname(root_dir)
    
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    # Load configuration from a file or environment variables
    # app.config.from_object('config.Config')

    # Initialize extensions, blueprints, etc.
    with app.app_context():
        
        # Import and register blueprints here
        from .routes import main
        app.register_blueprint(main)

        # Initialize other components like database, migrations, etc.
        # db.init_app(app)
        # migrate.init_app(app, db)

    return app