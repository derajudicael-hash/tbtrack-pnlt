from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember = BooleanField('Se souvenir de moi')
    submit = SubmitField('Se connecter')


class ProfilForm(FlaskForm):
    prenom = StringField('Prénom', validators=[DataRequired()])
    nom = StringField('Nom', validators=[DataRequired()])
    centre = StringField('Centre (CRPC/CDT)', validators=[DataRequired()])
    mot_de_passe_actuel = PasswordField('Mot de passe actuel', validators=[Optional()])
    nouveau_mot_de_passe = PasswordField('Nouveau mot de passe', validators=[
        Optional(), Length(min=6, message='Le mot de passe doit comporter au moins 6 caractères.')
    ])
    confirmer = PasswordField('Confirmer le nouveau mot de passe', validators=[
        EqualTo('nouveau_mot_de_passe', message='Les mots de passe ne correspondent pas.')
    ])
    submit = SubmitField('Enregistrer les modifications')


class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    nom = StringField('Nom', validators=[DataRequired()])
    prenom = StringField('Prénom', validators=[DataRequired()])
    role = SelectField('Rôle', choices=[
        ('medecin', 'Médecin'),
        ('infirmier', 'Infirmier(e)'),
        ('coordinateur', 'Coordinateur PNLT'),
        ('laborantin', 'Laborantin(e)'),
    ])
    centre = StringField('Centre (CRPC/CDT)', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Confirmer', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField("Créer le compte")
