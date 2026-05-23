import csv
import io
from calendar import monthrange
from datetime import date, timedelta
from flask import Blueprint, render_template, Response, request
from flask_login import login_required
from ...models import Patient, EffetSecondaire, Contact, Medicament, MouvementStock
from ...utils.decorators import role_required

rapports_bp = Blueprint('rapports', __name__, url_prefix='/rapports')


# ── Helpers ───────────────────────────────────────────────────────────────────

def _trimestre_range(year, q):
    month_start = (q - 1) * 3 + 1
    month_end   = q * 3
    return date(year, month_start, 1), date(year, month_end, monthrange(year, month_end)[1])


def _current_q():
    return ((date.today().month - 1) // 3) + 1


def _build_stats():
    patients = Patient.query.all()
    total = len(patients)
    gueris      = sum(1 for p in patients if p.statut == 'gueri')
    termines    = sum(1 for p in patients if p.statut == 'termine')
    perdus      = sum(1 for p in patients if p.statut == 'perdu_de_vue')
    echecs      = sum(1 for p in patients if p.statut == 'echec')
    decedes     = sum(1 for p in patients if p.statut == 'decede')
    actifs      = sum(1 for p in patients if p.statut == 'en_cours')
    transferts  = sum(1 for p in patients if p.statut == 'transfert')
    non_evalues = sum(1 for p in patients if p.statut == 'non_evalue')

    succes      = gueris + termines
    taux_succes = round(succes / total * 100) if total else 0

    contacts_tb_mr = sum(1 for c in Contact.query.all() if c.statut == 'tb_mr_confirmee')
    effets_severe  = sum(1 for e in EffetSecondaire.query.all() if e.severite == 'severe')

    trimestre = f'T{_current_q()} {date.today().year}'
    return dict(
        total=total, actifs=actifs, gueris=gueris, termines=termines,
        perdus=perdus, echecs=echecs, decedes=decedes,
        transferts=transferts, non_evalues=non_evalues,
        succes=succes, taux_succes=taux_succes,
        contacts_tb_mr=contacts_tb_mr, effets_severe=effets_severe,
        trimestre=trimestre,
    )


def _build_depistage(year, q):
    debut, fin = _trimestre_range(year, q)
    contacts = Contact.query.filter(
        Contact.date_premier_contact >= debut,
        Contact.date_premier_contact <= fin,
    ).all()

    total       = len(contacts)
    depistes    = sum(1 for c in contacts if c.date_depistage is not None)
    non_depiste = total - depistes

    gx_pos  = sum(1 for c in contacts if c.resultat_genexpert == 'positif')
    gx_neg  = sum(1 for c in contacts if c.resultat_genexpert == 'negatif')
    gx_inv  = sum(1 for c in contacts if c.resultat_genexpert == 'invalide')
    gx_nf   = sum(1 for c in contacts if c.resultat_genexpert == 'non_fait')

    radio_anorm = sum(1 for c in contacts if c.radiographie_thorax == 'anormale')
    radio_norm  = sum(1 for c in contacts if c.radiographie_thorax == 'normale')
    radio_nf    = sum(1 for c in contacts if c.radiographie_thorax == 'non_faite')

    tb_confirmes = sum(1 for c in contacts if c.statut == 'tb_mr_confirmee')
    ipt_propose  = sum(1 for c in contacts if c.ipt_propose)
    ipt_accepte  = sum(1 for c in contacts if c.ipt_accepte)

    par_relation = {}
    for rel in ('foyer', 'famille', 'travail', 'autre'):
        par_relation[rel] = sum(1 for c in contacts if (c.relation or 'autre') == rel)

    hommes = sum(1 for c in contacts if c.sexe == 'Homme')
    femmes = sum(1 for c in contacts if c.sexe == 'Femme')

    taux_depistage = round(depistes / total * 100) if total else 0
    taux_positif   = round(gx_pos  / depistes * 100) if depistes else 0
    taux_ipt       = round(ipt_accepte / ipt_propose * 100) if ipt_propose else 0

    return dict(
        year=year, q=q, debut=debut, fin=fin,
        total=total, depistes=depistes, non_depiste=non_depiste,
        gx_pos=gx_pos, gx_neg=gx_neg, gx_inv=gx_inv, gx_nf=gx_nf,
        radio_anorm=radio_anorm, radio_norm=radio_norm, radio_nf=radio_nf,
        tb_confirmes=tb_confirmes, ipt_propose=ipt_propose, ipt_accepte=ipt_accepte,
        par_relation=par_relation, hommes=hommes, femmes=femmes,
        taux_depistage=taux_depistage, taux_positif=taux_positif, taux_ipt=taux_ipt,
    )


def _build_commande():
    today        = date.today()
    debut_90j    = today - timedelta(days=90)
    trimestre    = f'T{_current_q()} {today.year}'

    medicaments = Medicament.query.order_by(Medicament.nom).all()

    # Nombre de patients actifs par médicament (via traitements actifs)
    actifs = Patient.query.filter_by(statut='en_cours').all()
    patients_par_med = {}
    for p in actifs:
        for t in p.traitements:
            if t.statut_traitement == 'actif':
                for nom in t.medicaments:
                    patients_par_med[nom] = patients_par_med.get(nom, 0) + 1

    # Consommation réelle (sorties stock 90 derniers jours)
    sorties = MouvementStock.query.filter(
        MouvementStock.type_mouvement == 'sortie',
        MouvementStock.date_mouvement >= debut_90j,
    ).all()
    conso_par_id = {}
    for s in sorties:
        conso_par_id[s.medicament_id] = conso_par_id.get(s.medicament_id, 0) + s.quantite

    lignes = []
    for m in medicaments:
        conso_90j        = conso_par_id.get(m.id, 0)
        conso_jour       = conso_90j / 90
        besoin_trimestre = round(conso_jour * 90)
        stock_actuel     = m.quantite_stock
        ecart            = besoin_trimestre - stock_actuel
        a_commander      = max(0, ecart)

        if stock_actuel == 0:
            urgence = 'danger'
        elif ecart > 0:
            urgence = 'warning'
        else:
            urgence = 'success'

        lignes.append(dict(
            medicament=m,
            conso_90j=conso_90j,
            besoin_trimestre=besoin_trimestre,
            stock_actuel=stock_actuel,
            ecart=ecart,
            a_commander=a_commander,
            urgence=urgence,
            nb_patients=patients_par_med.get(m.nom, 0),
        ))

    # Trier : ruptures → stock faible → OK
    ORDRE = {'danger': 0, 'warning': 1, 'success': 2}
    lignes.sort(key=lambda x: ORDRE[x['urgence']])

    nb_actifs        = len(actifs)
    total_a_commander = sum(l['a_commander'] for l in lignes)
    nb_ruptures      = sum(1 for l in lignes if l['urgence'] == 'danger')
    nb_faibles       = sum(1 for l in lignes if l['urgence'] == 'warning')

    return dict(
        lignes=lignes, nb_actifs=nb_actifs, trimestre=trimestre,
        total_a_commander=total_a_commander, nb_ruptures=nb_ruptures,
        nb_faibles=nb_faibles, debut_90j=debut_90j, today=today,
    )


def _build_annuel(year):
    debut = date(year, 1, 1)
    fin   = date(year, 12, 31)

    # Patients diagnostiqués dans l'année (ou tous si aucun diagnostic daté)
    par_date = Patient.query.filter(
        Patient.date_diagnostic >= debut,
        Patient.date_diagnostic <= fin,
    ).all()
    patients = par_date if par_date else Patient.query.all()
    total    = len(patients)

    # Résultats de traitement
    par_statut = {
        'gueri':        sum(1 for p in patients if p.statut == 'gueri'),
        'termine':      sum(1 for p in patients if p.statut == 'termine'),
        'perdu_de_vue': sum(1 for p in patients if p.statut == 'perdu_de_vue'),
        'echec':        sum(1 for p in patients if p.statut == 'echec'),
        'decede':       sum(1 for p in patients if p.statut == 'decede'),
        'transfert':    sum(1 for p in patients if p.statut == 'transfert'),
        'non_evalue':   sum(1 for p in patients if p.statut == 'non_evalue'),
        'en_cours':     sum(1 for p in patients if p.statut == 'en_cours'),
    }

    succes      = par_statut['gueri'] + par_statut['termine']
    defavorables = par_statut['perdu_de_vue'] + par_statut['echec'] + par_statut['decede']
    taux_succes = round(succes / total * 100) if total else 0

    # Par type de résistance
    resistances = ['RR-TB', 'TB-MR', 'pre-XDR', 'XDR']
    par_resistance = {r: sum(1 for p in patients if p.type_resistance == r) for r in resistances}
    par_resistance['Autre / Non précisé'] = total - sum(par_resistance.values())

    # Par catégorie — toutes les catégories PNLT (guide p.40-41)
    categories = {
        'nouveau_cas':    'N — Nouveau cas',
        'echec_primo':    'E1 — Échec primotraitement',
        'echec_retrait':  'E2 — Échec retraitement',
        'reprise':        'RT — Reprise après PDV',
        'rechute_primo':  'R1 — Rechute primo',
        'rechute_retrait':'R2 — Rechute retraitement',
        'transfert':      'TE — Transféré entrant',
        'echec_tbmr':     'E4 — Échec TB-MR',
        'reprise_tbmr':   'RT4 — Reprise PDV TB-MR',
        'rechute_tbmr':   'R4 — Rechute TB-MR',
        'autres':         'A — Autres',
    }
    par_categorie = {label: sum(1 for p in patients if p.categorie == k)
                     for k, label in categories.items()}

    # VIH
    vih_pos  = sum(1 for p in patients if p.statut_vih == 'positif')
    vih_neg  = sum(1 for p in patients if p.statut_vih == 'negatif')
    vih_inc  = sum(1 for p in patients if p.statut_vih == 'inconnu')
    taux_vih = round(vih_pos / total * 100) if total else 0

    # Sexe
    hommes = sum(1 for p in patients if p.sexe == 'Homme')
    femmes = sum(1 for p in patients if p.sexe == 'Femme')

    # Enrôlement mensuel (basé sur date_diagnostic de l'année sélectionnée)
    par_mois = [0] * 12
    for p in patients:
        if p.date_diagnostic and p.date_diagnostic.year == year:
            par_mois[p.date_diagnostic.month - 1] += 1

    # Effets sévères dans l'année
    effets_severes = EffetSecondaire.query.filter(
        EffetSecondaire.date_declaration >= debut,
        EffetSecondaire.date_declaration <= fin,
        EffetSecondaire.severite == 'severe',
    ).count()

    annees = list(range(2020, date.today().year + 1))

    return dict(
        year=year, annees=annees, debut=debut, fin=fin,
        total=total, par_statut=par_statut,
        succes=succes, defavorables=defavorables, taux_succes=taux_succes,
        par_resistance=par_resistance, par_categorie=par_categorie,
        vih_pos=vih_pos, vih_neg=vih_neg, vih_inc=vih_inc, taux_vih=taux_vih,
        hommes=hommes, femmes=femmes,
        par_mois=par_mois, effets_severes=effets_severes,
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@rapports_bp.route('/')
@login_required
@role_required('coordinateur', 'medecin')
def index():
    return render_template('rapports/index.html', **_build_stats())


@rapports_bp.route('/export.csv')
@login_required
@role_required('coordinateur', 'medecin')
def export_csv():
    stats = _build_stats()
    output = io.StringIO()
    output.write('﻿')
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Rapport PNLT', stats['trimestre'], '', ''])
    writer.writerow(['Résultat', 'Définition', 'Nombre', 'Pourcentage'])
    rows = [
        ('Guéri',                'Cultures négatives + traitement terminé',           stats['gueris']),
        ('Traitement terminé',   'Traitement terminé sans preuve bactério finale',     stats['termines']),
        ('Perdu de vue',         'Interruption ≥ 2 mois consécutifs',                 stats['perdus']),
        ('Échec thérapeutique',  'Culture positive ≥ M6 ou changement de schéma',     stats['echecs']),
        ('Décédé',               'Décès avant ou pendant le traitement',               stats['decedes']),
        ('Transféré',            'Transféré vers un autre centre',                     stats['transferts']),
        ('Non évalué',           'Résultat de traitement non documenté',               stats['non_evalues']),
        ('En cours',             'Traitement actif',                                   stats['actifs']),
    ]
    total = stats['total']
    for label, defn, val in rows:
        pct = f"{round(val / total * 100, 1)}%" if total else "0%"
        writer.writerow([label, defn, val, pct])
    writer.writerow(['Total cohorte', '', total, '100%'])
    writer.writerow([])
    writer.writerow(['Indicateurs PMDT', '', '', ''])
    writer.writerow(['Taux de succès thérapeutique', '', f"{stats['taux_succes']}%", ''])
    writer.writerow(['Contacts TB-MR confirmés',     '', stats['contacts_tb_mr'], ''])
    writer.writerow(['Effets sévères déclarés',       '', stats['effets_severe'], ''])
    filename = f"rapport_pnlt_{stats['trimestre'].replace(' ', '_')}.csv"
    return Response(output.getvalue(), mimetype='text/csv; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename="{filename}"'})


# ── Rapport trimestriel dépistage ────────────────────────────────────────────

@rapports_bp.route('/depistage')
@login_required
@role_required('coordinateur', 'medecin')
def depistage():
    today = date.today()
    year = request.args.get('annee', today.year, type=int)
    q    = request.args.get('trimestre', _current_q(), type=int)
    q    = max(1, min(4, q))
    data = _build_depistage(year, q)
    annees = list(range(2020, today.year + 1))
    return render_template('rapports/depistage.html', annees=annees, **data)


@rapports_bp.route('/depistage/export.csv')
@login_required
@role_required('coordinateur', 'medecin')
def depistage_csv():
    today = date.today()
    year = request.args.get('annee', today.year, type=int)
    q    = request.args.get('trimestre', _current_q(), type=int)
    d    = _build_depistage(year, q)
    label = f'T{q} {year}'

    output = io.StringIO()
    output.write('﻿')
    w = csv.writer(output, delimiter=';')
    w.writerow([f'Rapport Trimestriel Dépistage TB-MR — {label}', '', ''])
    w.writerow(['Indicateur', 'Valeur', 'Taux'])
    w.writerow(['Total contacts enregistrés', d['total'], ''])
    w.writerow(['Contacts dépistés', d['depistes'], f"{d['taux_depistage']}%"])
    w.writerow(['Non dépistés', d['non_depiste'], ''])
    w.writerow([])
    w.writerow(['GeneXpert', 'Nombre', ''])
    w.writerow(['Positif', d['gx_pos'], f"{d['taux_positif']}% des dépistés"])
    w.writerow(['Négatif', d['gx_neg'], ''])
    w.writerow(['Invalide', d['gx_inv'], ''])
    w.writerow(['Non fait', d['gx_nf'], ''])
    w.writerow([])
    w.writerow(['Radiographie thorax', 'Nombre', ''])
    w.writerow(['Anormale', d['radio_anorm'], ''])
    w.writerow(['Normale', d['radio_norm'], ''])
    w.writerow(['Non faite', d['radio_nf'], ''])
    w.writerow([])
    w.writerow(['TB-MR confirmés', d['tb_confirmes'], ''])
    w.writerow(['IPT proposé', d['ipt_propose'], ''])
    w.writerow(['IPT accepté', d['ipt_accepte'], f"{d['taux_ipt']}%"])
    w.writerow([])
    w.writerow(['Par lien de contact', 'Nombre', ''])
    for rel, nb in d['par_relation'].items():
        w.writerow([rel.capitalize(), nb, ''])
    w.writerow(['Hommes', d['hommes'], ''])
    w.writerow(['Femmes', d['femmes'], ''])

    return Response(output.getvalue(), mimetype='text/csv; charset=utf-8',
                    headers={'Content-Disposition':
                             f'attachment; filename="depistage_{label.replace(" ","_")}.csv"'})


# ── Commande trimestrielle médicaments ────────────────────────────────────────

@rapports_bp.route('/commande')
@login_required
@role_required('coordinateur', 'medecin')
def commande():
    data = _build_commande()
    return render_template('rapports/commande.html', **data)


@rapports_bp.route('/commande/export.csv')
@login_required
@role_required('coordinateur', 'medecin')
def commande_csv():
    d = _build_commande()
    output = io.StringIO()
    output.write('﻿')
    w = csv.writer(output, delimiter=';')
    w.writerow([f'Commande Trimestrielle Médicaments — {d["trimestre"]}', '', '', '', '', ''])
    w.writerow(['Médicament', 'Dosage', 'Stock actuel', 'Consommation 90j',
                'Besoin T+1', 'À commander', 'Urgence'])
    for l in d['lignes']:
        m = l['medicament']
        urg = {'danger': 'RUPTURE', 'warning': 'INSUFFISANT', 'success': 'OK'}.get(l['urgence'], '')
        w.writerow([m.nom, m.dosage_unitaire or '', l['stock_actuel'], l['conso_90j'],
                    l['besoin_trimestre'], l['a_commander'], urg])
    w.writerow([])
    w.writerow(['Total unités à commander', '', '', '', '', d['total_a_commander'], ''])

    fname = 'commande_' + d['trimestre'].replace(' ', '_') + '.csv'
    return Response(output.getvalue(), mimetype='text/csv; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename="{fname}"'})


