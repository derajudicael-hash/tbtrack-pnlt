from flask_wtf import FlaskForm
from wtforms import (StringField, SelectField, DateField, TextAreaField,
                     SubmitField, BooleanField, FloatField, IntegerField)
from wtforms.validators import DataRequired, Optional, Length

# Liste complète des médicaments TB-MR selon guide PNLT 2021 / OMS 2022
MEDICAMENTS_TBMR = [
    # Groupe A — Médicaments prioritaires
    'Lévofloxacine (Lfx)',
    'Moxifloxacine (Mfx)',
    'Bédaquiline (Bdq)',
    'Linézolide (Lzd)',
    # Groupe B — Médicaments additionnels
    'Clofazimine (Cfz)',
    'Cyclosérine (Cs)',
    'Térizidone (Trd)',
    # Groupe C — Médicaments complémentaires
    'Éthambutol (E)',
    'Délamanide (Dlm)',
    'Pyrazinamide (Z)',
    'Imipénème-Cilastatine (Imp)',
    'Méropénème (Mpm)',
    'Amikacine (Am)',
    'Streptomycine (S)',
    'Éthionamide (Eto)',
    'Prothionamide (Pto)',
    'Acide para-aminosalicylique (PAS)',
    # Agents complémentaires
    'Isoniazide haute dose (Hh)',
    'Rifabutine (Rfb)',
]

GROUPES_MEDICAMENTS = {
    'Groupe A — Prioritaires (OMS)': [
        'Lévofloxacine (Lfx)',
        'Moxifloxacine (Mfx)',
        'Bédaquiline (Bdq)',
        'Linézolide (Lzd)',
    ],
    'Groupe B — Additionnels': [
        'Clofazimine (Cfz)',
        'Cyclosérine (Cs)',
        'Térizidone (Trd)',
    ],
    'Groupe C — Complémentaires': [
        'Éthambutol (E)',
        'Délamanide (Dlm)',
        'Pyrazinamide (Z)',
        'Imipénème-Cilastatine (Imp)',
        'Méropénème (Mpm)',
        'Amikacine (Am)',
        'Streptomycine (S)',
        'Éthionamide (Eto)',
        'Prothionamide (Pto)',
        'Acide para-aminosalicylique (PAS)',
        'Isoniazide haute dose (Hh)',
        'Rifabutine (Rfb)',
    ],
}


class TraitementForm(FlaskForm):
    schema_nom = StringField('Nom du schéma / protocole', validators=[DataRequired(), Length(max=200)])
    phase = SelectField('Phase initiale', choices=[
        ('intensive', 'Phase intensive'),
        ('continuation', 'Phase de continuation'),
    ])
    date_debut = DateField('Date de début', format='%Y-%m-%d', validators=[DataRequired()])
    date_fin_prevue = DateField('Date de fin prévue', format='%Y-%m-%d', validators=[Optional()])
    statut_traitement = SelectField('Statut du traitement', choices=[
        ('actif', 'Actif'),
        ('suspendu', 'Suspendu'),
        ('termine', 'Terminé'),
        ('echec', 'Échec thérapeutique'),
        ('abandon', 'Abandon'),
    ])
    # Hidden field JSON — rempli par JavaScript lors de la sélection des checkboxes
    medicaments_json = StringField('Médicaments (JSON)', validators=[Optional()])
    observateur_nom = StringField("Nom de l'observateur DOT", validators=[Optional(), Length(max=100)])
    date_fin_reelle = DateField('Date de fin réelle', format='%Y-%m-%d', validators=[Optional()])
    motif_arret = TextAreaField("Motif d'arrêt / observations de fin", validators=[Optional()])
    notes = TextAreaField('Notes cliniques', validators=[Optional()])
    submit = SubmitField('Enregistrer le traitement')


class SuiviDOTForm(FlaskForm):
    date_observation = DateField("Date d'observation", format='%Y-%m-%d', validators=[DataRequired()])
    prise_confirmee = BooleanField('Prise confirmée', default=True)
    observateur_nom = StringField("Nom de l'observateur", validators=[Optional(), Length(max=100)])
    observateur_role = SelectField("Rôle de l'observateur", choices=[
        ('infirmier', 'Infirmier(e)'),
        ('agent_communautaire', 'Agent communautaire'),
        ('famille', 'Membre de la famille'),
        ('autre', 'Autre'),
    ])
    raison_omission = StringField("Raison de l'omission", validators=[Optional(), Length(max=200)])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Enregistrer la prise')


class BilanInitialForm(FlaskForm):
    date_bilan = DateField('Date du bilan', format='%Y-%m-%d', validators=[DataRequired()])

    # Anthropométrie
    poids_kg = FloatField('Poids (kg)', validators=[Optional()])
    taille_cm = FloatField('Taille (cm)', validators=[Optional()])

    # Examens obligatoires M0 (guide PNLT 2021 p.24-25)
    test_grossesse = BooleanField('Test de grossesse positif (femmes en âge de procréer)')
    rx_thorax_normale = BooleanField('Radiographie thorax normale')
    lpa_1ere_ligne = StringField('LPA 1ère ligne (résultat)', validators=[Optional(), Length(max=200)])
    lpa_2eme_ligne = StringField('LPA 2ème ligne (résultat)', validators=[Optional(), Length(max=200)])

    # Bilan rénal
    creatinine_umol_l = FloatField('Créatinine (µmol/L)', validators=[Optional()])
    clairance_creatinine = FloatField('Clairance créatinine (ml/min) — Cockcroft-Gault', validators=[Optional()])

    # NFS (critique Lzd)
    hb_g_dl = FloatField('Hémoglobine (g/dL)', validators=[Optional()])
    leucocytes_g_l = FloatField('Leucocytes (G/L)', validators=[Optional()])
    plaquettes_g_l = FloatField('Plaquettes (G/L)', validators=[Optional()])

    # Bilan hépatique
    alt_u_l = FloatField('ALAT / GPT (U/L)', validators=[Optional()])
    ast_u_l = FloatField('ASAT / GOT (U/L)', validators=[Optional()])

    # Métabolique
    glycemie_mmol_l = FloatField('Glycémie (mmol/L)', validators=[Optional()])
    kaliemie_mmol_l = FloatField('Kaliémie K+ (mmol/L)', validators=[Optional()])

    # Toxicités spécifiques
    audiogramme_normal = BooleanField('Audiogramme normal (aminoglycosides)')
    ecg_qt_ms = IntegerField('ECG M0 — QTc (ms)', validators=[Optional()])
    ecg_j7_qt_ms = IntegerField('ECG J7 — QTc à 7 jours post-début traitement (ms)', validators=[Optional()])
    acuite_visuelle_normale = BooleanField('Acuité visuelle normale (éthambutol)')
    thyroide_normale = BooleanField('Thyroïde cliniquement normale (éthionamide / prothionamide)')
    tsh_miu_l = FloatField('TSH (mIU/L) — seuil alerte : >1.5× norme haute (~6.75)', validators=[Optional()])

    notes = TextAreaField('Notes / observations', validators=[Optional()])
    submit = SubmitField('Enregistrer le bilan M0')
