from datetime import datetime
from ..extensions import db


class BilanInitial(db.Model):
    """Bilan paraclinique initial (M0) obligatoire selon guide PNLT 2021."""
    __tablename__ = 'bilans_initiaux'

    id = db.Column(db.Integer, primary_key=True)
    # Un seul bilan par patient (M0)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, unique=True)
    date_bilan = db.Column(db.Date)

    # Anthropométrie
    poids_kg = db.Column(db.Float)
    taille_cm = db.Column(db.Float)

    # Bilan rénal
    creatinine_umol_l = db.Column(db.Float)
    clairance_creatinine = db.Column(db.Float)  # ml/min, formule Cockcroft-Gault

    # Hématologie
    hb_g_dl = db.Column(db.Float)  # Hémoglobine

    # Bilan hépatique
    alt_u_l = db.Column(db.Float)   # ALAT
    ast_u_l = db.Column(db.Float)   # ASAT

    # Bilan métabolique
    glycemie_mmol_l = db.Column(db.Float)
    kaliemie_mmol_l = db.Column(db.Float)

    # Toxicités spécifiques aux médicaments TB-MR
    audiogramme_normal = db.Column(db.Boolean)       # Toxicité aminoglycosides (Am)
    ecg_qt_ms = db.Column(db.Integer)                # Allongement QT (Bdq, Dlm, Mfx)
    acuite_visuelle_normale = db.Column(db.Boolean)  # Éthambutol
    thyroide_normale = db.Column(db.Boolean)         # Éthionamide / Prothionamide

    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relation vers le patient
    patient = db.relationship('Patient', backref=db.backref('bilan_initial', uselist=False,
                              lazy=True, cascade='all, delete-orphan'))

    @property
    def imc(self):
        """Indice de masse corporelle (kg/m²)."""
        if self.poids_kg and self.taille_cm and self.taille_cm > 0:
            taille_m = self.taille_cm / 100
            return round(self.poids_kg / (taille_m ** 2), 1)
        return None

    @property
    def imc_categorie(self):
        """Catégorie IMC selon OMS."""
        imc = self.imc
        if imc is None:
            return None
        if imc < 16:
            return ('danger', 'Dénutrition sévère')
        elif imc < 18.5:
            return ('warning', 'Insuffisance pondérale')
        elif imc < 25:
            return ('success', 'Normal')
        elif imc < 30:
            return ('info', 'Surpoids')
        else:
            return ('warning', 'Obésité')

    @property
    def ecg_alerte(self):
        """Vrai si l'intervalle QTc est supérieur à 450 ms (risque torsades de pointes)."""
        return self.ecg_qt_ms is not None and self.ecg_qt_ms > 450

    @property
    def insuffisance_renale(self):
        """Vrai si la clairance de la créatinine est inférieure à 30 ml/min."""
        return self.clairance_creatinine is not None and self.clairance_creatinine < 30

    @property
    def anemie(self):
        """Vrai si l'hémoglobine est inférieure à 11 g/dl."""
        return self.hb_g_dl is not None and self.hb_g_dl < 11

    @property
    def cytolyse_hepatique(self):
        """Vrai si ALAT ou ASAT > 3x normale (> 120 U/L)."""
        alt_anormal = self.alt_u_l is not None and self.alt_u_l > 120
        ast_anormal = self.ast_u_l is not None and self.ast_u_l > 120
        return alt_anormal or ast_anormal

    def __repr__(self):
        return f'<BilanInitial patient_id={self.patient_id} date={self.date_bilan}>'
