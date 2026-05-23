from datetime import datetime
from ..extensions import db


class NoteClinique(db.Model):
    __tablename__ = 'notes_cliniques'

    id         = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    auteur_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    contenu    = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    patient = db.relationship('Patient', backref=db.backref(
        'notes', lazy='dynamic', cascade='all, delete-orphan'))
    auteur  = db.relationship('User', foreign_keys=[auteur_id])
