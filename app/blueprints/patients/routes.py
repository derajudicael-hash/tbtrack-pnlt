from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ...models import Patient, EffetSecondaire, Contact, Traitement, BilanInitial, SuiviPonderal, NoteClinique
from ...extensions import db
from .forms import PatientForm, SuiviPonderalForm
from ..traitement.forms import BilanInitialForm
from ...utils.decorators import role_required
from datetime import date

patients_bp = Blueprint('patients', __name__, url_prefix='/patients')


def _generate_code():
    """Génère un code unique en extrayant le plus grand numéro existant."""
    import re
    codes = [p.code_patient for p in Patient.query.with_entities(Patient.code_patient).all()]
    nums = []
    for c in codes:
        m = re.search(r'(\d+)$', c or '')
        if m:
            nums.append(int(m.group(1)))
    n = (max(nums) + 1) if nums else 1
    code = f'TB-MR-{n:04d}'
    while Patient.query.filter_by(code_patient=code).first():
        n += 1
        code = f'TB-MR-{n:04d}'
    return code


@patients_bp.route('/')
@login_required
def liste():
    q = request.args.get('q', '').strip()
    statut = request.args.get('statut', '')
    resistance = request.args.get('resistance', '')

    query = Patient.query
    if q:
        query = query.filter(
            (Patient.nom.ilike(f'%{q}%')) | (Patient.prenom.ilike(f'%{q}%')) | (Patient.code_patient.ilike(f'%{q}%'))
        )
    if statut:
        query = query.filter_by(statut=statut)
    if resistance:
        query = query.filter_by(type_resistance=resistance)

    patients = query.order_by(Patient.created_at.desc()).all()
    return render_template('patients/liste.html', patients=patients, q=q, statut=statut, resistance=resistance)


@patients_bp.route('/ajouter', methods=['GET', 'POST'])
@login_required
@role_required('coordinateur', 'medecin', 'infirmier')
def ajouter():
    form = PatientForm()
    if form.validate_on_submit():
        patient = Patient(
            code_patient=_generate_code(),
            nom=form.nom.data.upper(),
            prenom=form.prenom.data,
            date_naissance=form.date_naissance.data,
            sexe=form.sexe.data,
            adresse=form.adresse.data,
            telephone=form.telephone.data,
            poids=form.poids.data,
            statut_vih=form.statut_vih.data,
            date_diagnostic=form.date_diagnostic.data,
            type_resistance=form.type_resistance.data,
            categorie=form.categorie.data,
            statut=form.statut.data,
            schema_therapeutique=form.schema_therapeutique.data,
            date_debut_traitement=form.date_debut_traitement.data,
            notes_cliniques=form.notes_cliniques.data,
            date_sortie=form.date_sortie.data,
            motif_sortie=form.motif_sortie.data,
            centre_transfert=form.centre_transfert.data,
            medecin_id=current_user.id,
        )
        db.session.add(patient)
        db.session.commit()
        flash(f'Patient {patient.code_patient} enregistré avec succès.', 'success')
        return redirect(url_for('patients.fiche', patient_id=patient.id))
    return render_template('patients/ajouter.html', form=form, titre='Nouveau patient')


