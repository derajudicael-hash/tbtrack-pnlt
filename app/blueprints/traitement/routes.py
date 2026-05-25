import json
from datetime import date, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from ...models import Traitement, Patient, SuiviDOT
from ...utils.decorators import role_required
from ...utils.notifier import notifier_roles
from ...extensions import db
from .forms import TraitementForm, SuiviDOTForm, BilanInitialForm, GROUPES_MEDICAMENTS

traitement_bp = Blueprint('traitement', __name__, url_prefix='/traitement')


@traitement_bp.route('/')
@login_required
def liste():
    q      = request.args.get('q', '').strip()
    filtre = request.args.get('filtre', '')
    today  = date.today()

    query = Traitement.query.join(Patient)
    if q:
        query = query.filter(
            Patient.nom.ilike(f'%{q}%') |
            Patient.prenom.ilike(f'%{q}%') |
            Patient.code_patient.ilike(f'%{q}%')
        )
    traitements = query.order_by(Traitement.date_debut.desc()).all()

    # DOT saisis aujourd'hui
    dots_ids = {d.patient_id for d in SuiviDOT.query.filter_by(date_observation=today).all()}
    nb_dot_aujourd_hui = len(dots_ids)

    # Traitements actifs sans DOT aujourd'hui
    dot_manquants = [
        t for t in traitements
        if t.statut_traitement == 'actif'
        and t.patient.statut == 'en_cours'
        and t.patient.id not in dots_ids
    ]

    return render_template('traitement/liste.html',
        traitements=traitements,
        dot_manquants=dot_manquants,
        nb_dot_aujourd_hui=nb_dot_aujourd_hui,
        q=q, filtre=filtre)


