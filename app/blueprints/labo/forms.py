from flask_wtf import FlaskForm
from wtforms import (SelectField, IntegerField, DateField, BooleanField,
                     TextAreaField, SubmitField)
from wtforms.validators import DataRequired, InputRequired, Optional, NumberRange


RESISTANCE_CHOICES = [
    ('', '—'),
    ('sensible', 'Sensible'),
    ('resistant', 'Résistant'),
    ('intermediaire', 'Intermédiaire'),
]


class ExamenLaboForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    mois_suivi = IntegerField('Mois de suivi', validators=[InputRequired(), NumberRange(min=0, max=24)],
                              render_kw={'placeholder': '0'})
    date_prelevement = DateField('Date du prélèvement', validators=[DataRequired()])
    date_resultat = DateField('Date du résultat', validators=[Optional()])

    # GeneXpert
    genexpert_effectue = BooleanField('GeneXpert MTB/RIF effectué')
    genexpert_resultat = SelectField('Résultat GeneXpert', choices=[
        ('', '—'), ('positif', 'Positif (MTB détecté)'),
        ('negatif', 'Négatif (MTB non détecté)'), ('indetermine', 'Indéterminé'),
    ], validators=[Optional()])
    genexpert_resistance_rif = SelectField('Résistance Rifampicine', choices=[
        ('', '—'), ('detected', 'Détectée (RIF résistant)'),
        ('not_detected', 'Non détectée (RIF sensible)'), ('indetermine', 'Indéterminée'),
    ], validators=[Optional()])

    # Frottis
    frottis_effectue = BooleanField('Frottis (microscopie) effectué')
    frottis_resultat = SelectField('Résultat frottis', choices=[
        ('', '—'), ('positif', 'Positif (BAAR+)'), ('negatif', 'Négatif (BAAR-)'),
    ], validators=[Optional()])
    frottis_quantite = SelectField('Quantité bacilles', choices=[
        ('', '—'), ('scanty', 'Scanty (1-9/100c)'),
        ('1+', '1+ (10-99/100c)'), ('2+', '2+ (1-10/champ)'), ('3+', '3+ (>10/champ)'),
    ], validators=[Optional()])

    # Culture
    culture_effectuee = BooleanField('Culture effectuée')
    culture_resultat = SelectField('Résultat culture', choices=[
        ('', '—'), ('positif', 'Positif'), ('negatif', 'Négatif'),
        ('contamine', 'Contaminé'), ('en_attente', 'En attente'),
    ], validators=[Optional()])
    culture_milieu = SelectField('Milieu de culture', choices=[
        ('', '—'), ('LJ', 'Löwenstein-Jensen (LJ)'),
        ('MGIT', 'MGIT (liquide)'), ('LJ+MGIT', 'LJ + MGIT'),
    ], validators=[Optional()])

    # DST
    dst_effectue = BooleanField('Antibiogramme (DST) effectué')
    dst_isoniazide = SelectField('Isoniazide (H)', choices=RESISTANCE_CHOICES, validators=[Optional()])
    dst_rifampicine = SelectField('Rifampicine (R)', choices=RESISTANCE_CHOICES, validators=[Optional()])
    dst_ethambutol = SelectField('Ethambutol (E)', choices=RESISTANCE_CHOICES, validators=[Optional()])
    dst_pyrazinamide = SelectField('Pyrazinamide (Z)', choices=RESISTANCE_CHOICES, validators=[Optional()])
    dst_levofloxacine = SelectField('Levofloxacine (Lfx)', choices=RESISTANCE_CHOICES, validators=[Optional()])
    dst_moxifloxacine = SelectField('Moxifloxacine (Mfx)', choices=RESISTANCE_CHOICES, validators=[Optional()])
    dst_bedaquiline = SelectField('Bedaquiline (Bdq)', choices=RESISTANCE_CHOICES, validators=[Optional()])
    dst_linezolide = SelectField('Linézolide (Lzd)', choices=RESISTANCE_CHOICES, validators=[Optional()])
    # Aminoglycosides et FQ ancienne génération — requis pour classer XDR/pré-XDR (formulaire PNLT p.70)
    dst_amikacine = SelectField('Amikacine (Am)', choices=RESISTANCE_CHOICES, validators=[Optional()])
    dst_kanamycine = SelectField('Kanamycine (Km)', choices=RESISTANCE_CHOICES, validators=[Optional()])
    dst_capreomycine = SelectField('Capréomycine (Cm)', choices=RESISTANCE_CHOICES, validators=[Optional()])
    dst_ofloxacine = SelectField('Ofloxacine (Ofx)', choices=RESISTANCE_CHOICES, validators=[Optional()])

    notes = TextAreaField('Observations / Notes', validators=[Optional()])
    submit = SubmitField('Enregistrer les résultats')
