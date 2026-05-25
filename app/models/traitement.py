import json
from datetime import datetime, date
from ..extensions import db


class Traitement(db.Model):
    __tablename__ = 'traitements'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    schema_nom = db.Column(db.String(200))
    phase = db.Column(db.String(30), default='intensive')  # intensive | continuation
    date_debut = db.Column(db.Date)
    date_fin_prevue = db.Column(db.Date)
    _medicaments = db.Column('medicaments', db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Champs v0.2
    statut_traitement = db.Column(db.String(30), default='actif')  # actif | suspendu | termine | echec | abandon
    date_fin_reelle = db.Column(db.Date)
    motif_arret = db.Column(db.Text)
    observateur_nom = db.Column(db.String(100))  # Nom de l'observateur DOT désigné

    # Relation DOT
    suivi_dot = db.relationship('SuiviDOT', backref='traitement', lazy=True,
                                cascade='all, delete-orphan')

    @property
    def medicaments(self):
        if self._medicaments:
            return json.loads(self._medicaments)
        return []

    @medicaments.setter
    def medicaments(self, value):
        self._medicaments = json.dumps(value)

    @property
    def jours_ecoules(self):
        if self.date_debut:
            return (date.today() - self.date_debut).days
        return 0

    @property
    def progression(self):
        if self.date_debut and self.date_fin_prevue:
            total = (self.date_fin_prevue - self.date_debut).days
            ecoules = (date.today() - self.date_debut).days
            return min(100, int(ecoules / total * 100)) if total > 0 else 0
        return 0

    @property
    def statut_label(self):
        return {
            'actif': 'Actif',
            'suspendu': 'Suspendu',
            'termine': 'Terminé',
            'echec': 'Échec',
            'abandon': 'Abandon',
        }.get(self.statut_traitement, self.statut_traitement or 'Actif')

    @property
    def statut_badge(self):
        return {
            'actif': 'success',
            'suspendu': 'warning',
            'termine': 'secondary',
            'echec': 'danger',
            'abandon': 'dark',
        }.get(self.statut_traitement, 'secondary')

    @property
    def mois_ecoules(self):
        """Nombre de mois calendaires depuis le début du traitement."""
        if self.date_debut:
            today = date.today()
            return (today.year - self.date_debut.year) * 12 + (today.month - self.date_debut.month)
        return 0