@traitement_bp.route('/ajouter/<int:patient_id>', methods=['GET', 'POST'])
@login_required
@role_required('coordinateur', 'medecin')
def ajouter(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = TraitementForm()
    if form.validate_on_submit():
        # Récupération de la liste médicaments depuis le hidden field JSON
        medicaments = []
        raw = form.medicaments_json.data
        if raw:
            try:
                medicaments = json.loads(raw)
            except (ValueError, TypeError):
                medicaments = []
        traitement = Traitement(
            patient_id=patient_id,
            schema_nom=form.schema_nom.data,
            phase=form.phase.data,
            date_debut=form.date_debut.data,
            date_fin_prevue=form.date_fin_prevue.data,
            statut_traitement=form.statut_traitement.data,
            observateur_nom=form.observateur_nom.data,
            date_fin_reelle=form.date_fin_reelle.data,
            motif_arret=form.motif_arret.data,
            notes=form.notes.data,
        )
        traitement.medicaments = medicaments
        db.session.add(traitement)
        db.session.commit()
        flash(f'Traitement enregistré pour {patient.code_patient}.', 'success')
        return redirect(url_for('traitement.detail', traitement_id=traitement.id))
    # Pré-remplir la date de début avec la date du jour
    if not form.date_debut.data:
        form.date_debut.data = date.today()
    return render_template('traitement/ajouter.html',
                           form=form,
                           patient=patient,
                           groupes_medicaments=GROUPES_MEDICAMENTS)


@traitement_bp.route('/<int:traitement_id>/modifier', methods=['GET', 'POST'])
@login_required
@role_required('coordinateur', 'medecin')
def modifier(traitement_id):
    traitement = Traitement.query.get_or_404(traitement_id)
    patient = traitement.patient
    form = TraitementForm(obj=traitement)
    if request.method == 'GET':
        # Pré-remplir le hidden field avec les médicaments actuels
        form.medicaments_json.data = json.dumps(traitement.medicaments)
    if form.validate_on_submit():
        medicaments = []
        raw = form.medicaments_json.data
        if raw:
            try:
                medicaments = json.loads(raw)
            except (ValueError, TypeError):
                medicaments = []
        traitement.schema_nom = form.schema_nom.data
        traitement.phase = form.phase.data
        traitement.date_debut = form.date_debut.data
        traitement.date_fin_prevue = form.date_fin_prevue.data
        traitement.statut_traitement = form.statut_traitement.data
        traitement.observateur_nom = form.observateur_nom.data
        traitement.date_fin_reelle = form.date_fin_reelle.data
        traitement.motif_arret = form.motif_arret.data
        traitement.notes = form.notes.data
        traitement.medicaments = medicaments
        db.session.commit()
        flash('Traitement mis à jour.', 'success')
        return redirect(url_for('traitement.detail', traitement_id=traitement.id))
    return render_template('traitement/ajouter.html',
                           form=form,
                           patient=patient,
                           traitement=traitement,
                           groupes_medicaments=GROUPES_MEDICAMENTS,
                           modification=True)


@traitement_bp.route('/<int:traitement_id>/supprimer', methods=['POST'])
@login_required
@role_required('coordinateur', 'medecin')
def supprimer(traitement_id):
    traitement = Traitement.query.get_or_404(traitement_id)
    patient_id = traitement.patient_id
    db.session.delete(traitement)
    db.session.commit()
    flash('Traitement supprimé.', 'info')
    return redirect(url_for('patients.fiche', patient_id=patient_id))


@traitement_bp.route('/<int:traitement_id>')
@login_required
def detail(traitement_id):
    traitement = Traitement.query.get_or_404(traitement_id)
    patient = traitement.patient

    # Calcul du taux d'adhérence DOT sur 30 jours
    taux_adherence = SuiviDOT.taux_adherence(patient.id, traitement_id, nb_jours=30)

    # Dernières 30 prises DOT
    dot_recent = SuiviDOT.query.filter_by(
        traitement_id=traitement_id
    ).order_by(SuiviDOT.date_observation.desc()).limit(30).all()

    # Construction de la timeline M0-M18 ou M0-M11 selon le schéma
    nb_mois = 18 if patient.schema_therapeutique == 'long' else 11
    jalons = []
    for m in range(nb_mois + 1):
        if traitement.date_debut:
            from datetime import timedelta
            date_jalon = date(
                traitement.date_debut.year,
                traitement.date_debut.month,
                1,
            )
            # Avancer de m mois
            mois_total = date_jalon.month + m
            annee = date_jalon.year + (mois_total - 1) // 12
            mois = ((mois_total - 1) % 12) + 1
            date_jalon = date(annee, mois, 1)
        else:
            date_jalon = None

        # Examen labo du mois m pour ce patient
        examen = None
        for e in patient.examens_labo:
            if e.mois_suivi == m:
                examen = e
                break

        jalons.append({
            'mois': m,
            'date': date_jalon,
            'examen': examen,
            'passe': traitement.mois_ecoules >= m if traitement.date_debut else False,
            'actuel': traitement.mois_ecoules == m,
        })

    return render_template('traitement/detail.html',
                           traitement=traitement,
                           patient=patient,
                           jalons=jalons,
                           nb_mois=nb_mois,
                           taux_adherence=taux_adherence,
                           dot_recent=dot_recent)


@traitement_bp.route('/<int:traitement_id>/dot/ajouter', methods=['GET', 'POST'])
@login_required
@role_required('coordinateur', 'medecin', 'infirmier')
def dot_ajouter(traitement_id):
    traitement = Traitement.query.get_or_404(traitement_id)
    patient = traitement.patient
    form = SuiviDOTForm()
    if not form.date_observation.data:
        form.date_observation.data = date.today()
    # Paramètre pour revenir à la fiche patient après saisie
    depuis_fiche = request.args.get('depuis_fiche', '0')
    if form.validate_on_submit():
        doublon = SuiviDOT.query.filter_by(
            patient_id=patient.id,
            traitement_id=traitement_id,
            date_observation=form.date_observation.data,
        ).first()
        if doublon:
            flash(f'Une prise DOT existe déjà pour le {form.date_observation.data.strftime("%d/%m/%Y")}. Modifier la date ou consulter l\'historique.', 'warning')
            return render_template('traitement/dot_ajouter.html',
                                   form=form, traitement=traitement,
                                   patient=patient, depuis_fiche=depuis_fiche)

        medicaments_pris = traitement.medicaments if form.prise_confirmee.data else []
        medicaments_omis = [] if form.prise_confirmee.data else traitement.medicaments

        dot = SuiviDOT(
            patient_id=patient.id,
            traitement_id=traitement_id,
            date_observation=form.date_observation.data,
            prise_confirmee=form.prise_confirmee.data,
            observateur_nom=form.observateur_nom.data,
            observateur_role=form.observateur_role.data,
            raison_omission=form.raison_omission.data if not form.prise_confirmee.data else None,
            notes=form.notes.data,
        )
        dot.medicaments_pris = medicaments_pris
        dot.medicaments_omis = medicaments_omis
        db.session.add(dot)
        db.session.commit()
        # Alerte DOT manqué 2 jours consécutifs
        if not form.prise_confirmee.data:
            date_obs = form.date_observation.data
            jour_precedent = date_obs - timedelta(days=1)
            dot_precedent = SuiviDOT.query.filter_by(
                patient_id=patient.id,
                traitement_id=traitement_id,
                date_observation=jour_precedent,
            ).first()
            if dot_precedent and not dot_precedent.prise_confirmee:
                notifier_roles(
                    ['infirmier', 'medecin', 'coordinateur'],
                    f'DOT manqué 2 jours consécutifs : {patient.code_patient} {patient.nom} {patient.prenom} — {jour_precedent.strftime("%d/%m")} et {date_obs.strftime("%d/%m/%Y")}.',
                    type_notif='warning',
                    url=url_for('traitement.detail', traitement_id=traitement_id),
                    ref=f'dot_absent_{patient.id}_{date_obs}',
                )
                db.session.commit()
        statut = 'confirmée' if form.prise_confirmee.data else 'non confirmée'
        flash(f'Prise DOT du {form.date_observation.data.strftime("%d/%m/%Y")} ({statut}) enregistrée.', 'success')
        retour = request.form.get('depuis_fiche', '0')
        if retour == '1':
            return redirect(url_for('patients.fiche', patient_id=patient.id,
                                    _anchor='tab-dot'))
        return redirect(url_for('traitement.detail', traitement_id=traitement_id))
    return render_template('traitement/dot_ajouter.html',
                           form=form,
                           traitement=traitement,
                           patient=patient,
                           depuis_fiche=depuis_fiche)


@traitement_bp.route('/<int:traitement_id>/dot/historique')
@login_required
def dot_historique(traitement_id):
    traitement = Traitement.query.get_or_404(traitement_id)
    patient = traitement.patient
    dots = SuiviDOT.query.filter_by(
        traitement_id=traitement_id
    ).order_by(SuiviDOT.date_observation.desc()).all()
    taux = SuiviDOT.taux_adherence(patient.id, traitement_id, nb_jours=30)
    return render_template('traitement/dot_historique.html',
                           traitement=traitement,
                           patient=patient,
                           dots=dots,
                           taux_adherence=taux)
