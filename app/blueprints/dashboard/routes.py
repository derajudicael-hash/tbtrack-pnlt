from flask import Blueprint, render_template
from flask_login import login_required, current_user
from ...models import Patient, EffetSecondaire, Medicament, Contact, ExamenLabo, SuiviDOT
from datetime import date, timedelta

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/')
@login_required
def index():
    role = current_user.role

    patients = Patient.query.all()
    actifs   = [p for p in patients if p.statut == 'en_cours']

    if role == 'medecin':
        return _dashboard_medecin(actifs, patients)
    elif role == 'infirmier':
        return _dashboard_infirmier(actifs)
    elif role == 'laborantin':
        return _dashboard_laborantin(actifs)
    else:
        return _dashboard_coordinateur(actifs, patients)


# ── Médecin ──────────────────────────────────────────────────────────────────

def _dashboard_medecin(actifs, patients):
    alertes_effets = [e for e in EffetSecondaire.query.all() if e.alerte_active]
    patients_ecg   = [p for p in actifs if p.alerte_ecg_critique]
    patients_echec = [p for p in actifs if p.alerte_echec_therapeutique]

    date_30j = date.today() - timedelta(days=30)
    patients_sans_examen = []
    for p in actifs:
        if not p.examens_labo:
            patients_sans_examen.append(p)
        else:
            dernier = max(p.examens_labo, key=lambda e: e.date_prelevement)
            if (date.today() - dernier.date_prelevement).days > 30:
                patients_sans_examen.append(p)

    conversions_labels = [f'M{m}' for m in range(0, 7)]
    conversions_data   = [
        ExamenLabo.query.filter_by(mois_suivi=m, culture_resultat='negatif').count()
        for m in range(0, 7)
    ]

    statuts_labels = ['En cours', 'Guéri', 'Perdu de vue', 'Échec', 'Décédé']
    statuts_data   = [
        len(actifs),
        len([p for p in patients if p.statut == 'gueri']),
        len([p for p in patients if p.statut == 'perdu_de_vue']),
        len([p for p in patients if p.statut == 'echec']),
        len([p for p in patients if p.statut == 'decede']),
    ]

    patients_recents = Patient.query.order_by(Patient.created_at.desc()).limit(5).all()

    return render_template('dashboard/medecin.html',
        nb_actifs=len(actifs),
        nb_alertes_effets=len(alertes_effets),
        nb_ecg_urgents=len(patients_ecg),
        nb_sans_examen=len(patients_sans_examen),
        patients_ecg=patients_ecg[:5],
        patients_echec=patients_echec[:5],
        patients_sans_examen=patients_sans_examen[:5],
        patients_recents=patients_recents,
        conversions_labels=conversions_labels,
        conversions_data=conversions_data,
        statuts_labels=statuts_labels,
        statuts_data=statuts_data,
    )


# ── Infirmier ─────────────────────────────────────────────────────────────────

def _dashboard_infirmier(actifs):
    today = date.today()

    # Adhérence DOT sur 30 jours
    date_30j  = today - timedelta(days=30)
    dots_30j  = SuiviDOT.query.filter(SuiviDOT.date_observation >= date_30j).all()
    if dots_30j:
        nb_prises     = sum(1 for d in dots_30j if d.prise_confirmee)
        adherence_pct = round(nb_prises / len(dots_30j) * 100, 1)
    else:
        adherence_pct = None

    # DOT d'aujourd'hui manquants (seulement pour les patients avec traitement actif)
    dots_aujourd_hui = SuiviDOT.query.filter_by(date_observation=today).all()
    patients_avec_dot = {d.patient_id for d in dots_aujourd_hui}
    patients_sans_dot = [
        p for p in actifs
        if p.id not in patients_avec_dot and p.traitement_actif is not None
    ]

    # Absences consécutives ≥ 2 jours (seulement patients avec traitement actif démarré ≥ 2j)
    patients_absents = []
    hier    = today - timedelta(days=1)
    avant_h = today - timedelta(days=2)
    for p in actifs:
        t = p.traitement_actif
        if t is None:
            continue
        if t.date_debut and (today - t.date_debut).days < 2:
            continue
        dot_hier    = SuiviDOT.query.filter_by(patient_id=p.id, date_observation=hier).first()
        dot_avant_h = SuiviDOT.query.filter_by(patient_id=p.id, date_observation=avant_h).first()
        absent_hier    = not dot_hier or not dot_hier.prise_confirmee
        absent_avant_h = not dot_avant_h or not dot_avant_h.prise_confirmee
        if absent_hier and absent_avant_h:
            patients_absents.append(p)

    effets_recents = EffetSecondaire.query.order_by(
        EffetSecondaire.date_declaration.desc()
    ).limit(5).all()
    alertes_effets = [e for e in EffetSecondaire.query.all() if e.alerte_active]

    return render_template('dashboard/infirmier.html',
        nb_actifs=len(actifs),
        nb_sans_dot_aujourd_hui=len(patients_sans_dot),
        nb_absents_consecutifs=len(patients_absents),
        nb_alertes_effets=len(alertes_effets),
        adherence_pct=adherence_pct,
        patients_absents=patients_absents[:8],
        patients_sans_dot=patients_sans_dot[:8],
        effets_recents=effets_recents,
    )


# ── Laborantin ────────────────────────────────────────────────────────────────

