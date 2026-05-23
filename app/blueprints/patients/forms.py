from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FloatField, DateField, TextAreaField, SubmitField, IntegerField
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
        ('nouveau_cas',    'N — Nouveau cas'),
        ('echec_primo',    'E1 — Échec primotraitement'),
        ('echec_retrait',  'E2 — Échec retraitement'),
        ('reprise',        'RT — Reprise après perte de vue'),
        ('rechute_primo',  'R1 — Rechute après primotraitement'),
        ('rechute_retrait','R2 — Rechute après retraitement'),
        ('transfert',      'TE — Transfert entrant'),
        ('echec_tbmr',     'E4 — Échec schéma TB-MR'),
        ('reprise_tbmr',   'RT4 — Reprise après PDV sous TB-MR'),
        ('rechute_tbmr',   'R4 — Rechute après schéma TB-MR'),
        ('autres',         'A — Autres'),
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


class SuiviPonderalForm(FlaskForm):
    mois_suivi         = IntegerField('Mois de suivi (M0, M1...)', validators=[DataRequired(), NumberRange(min=0, max=36)])
    date_mesure        = DateField('Date de la mesure', format='%Y-%m-%d', validators=[DataRequired()])
    poids              = FloatField('Poids (kg)', validators=[Optional(), NumberRange(min=10, max=300)])
    taille             = FloatField('Taille (cm) — saisir une seule fois à M0', validators=[Optional(), NumberRange(min=50, max=250)])
    tension_sys        = IntegerField('Tension systolique (mmHg)', validators=[Optional(), NumberRange(min=50, max=300)])
    tension_dia        = IntegerField('Tension diastolique (mmHg)', validators=[Optional(), NumberRange(min=30, max=200)])
    temperature        = FloatField('Température (°C)', validators=[Optional(), NumberRange(min=34, max=43)])
    # Bilan biologique mensuel (Tableau IV PNLT 2021 p.27)
    kaliemie_mmol_l    = FloatField('Kaliémie K+ (mmol/L)', validators=[Optional(), NumberRange(min=1, max=10)])
    creatinine_umol_l  = FloatField('Créatinine (µmol/L)', validators=[Optional(), NumberRange(min=10, max=2000)])
    gpt_u_l            = FloatField('GPT / ALAT (U/L)', validators=[Optional(), NumberRange(min=0, max=5000)])
    got_u_l            = FloatField('GOT / ASAT (U/L)', validators=[Optional(), NumberRange(min=0, max=5000)])
    leucocytes_g_l     = FloatField('Leucocytes (G/L)', validators=[Optional(), NumberRange(min=0, max=100)])
    plaquettes_g_l     = FloatField('Plaquettes (G/L)', validators=[Optional(), NumberRange(min=0, max=2000)])
    notes              = TextAreaField('Observations', validators=[Optional()])
    submit             = SubmitField('Enregistrer')
