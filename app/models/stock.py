from datetime import datetime, date
from ..extensions import db


class Medicament(db.Model):
    __tablename__ = 'stock_medicaments'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(150), nullable=False)
    abreviation = db.Column(db.String(10))
    forme = db.Column(db.String(50))          # cp | gel | sachet | injectable
    dosage_unitaire = db.Column(db.String(50)) # ex: "400 mg"
    quantite_stock = db.Column(db.Integer, default=0)
    unite = db.Column(db.String(20), default='cp')
    seuil_alerte = db.Column(db.Integer, default=100)
    date_expiration = db.Column(db.Date)
    centre = db.Column(db.String(150))

    @property
    def stock_bas(self):
        return self.quantite_stock <= self.seuil_alerte

    @property
    def expire_bientot(self):
        if self.date_expiration:
            return (self.date_expiration - date.today()).days < 90
        return False

    @property
    def statut(self):
        if self.quantite_stock == 0:
            return ('danger', 'Rupture')
        elif self.stock_bas:
            return ('warning', 'Stock faible')
        return ('success', 'Disponible')

    @property
    def pourcentage_stock(self):
        reference = self.seuil_alerte * 3
        return min(100, int(self.quantite_stock / reference * 100)) if reference > 0 else 0


class MouvementStock(db.Model):
    """Traçabilité des entrées et sorties de stock de médicaments."""
    __tablename__ = 'mouvements_stock'

    id = db.Column(db.Integer, primary_key=True)
    medicament_id = db.Column(db.Integer, db.ForeignKey('stock_medicaments.id'), nullable=False)
    # entree | sortie | ajustement | perte | expiration
    type_mouvement = db.Column(db.String(20), nullable=False)
    quantite = db.Column(db.Integer, nullable=False)
    quantite_avant = db.Column(db.Integer, nullable=False)
    quantite_apres = db.Column(db.Integer, nullable=False)
    date_mouvement = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reference_bon = db.Column(db.String(50))
    motif = db.Column(db.String(200))

    medicament = db.relationship('Medicament', backref=db.backref('mouvements', lazy=True,
                                  cascade='all, delete-orphan'))
    utilisateur = db.relationship('User', foreign_keys=[utilisateur_id],
                                   backref=db.backref('mouvements_stock', lazy=True))

    @property
    def type_label(self):
        labels = {
            'entree': 'Entrée fournisseur',
            'sortie': 'Distribution patient',
            'ajustement': 'Ajustement inventaire',
            'perte': 'Perte / casse',
            'expiration': 'Péremption',
        }
        return labels.get(self.type_mouvement, self.type_mouvement)

    @property
    def type_badge(self):
        badges = {
            'entree': 'success',
            'sortie': 'primary',
            'ajustement': 'info',
            'perte': 'danger',
            'expiration': 'warning',
        }
        return badges.get(self.type_mouvement, 'secondary')

    def __repr__(self):
        return f'<MouvementStock med_id={self.medicament_id} type={self.type_mouvement} qte={self.quantite}>'
