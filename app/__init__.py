import os
from flask import Flask
from .config import Config
from .extensions import db, login_manager, migrate, csrf
from .models import User


def _migrate_actif_column():
    """Ajoute la colonne 'actif' si absente — compatible SQLite et PostgreSQL."""
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    try:
        cols = [c['name'] for c in inspector.get_columns('users')]
    except Exception:
        return  # table pas encore créée, db.create_all() s'en charge
    if 'actif' not in cols:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN actif INTEGER NOT NULL DEFAULT 1"))
            conn.commit()


def _migrate_sortie_columns():
    """Ajoute les colonnes sortie/fin si absentes — compatible SQLite et PostgreSQL."""
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    try:
        patient_cols    = [c['name'] for c in inspector.get_columns('patients')]
        traitement_cols = [c['name'] for c in inspector.get_columns('traitements')]
    except Exception:
        return

    with db.engine.connect() as conn:
        for col, ddl in [
            ('date_sortie',      'ALTER TABLE patients ADD COLUMN date_sortie DATE'),
            ('motif_sortie',     'ALTER TABLE patients ADD COLUMN motif_sortie TEXT'),
            ('centre_transfert', 'ALTER TABLE patients ADD COLUMN centre_transfert VARCHAR(150)'),
        ]:
            if col not in patient_cols:
                conn.execute(text(ddl))

        for col, ddl in [
            ('date_fin_reelle', 'ALTER TABLE traitements ADD COLUMN date_fin_reelle DATE'),
            ('motif_arret',     'ALTER TABLE traitements ADD COLUMN motif_arret TEXT'),
        ]:
            if col not in traitement_cols:
                conn.execute(text(ddl))

        conn.commit()


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config())
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        user = db.session.get(User, int(user_id))
        if user and not user.actif:
            return None
        return user

    # Blueprints
    from .blueprints.public import public_bp
    from .blueprints.auth import auth_bp
    from .blueprints.dashboard import dashboard_bp
    from .blueprints.patients import patients_bp
    from .blueprints.dosage import dosage_bp
    from .blueprints.traitement import traitement_bp
    from .blueprints.effets import effets_bp
    from .blueprints.contacts import contacts_bp
    from .blueprints.stock import stock_bp
    from .blueprints.rapports import rapports_bp
    from .blueprints.labo import labo_bp
    from .blueprints.admin import admin_bp
    from .blueprints.search import search_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(dosage_bp)
    app.register_blueprint(traitement_bp)
    app.register_blueprint(effets_bp)
    app.register_blueprint(contacts_bp)
    app.register_blueprint(stock_bp)
    app.register_blueprint(rapports_bp)
    app.register_blueprint(labo_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(search_bp)

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template as rt
        return rt('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template as rt
        return rt('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template as rt
        return rt('errors/500.html'), 500

    with app.app_context():
        db.create_all()
        _migrate_actif_column()
        _migrate_sortie_columns()
        if os.getenv('FLASK_ENV') != 'production':
            from .utils.seed import seed_demo_data
            seed_demo_data()

    return app