def _dashboard_laborantin(actifs):
    today     = date.today()
    debut_m   = date(today.year, today.month, 1)

    examens_mois = ExamenLabo.query.filter(
        ExamenLabo.date_prelevement >= debut_m
    ).count()

    cultures_pos = ExamenLabo.query.filter_by(culture_resultat='positif').count()

    # Examens attendus mais pas encore saisis (patient actif, dernier examen > 30 jours)
    patients_en_attente = []
    for p in actifs:
        if not p.examens_labo:
            patients_en_attente.append(p)
        else:
            dernier = max(p.examens_labo, key=lambda e: e.date_prelevement)
            if (today - dernier.date_prelevement).days > 30:
                patients_en_attente.append(p)

    examens_recents = ExamenLabo.query.order_by(
        ExamenLabo.date_prelevement.desc()
    ).limit(10).all()

    conversions_labels = [f'M{m}' for m in range(0, 7)]
    conversions_data   = [
        ExamenLabo.query.filter_by(mois_suivi=m, culture_resultat='negatif').count()
        for m in range(0, 7)
    ]

    return render_template('dashboard/laborantin.html',
        nb_actifs=len(actifs),
        examens_mois=examens_mois,
        cultures_pos=cultures_pos,
        nb_en_attente=len(patients_en_attente),
        patients_en_attente=patients_en_attente[:8],
        examens_recents=examens_recents,
        conversions_labels=conversions_labels,
        conversions_data=conversions_data,
    )


# ── Coordinateur (full view) ──────────────────────────────────────────────────

def _dashboard_coordinateur(actifs, patients):
    gueris  = [p for p in patients if p.statut == 'gueri']
    perdus  = [p for p in patients if p.statut == 'perdu_de_vue']
    echecs  = [p for p in patients if p.statut == 'echec']

    alertes       = [e for e in EffetSecondaire.query.all() if e.alerte_active]
    stocks        = Medicament.query.all()
    stocks_bas    = [m for m in stocks if m.stock_bas]
    contacts      = Contact.query.filter_by(statut='en_suivi').all()
    contacts_urg  = [c for c in contacts
                     if c.date_prochaine_visite and
                     c.date_prochaine_visite <= date.today() + timedelta(days=7)]

    patients_recents = Patient.query.order_by(Patient.created_at.desc()).limit(5).all()

    statuts_labels = ['En cours', 'Guéri', 'Perdu de vue', 'Échec', 'Décédé', 'Terminé']
    statuts_data   = [
        len(actifs), len(gueris), len(perdus), len(echecs),
        len([p for p in patients if p.statut == 'decede']),
        len([p for p in patients if p.statut == 'termine']),
    ]

    today      = date.today()
    mois_labels = []
    mois_data   = []
    for i in range(5, -1, -1):
        mois_date  = date(today.year, today.month, 1) - timedelta(days=30 * i)
        m_next     = mois_date.month % 12 + 1
        y_next     = mois_date.year + (1 if mois_date.month == 12 else 0)
        mois_fin   = date(y_next, m_next, 1)
        count      = Patient.query.filter(
            Patient.date_debut_traitement >= mois_date,
            Patient.date_debut_traitement < mois_fin,
        ).count()
        mois_labels.append(mois_date.strftime('%b %Y'))
        mois_data.append(count)

    cohorte_labels = ['Guéri', 'Échec', 'Perdu de vue', 'Décédé', 'Non évalué']
    cohorte_data   = [
        len(gueris), len(echecs), len(perdus),
        len([p for p in patients if p.statut == 'decede']),
        len([p for p in patients if p.statut in ('non_evalue', 'transfert')]),
    ]

    conversions_labels = [f'M{m}' for m in range(0, 7)]
    conversions_data   = [
        ExamenLabo.query.filter_by(mois_suivi=m, culture_resultat='negatif').count()
        for m in range(0, 7)
    ]

    date_30j       = today - timedelta(days=30)
    dots_recents   = SuiviDOT.query.filter(SuiviDOT.date_observation >= date_30j).all()
    if dots_recents:
        nb_prises        = sum(1 for d in dots_recents if d.prise_confirmee)
        adherence_globale = round(nb_prises / len(dots_recents) * 100, 1)
    else:
        adherence_globale = None

    patients_sans_examen  = []
    patients_ecg_urgents  = [p for p in actifs if p.alerte_ecg_critique]
    patients_echec_pot    = [p for p in actifs if p.alerte_echec_therapeutique]
    for p in actifs:
        if not p.examens_labo:
            patients_sans_examen.append(p)
        else:
            dernier = max(p.examens_labo, key=lambda e: e.date_prelevement)
            if (today - dernier.date_prelevement).days > 30:
                patients_sans_examen.append(p)

    return render_template('dashboard/index.html',
        total_patients=len(patients),
        nb_actifs=len(actifs),
        nb_alertes=len(alertes),
        nb_stocks_bas=len(stocks_bas),
        nb_contacts_urgents=len(contacts_urg),
        effets_recents=alertes[:5],
        patients_recents=patients_recents,
        statuts_labels=statuts_labels,
        statuts_data=statuts_data,
        mois_labels=mois_labels,
        mois_data=mois_data,
        cohorte_labels=cohorte_labels,
        cohorte_data=cohorte_data,
        conversions_labels=conversions_labels,
        conversions_data=conversions_data,
        adherence_globale=adherence_globale,
        patients_sans_examen=patients_sans_examen[:5],
        patients_ecg_urgents=patients_ecg_urgents,
        patients_echec_potentiel=patients_echec_pot,
    )
