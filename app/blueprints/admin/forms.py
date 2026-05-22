from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Optional, Length


class UserCreateForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired(), Length(max=100)])
    prenom = StringField('Prénom', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Rôle', choices=[
        ('medecin', 'Médecin'),
        ('infirmier', 'Infirmier(e)'),
        ('coordinateur', 'Coordinateur PNLT'),
        ('laborantin', 'Laborantin(e)'),
    ])
    centre = StringField('Centre / Structure de santé', validators=[Optional(), Length(max=150)])
    password = PasswordField('Mot de passe', validators=[
        DataRequired(),
        Length(min=8, message='Le mot de passe doit comporter au moins 8 caractères.'),
    ])
    password_confirm = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(),
        EqualTo('password', message='Les mots de passe ne correspondent pas.'),
    ])
    submit = SubmitField('Créer le compte')


class UserEditForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired(), Length(max=100)])
    prenom = StringField('Prénom', validators=[DataRequired(), Length(max=100)])
    role = SelectField('Rôle', choices=[
        ('medecin', 'Médecin'),
        ('infirmier', 'Infirmier(e)'),
        ('coordinateur', 'Coordinateur PNLT'),
        ('laborantin', 'Laborantin(e)'),
    ])
    centre = StringField('Centre / Structure de santé', validators=[Optional(), Length(max=150)])
    submit = SubmitField('Enregistrer les modifications')
