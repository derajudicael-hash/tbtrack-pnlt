from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, SubmitField, DateField
from wtforms.validators import DataRequired, Optional, Length, NumberRange


class MouvementForm(FlaskForm):
    type_mouvement = SelectField('Type de mouvement', choices=[
        ('entree', 'Entrée fournisseur'),
        ('sortie', 'Distribution patient'),
        ('ajustement', 'Ajustement inventaire'),
        ('perte', 'Perte / casse'),
        ('expiration', 'Péremption'),
    ], validators=[DataRequired()])
    quantite = IntegerField('Quantité', validators=[
        DataRequired(),
        NumberRange(min=1, message='La quantité doit être supérieure à 0.'),
    ])
    reference_bon = StringField('N° bon / référence', validators=[Optional(), Length(max=50)])
    motif = StringField('Motif / commentaire', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Enregistrer le mouvement')


class MedicamentForm(FlaskForm):
    nom = StringField('Nom du médicament', validators=[DataRequired(), Length(max=150)])
    abreviation = StringField('Abréviation', validators=[Optional(), Length(max=10)])
    forme = SelectField('Forme pharmaceutique', choices=[
        ('cp', 'Comprimé'),
        ('gel', 'Gélule'),
        ('sachet', 'Sachet'),
        ('injectable', 'Injectable'),
        ('sirop', 'Sirop'),
        ('autre', 'Autre'),
    ])
    dosage_unitaire = StringField('Dosage unitaire (ex: 400 mg)', validators=[Optional(), Length(max=50)])
    quantite_stock = IntegerField('Quantité initiale en stock', validators=[Optional()])
    seuil_alerte = IntegerField('Seuil d\'alerte', validators=[
        DataRequired(),
        NumberRange(min=1, message='Le seuil doit être supérieur à 0.'),
    ])
    date_expiration = DateField('Date d\'expiration', format='%Y-%m-%d', validators=[Optional()])
    centre = StringField('Centre / Structure de santé', validators=[Optional(), Length(max=150)])
    submit = SubmitField('Enregistrer')
