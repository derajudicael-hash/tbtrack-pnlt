from datetime import datetime, date
from ..extensions import db


class Contact(db.Model):
    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True)
    patient_source_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100))
    age = db.Column(db.Integer)
    sexe = db.Column(db.String(10))
    relation = db.Column(db.String(50))  # foyer | famille | travail | autre
    telephone = db.Column(db.String(20))
    date_premier_contact = db.Column(db.Date, default=date.today)
    statut = db.Column(db.String(30), default='en_suivi')  # en_suivi | negatif | tb_mr_confirmee | perdu
    date_prochaine_visite = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Champs dépistage TB-MR
    date_depistage = db.Column(db.Date)
    # negatif | positif | invalide | non_fait
    resultat_genexpert = db.Column(db.String(20), default='non_fait')
    # normale | anormale | non_faite
    radiographie_thorax = db.Column(db.String(20), default='non_faite')
    ipt_propose = db.Column(db.Boolean, default=False)   # Thérapie Préventive Isoniazide proposée
    ipt_accepte = db.Column(db.Boolean, default=False)
    date_prochain_controle = db.Column(db.Date)

    @property
    def jours_restants_suivi(self):
        if self.date_premier_contact:
            d = self.date_premier_contact
            fin = date(d.year + 2, d.month, d.day)
            return (fin - date.today()).days
        return None

    @property
    def progression_suivi(self):
        if self.date_premier_contact:
            ecoules = (date.today() - self.date_premier_contact).days
            return min(100, int(ecoules / 730 * 100))
        return 0

    @property
    def statut_badge(self):
        return {
            'en_suivi': 'primary',
            'negatif': 'success',
            'tb_mr_confirmee': 'danger',
            'perdu': 'warning',
        }.get(self.statut, 'secondary')

    @property
    def statut_label(self):
        return {
            'en_suivi': 'En suivi',
            'negatif': 'Négatif',
            'tb_mr_confirmee': 'TB-MR confirmée',
            'perdu': 'Perdu de vue',
        }.get(self.statut, self.statut)

    @property
    def necessite_suivi_urgent(self):
        """Vrai si le résultat GeneXpert est positif — nécessite prise en charge immédiate."""
        return self.resultat_genexpert == 'positif'

    @property
    def genexpert_badge(self):
        return {
            'negatif': 'success',
            'positif': 'danger',
            'invalide': 'warning',
            'non_fait': 'secondary',
        }.get(self.resultat_genexpert, 'secondary')

    @property
    def genexpert_label(self):
        return {
            'negatif': 'GeneXpert Négatif',
            'positif': 'GeneXpert Positif',
            'invalide': 'GeneXpert Invalide',
            'non_fait': 'Non effectué',
        }.get(self.resultat_genexpert, self.resultat_genexpert)
