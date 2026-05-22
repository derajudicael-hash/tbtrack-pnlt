from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from ..extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nom = db.Column(db.String(100))
    prenom = db.Column(db.String(100))
    role = db.Column(db.String(50), default='medecin')  # medecin | infirmier | coordinateur | laborantin
    centre = db.Column(db.String(150))
    actif = db.Column(db.Boolean, default=True, nullable=False, server_default='1')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patients = db.relationship('Patient', backref='medecin', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        if self.prenom and self.nom:
            return f"{self.prenom} {self.nom}"
        return self.email

    @property
    def role_label(self):
        labels = {
            'medecin': 'Médecin',
            'infirmier': 'Infirmier(e)',
            'coordinateur': 'Coordinateur PNLT',
            'laborantin': 'Laborantin(e)',
        }
        return labels.get(self.role, self.role)
