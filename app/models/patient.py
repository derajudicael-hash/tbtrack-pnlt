from datetime import datetime, date
from ..extensions import db


class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    code_patient = db.Column(db.String(20), unique=True)

    # Identité
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    date_naissance = db.Column(db.Date)
    sexe = db.Column(db.String(10))
    adresse = db.Column(db.String(200))
    telephone = db.Column(db.String(20))

    # Clinique
    poids = db.Column(db.Float)
    statut_vih = db.Column(db.String(20), default='inconnu')  # positif | negatif | inconnu

    # Diagnostic
    date_diagnostic = db.Column(db.Date)
    type_resistance = db.Column(db.String(20))  # RR-TB | TB-MR | pre-XDR | XDR
    categorie = db.Column(db.String(50))        # nouveau_cas | echec_primo | echec_retrait | reprise | rechute_primo | transfert

    # Traitement
    statut = db.Column(db.String(30), default='en_cours')    # en_cours | gueri | perdu_de_vue | echec | decede | termine | non_evalue | transfert
    schema_therapeutique = db.Column(db.String(20))           # court | long
    date_debut_traitement = db.Column(db.Date)
    notes_cliniques = db.Column(db.Text)

    # Champs de sortie (v0.2)
    date_sortie = db.Column(db.Date)
    motif_sortie = db.Column(db.Text)
    centre_transfert = db.Column(db.String(150))  # Renseigné si statut == 'transfert'

    # Relations
    medecin_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    effets = db.relationship('EffetSecondaire', backref='patient', lazy=True, cascade='all, delete-orphan')
    contacts = db.relationship('Contact', backref='patient_source', lazy=True, cascade='all, delete-orphan')
    traitements = db.relationship('Traitement', backref='patient', lazy=True, cascade='all, delete-orphan')
    examens_labo = db.relationship('ExamenLabo', backref='patient', lazy=True, cascade='all, delete-orphan',
                                   order_by='ExamenLabo.mois_suivi')

    @property
    def age(self):
        if self.date_naissance:
            today = date.today()
            return today.year - self.date_naissance.year - (
                (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
            )
        return None

    @property
    def jours_traitement(self):
        if self.date_debut_traitement:
            return (date.today() - self.date_debut_traitement).days
        return 0

    @property
    def statut_badge(self):
        return {
            'en_cours': 'primary',
            'gueri': 'success',
            'perdu_de_vue': 'warning',
            'echec': 'danger',
            'decede': 'dark',
            'termine': 'secondary',
            'non_evalue': 'light',
            'transfert': 'info',
        }.get(self.statut, 'secondary')

    @property
    def statut_label(self):
        return {
            'en_cours': 'En cours',
            'gueri': 'Guéri',
            'perdu_de_vue': 'Perdu de vue',
            'echec': 'Échec',
            'decede': 'Décédé',
            'termine': 'Terminé',
            'non_evalue': 'Non évalué',
            'transfert': 'Transféré',
        }.get(self.statut, self.statut)

    @property
    def type_resistance_badge(self):
        return {
            'RR-TB': 'info',
            'TB-MR': 'warning',
            'pre-XDR': 'orange',
            'XDR': 'danger',
        }.get(self.type_resistance, 'secondary')

    @property
    def nb_effets_non_notifies(self):
        return sum(1 for e in self.effets if e.severite == 'severe' and not e.notifie_crpc)

    def __repr__(self):
        return f'<Patient {self.code_patient} - {self.nom} {self.prenom}>'
