from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, DateField, TextAreaField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Optional


class ContactForm(FlaskForm):
    patient_source_id = SelectField('Patient source', coerce=int, validators=[DataRequired()])
    nom = StringField('Nom', validators=[DataRequired()])
    prenom = StringField('Prénom', validators=[Optional()])
    age = IntegerField('Âge', validators=[Optional()])
    sexe = SelectField('Sexe', choices=[('', '—'), ('Homme', 'Homme'), ('Femme', 'Femme')])
    relation = SelectField('Relation', choices=[
        ('foyer', 'Même foyer'),
        ('famille', 'Famille (hors foyer)'),
        ('travail', 'Collègue / travail'),
        ('autre', 'Autre'),
    ])
    telephone = StringField('Téléphone', validators=[Optional()])
    date_prochaine_visite = DateField('Prochaine visite', format='%Y-%m-%d', validators=[Optional()])
    statut = SelectField('Statut', choices=[
        ('en_suivi', 'En suivi'),
        ('negatif', 'Négatif'),
        ('tb_mr_confirmee', 'TB-MR confirmée'),
        ('perdu', 'Perdu de vue'),
    ])
    notes = TextAreaField('Notes', validators=[Optional()])

    # Champs dépistage TB-MR
    date_depistage = DateField('Date du dépistage', format='%Y-%m-%d', validators=[Optional()])
    resultat_genexpert = SelectField('Résultat GeneXpert', choices=[
        ('non_fait', 'Non effectué'),
        ('negatif', 'Négatif'),
        ('positif', 'Positif'),
        ('invalide', 'Invalide / indéterminé'),
    ])
    radiographie_thorax = SelectField('Radiographie thoracique', choices=[
        ('non_faite', 'Non effectuée'),
        ('normale', 'Normale'),
        ('anormale', 'Anormale — à explorer'),
    ])
    ipt_propose = BooleanField('TPT (Thérapie Préventive Tuberculose) proposée')
    ipt_accepte = BooleanField('TPT acceptée par le contact')
    date_prochain_controle = DateField('Date du prochain contrôle', format='%Y-%m-%d', validators=[Optional()])

    submit = SubmitField('Enregistrer')