@patients_bp.route('/<int:patient_id>')
@login_required
def fiche(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    traitement = Traitement.query.filter_by(patient_id=patient_id).order_by(Traitement.created_at.desc()).first()
    effets = EffetSecondaire.query.filter_by(patient_id=patient_id).order_by(EffetSecondaire.date_declaration.desc()).all()
    contacts = Contact.query.filter_by(patient_source_id=patient_id).all()
    bilan = BilanInitial.query.filter_by(patient_id=patient_id).first()
    notes = patient.notes.order_by(NoteClinique.created_at.desc()).all()

    # Calcul adhérence DOT (30 derniers jours)
    taux_adherence = None
    dot_recent = []
    if traitement:
        from ...models import SuiviDOT
        taux_adherence = SuiviDOT.taux_adherence(patient_id, traitement.id, nb_jours=30)
        dot_recent = (patient.suivi_dot
                      .filter_by(traitement_id=traitement.id)
                      .limit(30).all())

    return render_template('patients/fiche.html',
                           patient=patient,
                           traitement=traitement,
                           effets=effets,
                           contacts=contacts,
                           bilan=bilan,
                           notes=notes,
                           taux_adherence=taux_adherence,
                           dot_recent=dot_recent)


@patients_bp.route('/<int:patient_id>/modifier', methods=['GET', 'POST'])
@login_required
@role_required('coordinateur', 'medecin')
def modifier(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = PatientForm(obj=patient)
    if form.validate_on_submit():
        form.populate_obj(patient)
        patient.nom = patient.nom.upper()
        db.session.commit()
        flash('Patient mis à jour.', 'success')
        return redirect(url_for('patients.fiche', patient_id=patient.id))
    return render_template('patients/ajouter.html', form=form, titre='Modifier le patient', patient=patient)


@patients_bp.route('/<int:patient_id>/supprimer', methods=['POST'])
@login_required
@role_required('coordinateur')
def supprimer(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    db.session.delete(patient)
    db.session.commit()
    flash('Patient supprimé.', 'info')
    return redirect(url_for('patients.liste'))


@patients_bp.route('/<int:patient_id>/bilan', methods=['GET', 'POST'])
@login_required
@role_required('coordinateur', 'medecin')
def bilan(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    bilan_existant = BilanInitial.query.filter_by(patient_id=patient_id).first()
    form = BilanInitialForm(obj=bilan_existant)

    if form.validate_on_submit():
        if bilan_existant:
            # Mise à jour du bilan existant
            form.populate_obj(bilan_existant)
            db.session.commit()
            flash('Bilan M0 mis à jour.', 'success')
        else:
            # Création d'un nouveau bilan
            nouveau_bilan = BilanInitial(patient_id=patient_id)
            form.populate_obj(nouveau_bilan)
            db.session.add(nouveau_bilan)
            db.session.commit()
            flash('Bilan initial M0 enregistré.', 'success')
        return redirect(url_for('patients.fiche', patient_id=patient_id, _anchor='tab-bilan'))

    if not form.date_bilan.data:
        form.date_bilan.data = bilan_existant.date_bilan if bilan_existant else date.today()

    return render_template('patients/bilan.html',
                           form=form,
                           patient=patient,
                           bilan=bilan_existant)


# ── Suivi pondéral mensuel ────────────────────────────────────────────────────

@patients_bp.route('/<int:patient_id>/parametres', methods=['GET', 'POST'])
@login_required
@role_required('coordinateur', 'medecin', 'infirmier')
def parametres(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = SuiviPonderalForm()
    if form.validate_on_submit():
        existant = SuiviPonderal.query.filter_by(
            patient_id=patient_id, mois_suivi=form.mois_suivi.data
        ).first()
        if existant:
            flash(f'Une mesure existe déjà pour M{form.mois_suivi.data}. Supprimez-la avant d\'en créer une nouvelle.', 'warning')
            historique = patient.suivi_ponderal.all()
            return render_template('patients/parametres.html',
                                   patient=patient, form=form, historique=historique)
        mesure = SuiviPonderal(
            patient_id=patient_id,
            mois_suivi=form.mois_suivi.data,
            date_mesure=form.date_mesure.data,
            poids=form.poids.data,
            taille=form.taille.data or None,
            tension_sys=form.tension_sys.data or None,
            tension_dia=form.tension_dia.data or None,
            temperature=form.temperature.data or None,
            kaliemie_mmol_l=form.kaliemie_mmol_l.data or None,
            creatinine_umol_l=form.creatinine_umol_l.data or None,
            gpt_u_l=form.gpt_u_l.data or None,
            got_u_l=form.got_u_l.data or None,
            leucocytes_g_l=form.leucocytes_g_l.data or None,
            plaquettes_g_l=form.plaquettes_g_l.data or None,
            notes=form.notes.data,
        )
        db.session.add(mesure)
        db.session.commit()
        flash(f'Paramètres M{form.mois_suivi.data} enregistrés.', 'success')
        return redirect(url_for('patients.parametres', patient_id=patient_id))
    form.date_mesure.data = form.date_mesure.data or date.today()
    historique = patient.suivi_ponderal.all()
    return render_template('patients/parametres.html',
                           patient=patient, form=form, historique=historique)


@patients_bp.route('/<int:patient_id>/parametres/<int:mesure_id>/supprimer', methods=['POST'])
@login_required
@role_required('coordinateur', 'medecin')
def parametres_supprimer(patient_id, mesure_id):
    mesure = SuiviPonderal.query.get_or_404(mesure_id)
    db.session.delete(mesure)
    db.session.commit()
    flash('Mesure supprimée.', 'info')
    return redirect(url_for('patients.parametres', patient_id=patient_id))


# ── Notes cliniques ───────────────────────────────────────────────────────────

@patients_bp.route('/<int:patient_id>/notes/ajouter', methods=['POST'])
@login_required
@role_required('coordinateur', 'medecin', 'infirmier')
def note_ajouter(patient_id):
    Patient.query.get_or_404(patient_id)
    contenu = request.form.get('contenu', '').strip()
    if not contenu:
        flash('La note ne peut pas être vide.', 'warning')
        return redirect(url_for('patients.fiche', patient_id=patient_id, _anchor='tab-notes'))
    note = NoteClinique(patient_id=patient_id, auteur_id=current_user.id, contenu=contenu)
    db.session.add(note)
    db.session.commit()
    flash('Note ajoutée.', 'success')
    return redirect(url_for('patients.fiche', patient_id=patient_id, _anchor='tab-notes'))


@patients_bp.route('/<int:patient_id>/notes/<int:note_id>/supprimer', methods=['POST'])
@login_required
@role_required('coordinateur', 'medecin')
def note_supprimer(patient_id, note_id):
    note = NoteClinique.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    flash('Note supprimée.', 'info')
    return redirect(url_for('patients.fiche', patient_id=patient_id, _anchor='tab-notes'))
