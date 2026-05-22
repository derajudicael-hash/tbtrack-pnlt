from datetime import datetime
from ..extensions import db


class EffetSecondaire(db.Model):
    __tablename__ = 'effets_secondaires'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    medicament_incrimine = db.Column(db.String(100))
    symptome = db.Column(db.String(200), nullable=False)
    severite = db.Column(db.String(20), default='leger')  # leger | modere | severe
    date_declaration = db.Column(db.DateTime, default=datetime.utcnow)
    notifie_crpc = db.Column(db.Boolean, default=False)
    date_notification = db.Column(db.DateTime)
    declare_par = db.Column(db.String(100))
    notes = db.Column(db.Text)

    @property
    def severite_badge(self):
        return {'leger': 'warning', 'modere': 'orange', 'severe': 'danger'}.get(self.severite, 'secondary')

    @property
    def severite_label(self):
        return {'leger': 'Léger', 'modere': 'Modéré', 'severe': 'Sévère'}.get(self.severite, self.severite)

    @property
    def heures_depuis_declaration(self):
        return (datetime.utcnow() - self.date_declaration).total_seconds() / 3600

    @property
    def alerte_active(self):
        return self.severite == 'severe' and not self.notifie_crpc
