from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from ...models import User, Patient
from ...extensions import db
from .forms import UserCreateForm, UserEditForm

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def require_coordinateur():
    """Vérifie que l'utilisateur connecté est coordinateur, sinon retourne 403."""
    if not current_user.is_authenticated or current_user.role != 'coordinateur':
        abort(403)


@admin_bp.route('/utilisateurs')
@login_required
def utilisateurs():
    require_coordinateur()
    users = User.query.order_by(User.nom.asc()).all()
    # Calcul du nombre de patients par utilisateur (médecins)
    nb_patients_par_user = {}
    for u in users:
        nb_patients_par_user[u.id] = Patient.query.filter_by(medecin_id=u.id).count()
    return render_template('admin/users.html',
                           users=users,
                           nb_patients_par_user=nb_patients_par_user)


@admin_bp.route('/utilisateurs/<int:user_id>/toggle-actif', methods=['POST'])
@login_required
def toggle_actif(user_id):
    require_coordinateur()
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Vous ne pouvez pas désactiver votre propre compte.', 'warning')
        return redirect(url_for('admin.utilisateurs'))
    user.actif = not user.actif
    action = 'réactivé' if user.actif else 'désactivé'
    flash(f'Compte de {user.full_name} {action}.', 'success' if user.actif else 'info')
    db.session.commit()
    return redirect(url_for('admin.utilisateurs'))


@admin_bp.route('/utilisateurs/creer', methods=['GET', 'POST'])
@login_required
def creer_utilisateur():
    require_coordinateur()
    form = UserCreateForm()
    if form.validate_on_submit():
        # Vérifier que l'email n'est pas déjà utilisé
        existant = User.query.filter_by(email=form.email.data.lower()).first()
        if existant:
            flash('Cet email est déjà utilisé par un autre compte.', 'danger')
            return render_template('admin/creer_user.html', form=form)
        user = User(
            nom=form.nom.data.upper(),
            prenom=form.prenom.data,
            email=form.email.data.lower(),
            role=form.role.data,
            centre=form.centre.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Compte créé pour {user.full_name} ({user.role_label}).', 'success')
        return redirect(url_for('admin.utilisateurs'))
    return render_template('admin/creer_user.html', form=form)


@admin_bp.route('/utilisateurs/<int:user_id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_utilisateur(user_id):
    require_coordinateur()
    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)
    if form.validate_on_submit():
        user.nom = form.nom.data.upper()
        user.prenom = form.prenom.data
        user.role = form.role.data
        user.centre = form.centre.data
        db.session.commit()
        flash(f'Compte de {user.full_name} mis à jour.', 'success')
        return redirect(url_for('admin.utilisateurs'))
    return render_template('admin/modifier_user.html', form=form, user=user)
