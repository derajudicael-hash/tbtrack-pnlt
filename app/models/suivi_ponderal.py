from datetime import datetime
from ..extensions import db


class SuiviPonderal(db.Model):
    """Mesures mensuelles : poids, taille, IMC, tension."""
    __tablename__ = 'suivi_ponderal'

    id          = db.Column(db.Integer, primary_key=True)
    patient_id  = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    mois_suivi  = db.Column(db.Integer, nullable=False)   # M0, M1, M2...
    date_mesure = db.Column(db.Date, nullable=False)
    poids       = db.Column(db.Float)                     # kg
    taille      = db.Column(db.Float)                     # cm (saisie une seule fois)
    tension_sys = db.Column(db.Integer)                   # mmHg systolique
    tension_dia = db.Column(db.Integer)                   # mmHg diastolique
    temperature = db.Column(db.Float)                     # °C
    # Bilan biologique mensuel (Tableau IV guide PNLT 2021 p.27)
    kaliemie_mmol_l    = db.Column(db.Float)              # K+ — requis M0→M4 schéma court
    creatinine_umol_l  = db.Column(db.Float)              # Créatinine — requis M0→M4
    gpt_u_l            = db.Column(db.Float)              # GPT/ALAT — requis M0→M18
    got_u_l            = db.Column(db.Float)              # GOT/ASAT — requis M0→M18
    leucocytes_g_l     = db.Column(db.Float)              # NFS — critique pour Linézolide (Lzd)
    plaquettes_g_l     = db.Column(db.Float)              # NFS — critique pour Linézolide (Lzd)
    notes       = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient', backref=db.backref(
        'suivi_ponderal', lazy='dynamic', cascade='all, delete-orphan'))

    @property
    def imc(self):
        if self.poids and self.taille and self.taille > 0:
            return round(self.poids / ((self.taille / 100) ** 2), 1)
        return None

    @property
    def imc_categorie(self):
        v = self.imc
        if v is None:
            return ('secondary', '—')
        if v < 16:
            return ('danger', 'Dénutrition sévère')
        if v < 18.5:
            return ('warning', 'Insuffisance pondérale')
        if v < 25:
            return ('success', 'Normal')
        if v < 30:
            return ('info', 'Surpoids')
        return ('warning', 'Obésité')

    @property
    def tension_label(self):
        if self.tension_sys and self.tension_dia:
            return f'{self.tension_sys}/{self.tension_dia} mmHg'
        return '—'
