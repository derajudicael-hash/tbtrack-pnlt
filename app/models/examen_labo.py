from datetime import datetime, date
from ..extensions import db


class ExamenLabo(db.Model):
    __tablename__ = 'examens_labo'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    laborantin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    mois_suivi = db.Column(db.Integer, nullable=False)  # M0, M1, M2...
    date_prelevement = db.Column(db.Date, nullable=False)
    date_resultat = db.Column(db.Date)

    # GeneXpert MTB/RIF
    genexpert_effectue = db.Column(db.Boolean, default=False)
    genexpert_resultat = db.Column(db.String(50))       # positif | negatif | indetermine
    genexpert_resistance_rif = db.Column(db.String(50)) # detected | not_detected | indetermine

    # Frottis (microscopie)
    frottis_effectue = db.Column(db.Boolean, default=False)
    frottis_resultat = db.Column(db.String(50))   # positif | negatif
    frottis_quantite = db.Column(db.String(50))   # scanty | 1+ | 2+ | 3+

    # Culture
    culture_effectuee = db.Column(db.Boolean, default=False)
    culture_resultat = db.Column(db.String(50))   # positif | negatif | contamine | en_attente
    culture_milieu = db.Column(db.String(50))     # LJ | MGIT | LJ+MGIT

    # DST / Antibiogramme
    dst_effectue = db.Column(db.Boolean, default=False)
    dst_isoniazide = db.Column(db.String(20))
    dst_rifampicine = db.Column(db.String(20))
    dst_ethambutol = db.Column(db.String(20))
    dst_pyrazinamide = db.Column(db.String(20))
    dst_levofloxacine = db.Column(db.String(20))
    dst_moxifloxacine = db.Column(db.String(20))
    dst_bedaquiline = db.Column(db.String(20))
    dst_linezolide = db.Column(db.String(20))

    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    laborantin = db.relationship('User', foreign_keys=[laborantin_id], backref='examens_realises')

    @property
    def conversion_label(self):
        if self.culture_resultat == 'negatif':
            return 'Converti'
        if self.culture_resultat == 'positif':
            return 'Non converti'
        if self.frottis_resultat == 'negatif':
            return 'Négatif (frottis)'
        return '—'

    @property
    def conversion_badge(self):
        if self.culture_resultat == 'negatif':
            return 'success'
        if self.culture_resultat == 'positif':
            return 'danger'
        if self.frottis_resultat == 'negatif':
            return 'info'
        return 'secondary'

    @property
    def statut_global(self):
        if self.culture_resultat == 'en_attente':
            return 'en_attente'
        if self.date_resultat:
            return 'complete'
        return 'en_attente'

    @property
    def resistance_label(self):
        labels = {
            'sensible': 'Sensible',
            'resistant': 'Résistant',
            'intermediaire': 'Intermédiaire',
        }
        return labels

    def dst_summary(self):
        fields = {
            'H (Isoniazide)': self.dst_isoniazide,
            'R (Rifampicine)': self.dst_rifampicine,
            'E (Ethambutol)': self.dst_ethambutol,
            'Z (Pyrazinamide)': self.dst_pyrazinamide,
            'Lfx': self.dst_levofloxacine,
            'Mfx': self.dst_moxifloxacine,
            'Bdq': self.dst_bedaquiline,
            'Lzd': self.dst_linezolide,
        }
        return {k: v for k, v in fields.items() if v}

    def __repr__(self):
        return f'<ExamenLabo M{self.mois_suivi} patient_id={self.patient_id}>'
