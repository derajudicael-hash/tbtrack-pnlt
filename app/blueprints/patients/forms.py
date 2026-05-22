from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FloatField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError
from datetime import date




class PatientForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    prenom = StringField('Prénom', validators=[DataRequired()])
    date_naissance = DateField('Date de naissance', format='%Y-%m-%d', validators=[Optional()])

    def validate_date_naissance(self, field):
        if field.data and field.data > date.today():
            raise ValidationError('La date de naissance ne peut pas être dans le futur.')
    sexe = SelectField('Sexe', choices=[('', '—'), ('Homme', 'Homme'), ('Femme', 'Femme')])
    adresse = StringField('Adresse', validators=[Optional(), Length(max=200)])
    telephone = StringField('Téléphone', validators=[Optional()])
    poids = FloatField('Poids (kg)', validators=[Optional(), NumberRange(min=1, max=300, message='Poids invalide (1–300 kg)')])
    statut_vih = SelectField('Statut VIH', choices=[
        ('inconnu', 'Inconnu'), ('negatif', 'Négatif'), ('positif', 'Positif')
    ])
    date_diagnostic = DateField('Date du diagnostic', format='%Y-%m-%d', validators=[Optional()])
    type_resistance = SelectField('Type de résistance', choices=[
        ('', '— Sélectionner —'), ('RR-TB', 'RR-TB'), ('TB-MR', 'TB-MR'),
        ('pre-XDR', 'Pré-XDR'), ('XDR', 'XDR')
    ])
    categorie = SelectField('Catégorie', choices=[
        ('nouveau_cas', 'Nouveau cas'),
        ('echec_primo', 'Échec primotraitement'),
        ('echec_retrait', 'Échec retraitement'),
        ('reprise', 'Reprise du traitement'),
        ('rechute_primo', 'Rechute après primotraitement'),
        ('rechute_retrait', 'Rechute après retraitement'),
        ('transfert', 'Transfert entrant'),
    ])
    statut = SelectField('Statut', choices=[
        ('en_cours', 'En cours'),
        ('gueri', 'Guéri'),
        ('perdu_de_vue', 'Perdu de vue'),
        ('echec', 'Échec'),
        ('decede', 'Décédé'),
        ('termine', 'Traitement terminé'),
        ('transfert', 'Transféré'),
        ('non_evalue', 'Non évalué'),
    ])
    schema_therapeutique = SelectField('Schéma thérapeutique', choices=[
        ('', '— Sélectionner —'), ('court', 'Court (9-11 mois)'), ('long', 'Long (18 mois)')
    ])
    date_debut_traitement = DateField('Date début traitement', format='%Y-%m-%d', validators=[Optional()])
    notes_cliniques = TextAreaField('Notes cliniques', validators=[Optional()])
    date_sortie = DateField('Date de sortie', format='%Y-%m-%d', validators=[Optional()])
    motif_sortie = TextAreaField('Motif / observations de sortie', validators=[Optional()])
    centre_transfert = StringField('Centre de transfert', validators=[Optional(), Length(max=150)])
    submit = SubmitField('Enregistrer')
