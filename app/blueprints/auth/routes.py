from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from ...models import User
from ...extensions import db
from .forms import LoginForm, RegisterForm, ProfilForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data):
            if not user.actif:
                flash('Votre compte n\'est pas encore activé. Contactez votre coordinateur PNLT.', 'warning')
                return render_template('auth/login.html', form=form)
            login_user(user, remember=form.remember.data)
            session.pop('role_selectionne', None)
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        flash('Email ou mot de passe incorrect.', 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash('Cet email est déjà utilisé.', 'danger')
            return redirect(url_for('auth.register'))
        user = User(email=form.email.data.lower(), nom=form.nom.data.upper(),
                    prenom=form.prenom.data, role=form.role.data, centre=form.centre.data,
                    actif=False)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Compte créé. Il sera activé par votre coordinateur PNLT avant que vous puissiez vous connecter.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth_bp.route('/profil', methods=['GET', 'POST'])
@login_required
def profil():
    form = ProfilForm(obj=current_user)
    if form.validate_on_submit():
        # Vérifier le mot de passe actuel si un nouveau est demandé
        if form.nouveau_mot_de_passe.data:
            if not form.mot_de_passe_actuel.data:
                flash('Veuillez entrer votre mot de passe actuel pour le modifier.', 'danger')
                return render_template('auth/profil.html', form=form)
            if not current_user.check_password(form.mot_de_passe_actuel.data):
                flash('Mot de passe actuel incorrect.', 'danger')
                return render_template('auth/profil.html', form=form)
            current_user.set_password(form.nouveau_mot_de_passe.data)
        current_user.prenom = form.prenom.data
        current_user.nom = form.nom.data.upper()
        current_user.centre = form.centre.data
        db.session.commit()
        flash('Profil mis à jour avec succès.', 'success')
        return redirect(url_for('auth.profil'))
    return render_template('auth/profil.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
