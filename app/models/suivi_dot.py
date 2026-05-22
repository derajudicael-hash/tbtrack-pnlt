import json
from datetime import datetime, date
from ..extensions import db


class SuiviDOT(db.Model):
    """DOT = Directly Observed Therapy — observation directe de la prise de médicaments."""
    __tablename__ = 'suivi_dot'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    traitement_id = db.Column(db.Integer, db.ForeignKey('traitements.id'), nullable=False)
    date_observation = db.Column(db.Date, nullable=False, default=date.today)
    prise_confirmee = db.Column(db.Boolean, default=True, nullable=False)
    _medicaments_pris = db.Column('medicaments_pris', db.Text)
    _medicaments_omis = db.Column('medicaments_omis', db.Text)
    observateur_nom = db.Column(db.String(100))
    observateur_role = db.Column(db.String(50))  # infirmier | agent_communautaire | famille | autre
    raison_omission = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relation vers le patient (sans delete-orphan : la suppression en cascade est gérée par Traitement)
    patient = db.relationship('Patient', backref=db.backref('suivi_dot',
                              lazy='dynamic', order_by='SuiviDOT.date_observation.desc()'))

    @property
    def medicaments_pris(self):
        if self._medicaments_pris:
            return json.loads(self._medicaments_pris)
        return []

    @medicaments_pris.setter
    def medicaments_pris(self, value):
        self._medicaments_pris = json.dumps(value) if value else None

    @property
    def medicaments_omis(self):
        if self._medicaments_omis:
            return json.loads(self._medicaments_omis)
        return []

    @medicaments_omis.setter
    def medicaments_omis(self, value):
        self._medicaments_omis = json.dumps(value) if value else None

    @classmethod
    def taux_adherence(cls, patient_id, traitement_id, nb_jours=30):
        """Calcule le pourcentage de prises confirmées sur les nb_jours derniers jours."""
        from datetime import timedelta
        date_debut = date.today() - timedelta(days=nb_jours)
        observations = cls.query.filter(
            cls.patient_id == patient_id,
            cls.traitement_id == traitement_id,
            cls.date_observation >= date_debut,
        ).all()
        if not observations:
            return None
        nb_prises = sum(1 for o in observations if o.prise_confirmee)
        return round(nb_prises / len(observations) * 100, 1)

    def __repr__(self):
        return f'<SuiviDOT patient_id={self.patient_id} date={self.date_observation} pris={self.prise_confirmee}>'
