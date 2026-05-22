from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional


class EffetForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    medicament_incrimine = SelectField('Médicament incriminé', choices=[
        ('', '— Sélectionner —'),
        ('Bedaquiline', 'Bedaquiline (Bdq)'),
        ('Moxifloxacine', 'Moxifloxacine (Mfx)'),
        ('Levofloxacine', 'Levofloxacine (Lfx)'),
        ('Linezolide', 'Linezolide (Lzd)'),
        ('Clofazimine', 'Clofazimine (Cfz)'),
        ('Cycloserine', 'Cycloserine (Cs)'),
        ('Prothionamide', 'Prothionamide (Pto)'),
        ('Ethambutol', 'Ethambutol (E)'),
        ('Pyrazinamide', 'Pyrazinamide (Z)'),
        ('Isoniazide', 'Isoniazide (H)'),
        ('Delamanide', 'Delamanide (Dlm)'),
        ('PAS', 'PAS'),
        ('Autre', 'Autre'),
    ])
    symptome = StringField('Symptôme / Effet observé', validators=[DataRequired()])
    severite = SelectField('Sévérité', choices=[
        ('leger', 'Léger'), ('modere', 'Modéré'), ('severe', 'Sévère')
    ])
    notes = TextAreaField('Notes complémentaires', validators=[Optional()])
    submit = SubmitField('Déclarer l\'effet')
