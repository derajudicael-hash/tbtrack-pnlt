from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ...models import EffetSecondaire, Patient
from ...extensions import db
from .forms import EffetForm
from ...utils.decorators import role_required
from datetime import datetime

effets_bp = Blueprint('effets', __name__, url_prefix='/effets')


@effets_bp.route('/')
@login_required
def liste():
    q      = request.args.get('q', '').strip()
    filtre = request.args.get('filtre', '')

    query = EffetSecondaire.query
    if q:
        query = query.join(Patient).filter(
            Patient.nom.ilike(f'%{q}%') |
            Patient.prenom.ilike(f'%{q}%') |
            Patient.code_patient.ilike(f'%{q}%') |
            EffetSecondaire.symptome.ilike(f'%{q}%') |
            EffetSecondaire.medicament_incrimine.ilike(f'%{q}%')
        )
    effets  = query.order_by(EffetSecondaire.date_declaration.desc()).all()
    alertes = [e for e in effets if e.alerte_active]
    severes = [e for e in effets if e.severite == 'severe']

    return render_template('effets/liste.html',
        effets=effets, alertes=alertes, severes=severes,
        q=q, filtre=filtre)


@effets_bp.route('/declarer', methods=['GET', 'POST'])
@login_required
@role_required('coordinateur', 'medecin', 'infirmier')
def declarer():
    form = EffetForm()
    # Tous les patients (pas uniquement "en_cours") — un effet peut survenir pour tout statut
    tous = Patient.query.order_by(Patient.nom, Patient.prenom).all()
    form.patient_id.choices = [(p.id, f'{p.code_patient} — {p.nom} {p.prenom} ({p.statut_label})')
                               for p in tous]

    # retour_patient_id : vient de GET (?patient_id=X) ou d'un POST échoué (hidden field)
    retour_patient_id = (request.args.get('patient_id', type=int)
                         or request.form.get('retour_patient_id', type=int))

    # Pré-sélection du patient si on vient de la fiche patient (GET uniquement)
    if request.method == 'GET' and retour_patient_id:
        form.patient_id.data = retour_patient_id

    if form.validate_on_submit():
        effet = EffetSecondaire(
            patient_id=form.patient_id.data,
            medicament_incrimine=form.medicament_incrimine.data,
            symptome=form.symptome.data,
            severite=form.severite.data,
            notes=form.notes.data,
            declare_par=current_user.full_name,
        )
        db.session.add(effet)
        db.session.commit()
        if effet.severite == 'severe':
            flash('⚠ Effet sévère enregistré — notification CRPC requise dans les 24h.', 'danger')
        else:
            flash('Effet secondaire déclaré avec succès.', 'success')
        pid = request.form.get('retour_patient_id', type=int)
        if pid:
            return redirect(url_for('patients.fiche', patient_id=pid, _anchor='tab-effets'))
        return redirect(url_for('effets.liste'))
    return render_template('effets/declarer.html', form=form,
                           retour_patient_id=retour_patient_id)


@effets_bp.route('/<int:effet_id>/notifier', methods=['POST'])
@login_required
@role_required('coordinateur', 'medecin', 'infirmier')
def marquer_notifie(effet_id):
    effet = EffetSecondaire.query.get_or_404(effet_id)
    effet.notifie_crpc = True
    effet.date_notification = datetime.utcnow()
    db.session.commit()
    flash('Notification CRPC enregistrée.', 'success')
    return redirect(url_for('effets.liste'))
