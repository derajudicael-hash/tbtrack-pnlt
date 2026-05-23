from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from ...models import ExamenLabo, Patient
from ...extensions import db
from .forms import ExamenLaboForm
from datetime import date

labo_bp = Blueprint('labo', __name__, url_prefix='/labo')


def _labo_required():
    if current_user.role not in ('laborantin', 'coordinateur', 'medecin'):
        abort(403)


@labo_bp.route('/')
@login_required
def index():
    _labo_required()
    q = request.args.get('q', '').strip()
    mois = request.args.get('mois', '')

    examens = (ExamenLabo.query
               .join(Patient)
               .order_by(ExamenLabo.date_prelevement.desc()))

    if q:
        examens = examens.filter(
            Patient.nom.ilike(f'%{q}%') |
            Patient.prenom.ilike(f'%{q}%') |
            Patient.code_patient.ilike(f'%{q}%')
        )
    if mois != '':
        try:
            examens = examens.filter(ExamenLabo.mois_suivi == int(mois))
        except ValueError:
            pass

    examens = examens.all()

    patients_actifs = Patient.query.filter_by(statut='en_cours').count()
    total_examens = ExamenLabo.query.count()
    conversions = ExamenLabo.query.filter_by(culture_resultat='negatif').count()
    en_attente = ExamenLabo.query.filter_by(culture_resultat='en_attente').count()

    stats = {
        'patients_actifs': patients_actifs,
        'total_examens': total_examens,
        'conversions': conversions,
        'en_attente': en_attente,
    }

    return render_template('labo/index.html', examens=examens, stats=stats, q=q, mois=mois)


@labo_bp.route('/saisir', methods=['GET', 'POST'])
@login_required
def saisir():
    _labo_required()
    form = ExamenLaboForm()
    tous = Patient.query.order_by(Patient.nom, Patient.prenom).all()
    form.patient_id.choices = [(p.id, f'{p.code_patient} — {p.nom} {p.prenom} ({p.statut_label})')
                               for p in tous]

    if form.validate_on_submit():
        examen = ExamenLabo(
            patient_id=form.patient_id.data,
            laborantin_id=current_user.id,
            mois_suivi=form.mois_suivi.data,
            date_prelevement=form.date_prelevement.data,
            date_resultat=form.date_resultat.data,
            genexpert_effectue=form.genexpert_effectue.data,
            genexpert_resultat=form.genexpert_resultat.data or None,
            genexpert_resistance_rif=form.genexpert_resistance_rif.data or None,
            frottis_effectue=form.frottis_effectue.data,
            frottis_resultat=form.frottis_resultat.data or None,
            frottis_quantite=form.frottis_quantite.data or None,
            culture_effectuee=form.culture_effectuee.data,
            culture_resultat=form.culture_resultat.data or None,
            culture_milieu=form.culture_milieu.data or None,
            dst_effectue=form.dst_effectue.data,
            dst_isoniazide=form.dst_isoniazide.data or None,
            dst_rifampicine=form.dst_rifampicine.data or None,
            dst_ethambutol=form.dst_ethambutol.data or None,
            dst_pyrazinamide=form.dst_pyrazinamide.data or None,
            dst_levofloxacine=form.dst_levofloxacine.data or None,
            dst_moxifloxacine=form.dst_moxifloxacine.data or None,
            dst_bedaquiline=form.dst_bedaquiline.data or None,
            dst_linezolide=form.dst_linezolide.data or None,
            dst_amikacine=form.dst_amikacine.data or None,
            dst_kanamycine=form.dst_kanamycine.data or None,
            dst_capreomycine=form.dst_capreomycine.data or None,
            dst_ofloxacine=form.dst_ofloxacine.data or None,
            notes=form.notes.data,
        )
        db.session.add(examen)
        db.session.commit()

        patient = Patient.query.get(form.patient_id.data)
        flash(f'Résultats M{form.mois_suivi.data} enregistrés pour {patient.nom} {patient.prenom}.', 'success')

        if examen.culture_resultat == 'negatif':
            flash(f'Conversion bactériologique confirmée à M{form.mois_suivi.data} !', 'info')

        # Retour à la fiche patient si on venait de là
        retour_patient_id = request.form.get('retour_patient_id', type=int)
        if retour_patient_id:
            return redirect(url_for('patients.fiche', patient_id=retour_patient_id,
                                    _anchor='tab-labo'))
        return redirect(url_for('labo.index'))

    patient_id = request.args.get('patient_id', type=int)
    # Conserver retour_patient_id même après un échec de validation (POST)
    retour_patient_id = patient_id or request.form.get('retour_patient_id', type=int)
    if patient_id:
        form.patient_id.data = patient_id

    return render_template('labo/saisir.html', form=form, retour_patient_id=retour_patient_id)


@labo_bp.route('/<int:examen_id>')
@login_required
def detail(examen_id):
    _labo_required()
    examen = ExamenLabo.query.get_or_404(examen_id)
    return render_template('labo/detail.html', examen=examen)


@labo_bp.route('/<int:examen_id>/supprimer', methods=['POST'])
@login_required
def supprimer(examen_id):
    if current_user.role not in ('laborantin', 'coordinateur'):
        abort(403)
    examen = ExamenLabo.query.get_or_404(examen_id)
    db.session.delete(examen)
    db.session.commit()
    flash('Examen supprimé.', 'info')
    return redirect(url_for('labo.index'))


@labo_bp.route('/patient/<int:patient_id>')
@login_required
def suivi_patient(patient_id):
    _labo_required()
    patient = Patient.query.get_or_404(patient_id)
    examens = (ExamenLabo.query
               .filter_by(patient_id=patient_id)
               .order_by(ExamenLabo.mois_suivi)
               .all())
    return render_template('labo/suivi_patient.html', patient=patient, examens=examens)
