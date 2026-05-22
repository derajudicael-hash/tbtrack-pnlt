from flask import Blueprint, render_template
from flask_login import login_required
from ...models import Patient, EffetSecondaire, Medicament, Contact, ExamenLabo, SuiviDOT
from datetime import date, timedelta

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/')
@login_required
def index():
    patients = Patient.query.all()
    actifs = [p for p in patients if p.statut == 'en_cours']
    gueris = [p for p in patients if p.statut == 'gueri']
    perdus = [p for p in patients if p.statut == 'perdu_de_vue']
    echecs = [p for p in patients if p.statut == 'echec']

    effets_recents = EffetSecondaire.query.order_by(EffetSecondaire.date_declaration.desc()).limit(5).all()
    alertes = [e for e in EffetSecondaire.query.all() if e.alerte_active]

    stocks = Medicament.query.all()
    stocks_bas = [m for m in stocks if m.stock_bas]

    contacts = Contact.query.filter_by(statut='en_suivi').all()
    contacts_urgents = [c for c in contacts if c.date_prochaine_visite and c.date_prochaine_visite <= date.today() + timedelta(days=7)]

    patients_recents = Patient.query.order_by(Patient.created_at.desc()).limit(5).all()

    statuts_labels = ['En cours', 'Guéri', 'Perdu de vue', 'Échec', 'Décédé', 'Terminé']
    statuts_data = [
        len(actifs), len(gueris), len(perdus), len(echecs),
        len([p for p in patients if p.statut == 'decede']),
        len([p for p in patients if p.statut == 'termine']),
    ]

    today = date.today()
    mois_labels = []
    mois_data = []
    for i in range(5, -1, -1):
        mois_date = date(today.year, today.month, 1) - timedelta(days=30 * i)
        mois_suivant_month = mois_date.month % 12 + 1
        mois_suivant_year = mois_date.year + (1 if mois_date.month == 12 else 0)
        mois_fin = date(mois_suivant_year, mois_suivant_month, 1)
        label = mois_date.strftime('%b %Y')
        count = Patient.query.filter(
            Patient.date_debut_traitement >= mois_date,
            Patient.date_debut_traitement < mois_fin,
        ).count()
        mois_labels.append(label)
        mois_data.append(count)

    # ── Données cohorte trimestrielle ──────────────────────────────────────────
    cohorte_labels = ['Guéri', 'Échec', 'Perdu de vue', 'Décédé', 'Non évalué']
    cohorte_data = [
        len(gueris),
        len(echecs),
        len(perdus),
        len([p for p in patients if p.statut == 'decede']),
        len([p for p in patients if p.statut in ('non_evalue', 'transfert')]),
    ]

    # ── Conversions bactériologiques par mois (M1–M6) ─────────────────────────
    conversions_labels = [f'M{m}' for m in range(0, 7)]
    conversions_data = []
    for m in range(0, 7):
        nb = ExamenLabo.query.filter_by(
            mois_suivi=m,
            culture_resultat='negatif',
        ).count()
        conversions_data.append(nb)

    # ── Adhérence globale DOT ──────────────────────────────────────────────────
    date_30j = date.today() - timedelta(days=30)
    dots_recents = SuiviDOT.query.filter(SuiviDOT.date_observation >= date_30j).all()
    if dots_recents:
        nb_prises = sum(1 for d in dots_recents if d.prise_confirmee)
        adherence_globale = round(nb_prises / len(dots_recents) * 100, 1)
    else:
        adherence_globale = None

    # ── Patients actifs sans examen labo depuis > 30 jours ────────────────────
    patients_sans_examen = []
    for p in actifs:
        if not p.examens_labo:
            patients_sans_examen.append(p)
        else:
            dernier_examen = max(p.examens_labo, key=lambda e: e.date_prelevement)
            if (date.today() - dernier_examen.date_prelevement).days > 30:
                patients_sans_examen.append(p)

    return render_template('dashboard/index.html',
        total_patients=len(patients),
        nb_actifs=len(actifs),
        nb_alertes=len(alertes),
        nb_stocks_bas=len(stocks_bas),
        nb_contacts_urgents=len(contacts_urgents),
        effets_recents=effets_recents,
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
    )
