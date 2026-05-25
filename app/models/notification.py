from datetime import datetime
from ..extensions import db


class Notification(db.Model):
    __tablename__ = 'notifications'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message    = db.Column(db.Text, nullable=False)
    type_notif = db.Column(db.String(20), default='info')   # info | warning | danger | success
    lue        = db.Column(db.Boolean, default=False, nullable=False)
    url        = db.Column(db.String(300), nullable=True)
    # Clé de déduplication : une seule notif non lue par ref par utilisateur
    ref        = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User',
                           backref=db.backref('notifications',
                                              lazy='dynamic',
                                              cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Notification user={self.user_id} type={self.type_notif} lue={self.lue}>'
