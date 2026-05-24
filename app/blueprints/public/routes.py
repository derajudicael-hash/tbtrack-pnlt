from flask import Blueprint, render_template, redirect, url_for, session
from flask_login import current_user

public_bp = Blueprint('public', __name__)

ROLES_VALIDES = ('medecin', 'coordinateur', 'infirmier', 'laborantin')


@public_bp.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('public/landing_v2.html')


@public_bp.route('/choisir-role/<role>')
def choisir_role(role):
    if role in ROLES_VALIDES:
        session['role_selectionne'] = role
    return redirect(url_for('auth.login'))
