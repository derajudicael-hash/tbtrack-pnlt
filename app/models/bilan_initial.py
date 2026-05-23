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

    # Examens obligatoires M0 (guide PNLT 2021 p.24-25)
    test_grossesse = db.Column(db.Boolean)            # Obligatoire chez toute femme en âge de procréer
    rx_thorax_normale = db.Column(db.Boolean)         # Radiographie thorax M0
    lpa_1ere_ligne = db.Column(db.String(200))        # LPA 1ère ligne (résultat texte)
    lpa_2eme_ligne = db.Column(db.String(200))        # LPA 2ème ligne (résultat texte)

    # NFS complète (guide p.27 — critique pour suivi Linézolide)
    leucocytes_g_l = db.Column(db.Float)              # G/L (normale 4–10)
    plaquettes_g_l = db.Column(db.Float)              # G/L (normale 150–400)

    # Toxicités spécifiques aux médicaments TB-MR
    audiogramme_normal = db.Column(db.Boolean)        # Toxicité aminoglycosides (Am)
    ecg_qt_ms = db.Column(db.Integer)                 # ECG M0 — intervalle QTc (ms)
    ecg_j7_qt_ms = db.Column(db.Integer)              # ECG J7 post-début traitement (guide p.27)
    acuite_visuelle_normale = db.Column(db.Boolean)   # Éthambutol
    thyroide_normale = db.Column(db.Boolean)          # Éthionamide / Prothionamide (boolean, rétrocompat)
    tsh_miu_l = db.Column(db.Float)                   # TSH numérique (mIU/L) — seuil 1.5× norme = traitement

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
        """Niveau d'alerte ECG selon guide PNLT 2021 p.27 :
        - 'stop' : QTc ≥ 500 ms → arrêter tous les médicaments allongeant le QT
        - 'surveillance' : QTc 450–499 ms → surveillance rapprochée
        - None : QTc normal (<450 ms)
        """
        if self.ecg_qt_ms is None:
            return None
        if self.ecg_qt_ms >= 500:
            return 'stop'
        if self.ecg_qt_ms > 450:
            return 'surveillance'
        return None

    @property
    def ecg_alerte_j7(self):
        """Même logique pour l'ECG à J7 post-début traitement."""
        if self.ecg_j7_qt_ms is None:
            return None
        if self.ecg_j7_qt_ms >= 500:
            return 'stop'
        if self.ecg_j7_qt_ms > 450:
            return 'surveillance'
        return None

    @property
    def tsh_alerte(self):
        """Vrai si TSH > 1.5× la norme haute (4.5 mIU/L) → commencer traitement substitutif."""
        if self.tsh_miu_l is None:
            return False
        return self.tsh_miu_l > 6.75  # 1.5 × 4.5 mIU/L

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