# ── Rapport annuel résultats TB-MR ────────────────────────────────────────────

@rapports_bp.route('/annuel')
@login_required
@role_required('coordinateur', 'medecin')
def annuel():
    year = request.args.get('annee', date.today().year, type=int)
    data = _build_annuel(year)
    return render_template('rapports/annuel.html', **data)


@rapports_bp.route('/annuel/export.csv')
@login_required
@role_required('coordinateur', 'medecin')
def annuel_csv():
    year = request.args.get('annee', date.today().year, type=int)
    d    = _build_annuel(year)
    output = io.StringIO()
    output.write('﻿')
    w = csv.writer(output, delimiter=';')
    w.writerow([f'Rapport Annuel TB-MR — {year}', '', ''])
    w.writerow(['Résultat', 'Nombre', 'Pourcentage'])
    labels = {
        'gueri': 'Guéri', 'termine': 'Traitement terminé',
        'perdu_de_vue': 'Perdu de vue', 'echec': 'Échec',
        'decede': 'Décédé', 'transfert': 'Transféré',
        'non_evalue': 'Non évalué', 'en_cours': 'En cours',
    }
    for k, lbl in labels.items():
        val = d['par_statut'].get(k, 0)
        pct = f"{round(val/d['total']*100,1)}%" if d['total'] else '0%'
        w.writerow([lbl, val, pct])
    w.writerow(['Total', d['total'], '100%'])
    w.writerow([])
    w.writerow(['Taux de succès', f"{d['taux_succes']}%", ''])
    w.writerow(['Co-infection VIH', d['vih_pos'], f"{d['taux_vih']}%"])
    w.writerow(['Effets sévères', d['effets_severes'], ''])
    w.writerow([])
    w.writerow(['Par type de résistance', 'Nombre', ''])
    for r, nb in d['par_resistance'].items():
        w.writerow([r, nb, ''])
    w.writerow([])
    w.writerow(['Enrôlement mensuel', 'Nombre', ''])
    mois_noms = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun',
                 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
    for i, nb in enumerate(d['par_mois']):
        w.writerow([mois_noms[i], nb, ''])

    return Response(output.getvalue(), mimetype='text/csv; charset=utf-8',
                    headers={'Content-Disposition':
                             f'attachment; filename="annuel_tbmr_{year}.csv"'})
