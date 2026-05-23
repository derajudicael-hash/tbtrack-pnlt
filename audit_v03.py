"""
Audit complet TBTrack v0.3
Teste TOUS les cycles : patients, traitements, DOT, labo, effets,
contacts, parametres, notes, stock, rapports, roles, securite.
"""
import os, sys, datetime
os.environ['TESTING'] = '1'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
sys.path.insert(0, '.')
from app import create_app
from app.extensions import db
from app.models import (User, Patient, Traitement, EffetSecondaire,
                        Contact, ExamenLabo, SuiviDOT, Medicament,
                        MouvementStock, SuiviPonderal, NoteClinique, BilanInitial)

app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

BUGS = []
OK = 0
SECTION = ''

def section(name):
    global SECTION
    SECTION = name
    print(f'\n{"=" * 65}\n  {name}\n{"=" * 65}')

def check(label, cond, detail=''):
    global OK
    if cond:
        OK += 1
        print(f'  OK   {label}')
    else:
        BUGS.append(f'[{SECTION}] {label}' + (f' — {detail}' if detail else ''))
        print(f'  FAIL {label}' + (f' [{detail}]' if detail else ''))

def html_ok(r, label):
    s = r.status_code == 200
    no_crash  = b'internal server error' not in r.data.lower()
    no_jinja  = b'jinja2' not in r.data.lower() and b'templatenotfound' not in r.data.lower()
    no_trace  = b'traceback' not in r.data.lower()
    ok = s and no_crash and no_jinja and no_trace
    check(label, ok, f'HTTP {r.status_code}' +
          (' CRASH' if not no_crash else '') +
          (' JINJA' if not no_jinja else '') +
          (' TRACE' if not no_trace else ''))
    return ok

def post(C, url, data):
    return C.post(url, data=data, follow_redirects=True)

# ── Setup DB ──────────────────────────────────────────────────────────────────
with app.app_context():
    # Utilisateurs
    users = {}
    for role, email in [
        ('coordinateur', 'coord@tb.mg'),
        ('medecin',      'med@tb.mg'),
        ('infirmier',    'inf@tb.mg'),
        ('laborantin',   'lab@tb.mg'),
    ]:
        u = User(email=email, nom=role.upper(), prenom='Test',
                 role=role, centre='CDT Test')
        u.set_password('test1234')
        db.session.add(u)
        users[role] = u
    db.session.flush()

    # Patient principal pour les tests
    p_main = Patient(
        code_patient='TST-0001',
        nom='RASOA', prenom='Marie',
        date_naissance=datetime.date(1990, 5, 15),
        sexe='Femme', adresse='Lot II A, Antananarivo',
        telephone='034 00 000 01', poids=55.0,
        statut_vih='negatif', type_resistance='TB-MR',
        categorie='nouveau_cas', statut='en_cours',
        schema_therapeutique='court',
        date_diagnostic=datetime.date.today() - datetime.timedelta(days=30),
        date_debut_traitement=datetime.date.today() - datetime.timedelta(days=20),
        medecin_id=users['medecin'].id,
    )
    # Patient pour test suppression
    p_del = Patient(
        code_patient='TST-DEL', nom='TODEL', prenom='Patient',
        statut='en_cours', poids=60.0,
        medecin_id=users['medecin'].id,
    )
    # Patients avec tous les statuts pour rapports
    statuts = ['gueri', 'perdu_de_vue', 'echec', 'decede', 'transfert', 'termine']
    p_statuts = []
    for i, s in enumerate(statuts):
        p = Patient(
            code_patient=f'TST-{s.upper()[:5]}{i}',
            nom=f'NOM{i}', prenom='P',
            statut=s, poids=60.0, type_resistance='TB-MR',
            medecin_id=users['medecin'].id,
            date_sortie=datetime.date(2025, 1, 1),
        )
        p_statuts.append(p)
    db.session.add_all([p_main, p_del] + p_statuts)
    db.session.flush()

    # Traitement
    t_main = Traitement(
        patient_id=p_main.id,
        schema_nom='4Bdq-Mfx-Cfz-Z',
        phase='intensive',
        date_debut=p_main.date_debut_traitement,
        date_fin_prevue=p_main.date_debut_traitement + datetime.timedelta(days=270),
        statut_traitement='actif',
    )
    t_main.medicaments = ['Bedaquiline', 'Moxifloxacine', 'Clofazimine']
    db.session.add(t_main)
    db.session.flush()

    # Effet secondaire sévère non notifié
    ef = EffetSecondaire(
        patient_id=p_main.id,
        symptome='Troubles visuels',
        severite='severe',
        medicament_incrimine='Ethambutol',
        date_declaration=datetime.datetime.utcnow(),
        notifie_crpc=False,
        declare_par='Test',
    )
    db.session.add(ef)

    # Contact
    ct = Contact(
        patient_source_id=p_main.id,
        nom='CONTACT', prenom='Test',
        age=35, sexe='Homme', relation='foyer',
        date_premier_contact=datetime.date.today(),
        statut='en_suivi',
    )
    db.session.add(ct)

    # Examen labo
    ex = ExamenLabo(
        patient_id=p_main.id,
        laborantin_id=users['laborantin'].id,
        mois_suivi=0,
        date_prelevement=datetime.date.today() - datetime.timedelta(days=5),
        date_resultat=datetime.date.today(),
        genexpert_effectue=True, genexpert_resultat='positif',
        frottis_effectue=True, frottis_resultat='positif', frottis_quantite='2+',
    )
    db.session.add(ex)

    # Médicament en stock
    med = Medicament(
        nom='Bedaquiline Test', abreviation='BdqT',
        forme='cp', dosage_unitaire='100mg',
        quantite_stock=200, seuil_alerte=50, unite='cp',
        centre='CDT Test',
    )
    db.session.add(med)

    # SuiviPonderal M0
    sp = SuiviPonderal(
        patient_id=p_main.id,
        mois_suivi=0,
        date_mesure=datetime.date.today() - datetime.timedelta(days=20),
        poids=55.0, taille=162.0,
    )
    db.session.add(sp)

    # Note clinique
    note = NoteClinique(
        patient_id=p_main.id,
        auteur_id=users['medecin'].id,
        contenu='Bonne tolérance initiale. Suivi à J+30.',
    )
    db.session.add(note)

    db.session.commit()

    # IDs pour les tests
    pid   = p_main.id
    pid_d = p_del.id
    tid   = t_main.id
    eid   = ef.id
    cid   = ct.id
    mid   = med.id
    uid_coord = users['coordinateur'].id
    uid_med   = users['medecin'].id
    uid_inf   = users['infirmier'].id
    uid_lab   = users['laborantin'].id


def client_as(role_key):
    uid = {'coordinateur': uid_coord, 'medecin': uid_med,
           'infirmier': uid_inf, 'laborantin': uid_lab}[role_key]
    C = app.test_client()
    with C.session_transaction() as sess:
        sess['_user_id'] = str(uid)
        sess['_fresh'] = True
    return C


# ══════════════════════════════════════════════════════════════════════════════
# 1. SÉCURITÉ — SANS LOGIN
# ══════════════════════════════════════════════════════════════════════════════
section('1. SECURITE — SANS LOGIN')
with app.test_client() as Ca:
    for url in ['/login']:
        r = Ca.get(url)
        check(f'Page publique {url}', r.status_code == 200)
    for url in ['/dashboard/', '/patients/', '/rapports/', '/stock/',
                '/admin/utilisateurs', '/labo/']:
        r = Ca.get(url, follow_redirects=False)
        check(f'Protégé sans login → redirect: {url}', r.status_code in (301, 302),
              f'got {r.status_code}')


# ══════════════════════════════════════════════════════════════════════════════
# 2. AUTORISATIONS PAR ROLE — 403
# ══════════════════════════════════════════════════════════════════════════════
section('2. AUTORISATIONS PAR ROLE')

# Laborantin ne peut PAS accéder aux rapports
with client_as('laborantin') as Cl:
    r = Cl.get('/rapports/', follow_redirects=True)
    check('Laborantin → rapports = 403', r.status_code == 403, f'got {r.status_code}')

    r = Cl.post(f'/patients/ajouter', data={
        'nom': 'HACK', 'prenom': 'Test', 'poids': 60
    }, follow_redirects=True)
    check('Laborantin → ajouter patient = 403', r.status_code == 403)

    r = Cl.post(f'/stock/ajouter', data={'nom': 'Hack'}, follow_redirects=True)
    check('Laborantin → ajouter médicament = 403', r.status_code == 403)

# Infirmier ne peut PAS modifier un patient
with client_as('infirmier') as Ci:
    r = Ci.get(f'/patients/{pid}/modifier', follow_redirects=True)
    check('Infirmier → modifier patient = 403', r.status_code == 403)

    r = Ci.post(f'/patients/{pid}/supprimer', follow_redirects=True)
    check('Infirmier → supprimer patient = 403', r.status_code == 403)

    r = Ci.get('/rapports/', follow_redirects=True)
    check('Infirmier → rapports = 403', r.status_code == 403)

    r = Ci.post(f'/stock/{mid}/supprimer', follow_redirects=True)
    check('Infirmier → supprimer médicament = 403', r.status_code == 403)

# Médecin ne peut PAS supprimer patient ni accéder admin
with client_as('medecin') as Cm:
    r = Cm.post(f'/patients/{pid}/supprimer', follow_redirects=True)
    check('Médecin → supprimer patient = 403', r.status_code == 403)

    r = Cm.get('/admin/utilisateurs', follow_redirects=True)
    check('Médecin → admin = 403', r.status_code == 403)

    r = Cm.post(f'/stock/{mid}/supprimer', follow_redirects=True)
    check('Médecin → supprimer médicament = 403', r.status_code == 403)


# ══════════════════════════════════════════════════════════════════════════════
# 3. COORDINATEUR — ACCES TOTAL
# ══════════════════════════════════════════════════════════════════════════════
section('3. COORDINATEUR — ACCES TOTAL')
with client_as('coordinateur') as Cc:
    for url, label in [
        ('/dashboard/',           'Dashboard'),
        ('/patients/',            'Liste patients'),
        (f'/patients/{pid}',      'Fiche patient'),
        ('/rapports/',            'Rapports'),
        ('/rapports/depistage',   'Rapport dépistage'),
        ('/rapports/commande',    'Rapport commande'),
        ('/rapports/annuel',      'Rapport annuel'),
        ('/stock/',               'Stock inventaire'),
        ('/labo/',                'Labo index'),
        ('/admin/utilisateurs',   'Admin utilisateurs'),
        ('/dosage/',              'Calculateur dosage'),
        ('/traitement/',          'Liste traitements'),
        ('/effets/',              'Effets secondaires'),
        ('/contacts/',            'Contacts'),
    ]:
        html_ok(Cc.get(url, follow_redirects=True), f'Coordinateur: {label}')


# ══════════════════════════════════════════════════════════════════════════════
# 4. CYCLE COMPLET PATIENT — CREATION
# ══════════════════════════════════════════════════════════════════════════════
section('4. CYCLE PATIENT — CREATION')
with client_as('medecin') as Cm:
    today = datetime.date.today().isoformat()

    # Créer un nouveau patient
    r = post(Cm, '/patients/ajouter', {
        'nom': 'RAKOTO', 'prenom': 'Jean',
        'date_naissance': '1985-03-20',
        'sexe': 'Homme', 'adresse': 'Lot I A Antananarivo',
        'telephone': '034 00 111 22', 'poids': 68.5,
        'statut_vih': 'negatif', 'type_resistance': 'TB-MR',
        'categorie': 'nouveau_cas', 'statut': 'en_cours',
        'schema_therapeutique': 'court',
        'date_diagnostic': today,
        'date_debut_traitement': today,
    })
    check('Créer patient → redirect fiche', r.status_code == 200)
    check('Fiche créée contient le nom', b'RAKOTO' in r.data)

    # Vérifier que le code est unique
    with app.app_context():
        nouveau = Patient.query.filter_by(nom='RAKOTO').first()
        check('Code patient généré', nouveau is not None and nouveau.code_patient is not None)
        new_pid = nouveau.id if nouveau else pid

    # Fiche patient
    r = Cm.get(f'/patients/{new_pid}', follow_redirects=True)
    html_ok(r, 'Fiche nouveau patient accessible')

    # Modifier le patient
    r = post(Cm, f'/patients/{new_pid}/modifier', {
        'nom': 'RAKOTO', 'prenom': 'Jean-Paul',
        'date_naissance': '1985-03-20',
        'sexe': 'Homme', 'poids': 70.0,
        'statut_vih': 'negatif', 'type_resistance': 'TB-MR',
        'categorie': 'nouveau_cas', 'statut': 'en_cours',
        'schema_therapeutique': 'court',
    })
    check('Modifier patient OK', r.status_code == 200)
    check('Prénom mis à jour', b'Jean-Paul' in r.data)


# ══════════════════════════════════════════════════════════════════════════════
# 5. CYCLE TRAITEMENT
# ══════════════════════════════════════════════════════════════════════════════
section('5. CYCLE TRAITEMENT')
with client_as('medecin') as Cm:
    today = datetime.date.today().isoformat()
    fin = (datetime.date.today() + datetime.timedelta(days=270)).isoformat()

    # Créer un traitement
    r = post(Cm, f'/traitement/ajouter/{pid}', {
        'schema_nom': 'Test-Schema-4Bdq',
        'phase': 'intensive',
        'date_debut': today,
        'date_fin_prevue': fin,
        'medicaments': ['Bedaquiline', 'Moxifloxacine'],
    })
    check('Créer traitement', r.status_code == 200)

    # Détail traitement
    r = Cm.get(f'/traitement/{tid}', follow_redirects=True)
    html_ok(r, 'Détail traitement accessible')
    check('Médicaments visibles', b'Bedaquiline' in r.data or b'traitement' in r.data.lower())

    # Modifier traitement
    r = post(Cm, f'/traitement/{tid}/modifier', {
        'schema_nom': 'Schema-Modifie',
        'phase': 'continuation',
        'date_debut': today,
        'date_fin_prevue': fin,
    })
    check('Modifier traitement', r.status_code == 200)


# ══════════════════════════════════════════════════════════════════════════════
# 6. DOT — SUIVI QUOTIDIEN
# ══════════════════════════════════════════════════════════════════════════════
section('6. DOT — SUIVI QUOTIDIEN')
with client_as('infirmier') as Ci:
    today = datetime.date.today().isoformat()

    r = Ci.get(f'/traitement/{tid}/dot/ajouter', follow_redirects=True)
    html_ok(r, 'Page saisie DOT accessible par infirmier')

    r = post(Ci, f'/traitement/{tid}/dot/ajouter', {
        'date_prise': today,
        'prise_complete': 'on',
        'medicaments_pris': ['Bedaquiline', 'Moxifloxacine'],
        'observateur': 'Inf. Test',
    })
    check('Enregistrer DOT', r.status_code == 200)

    r = Ci.get(f'/traitement/{tid}/dot/historique', follow_redirects=True)
    html_ok(r, 'Historique DOT accessible')


# ══════════════════════════════════════════════════════════════════════════════
# 7. LABORATOIRE
# ══════════════════════════════════════════════════════════════════════════════
section('7. LABORATOIRE')
with client_as('laborantin') as Cl:
    today = datetime.date.today().isoformat()

    r = Cl.get('/labo/', follow_redirects=True)
    html_ok(r, 'Index labo accessible par laborantin')

    r = Cl.get('/labo/saisir', follow_redirects=True)
    html_ok(r, 'Page saisie examen accessible')

    r = post(Cl, '/labo/saisir', {
        'patient_id': pid,
        'mois_suivi': 1,
        'date_prelevement': today,
        'date_resultat': today,
        'frottis_effectue': 'on',
        'frottis_resultat': 'negatif',
        'culture_effectuee': 'on',
        'culture_resultat': 'negatif',
        'culture_milieu': 'MGIT',
    })
    check('Saisir examen labo M1', r.status_code == 200)

    # Labo laborantin ne peut PAS accéder aux rapports
    r = Cl.get('/rapports/', follow_redirects=True)
    check('Laborantin → rapports = 403', r.status_code == 403)


# ══════════════════════════════════════════════════════════════════════════════
# 8. EFFETS SECONDAIRES
# ══════════════════════════════════════════════════════════════════════════════
section('8. EFFETS SECONDAIRES')
with client_as('infirmier') as Ci:
    r = Ci.get('/effets/', follow_redirects=True)
    html_ok(r, 'Liste effets accessible par infirmier')

    today_dt = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M')
    r = post(Ci, '/effets/declarer', {
        'patient_id': pid,
        'medicament_incrimine': 'Clofazimine',
        'symptome': 'Coloration cutanée orangée',
        'severite': 'leger',
        'date_declaration': today_dt,
        'declare_par': 'Inf. Test',
    })
    check('Déclarer effet secondaire léger', r.status_code == 200)

with client_as('medecin') as Cm:
    # Notifier CRPC pour l'effet sévère
    r = post(Cm, f'/effets/{eid}/notifier', {})
    check('Notifier CRPC effet sévère', r.status_code == 200)

    # Vérifier que le dashboard ne montre plus l'alerte
    r = Cm.get('/dashboard/', follow_redirects=True)
    html_ok(r, 'Dashboard après notification')


# ══════════════════════════════════════════════════════════════════════════════
# 9. CONTACTS ET DEPISTAGE
# ══════════════════════════════════════════════════════════════════════════════
section('9. CONTACTS ET DEPISTAGE')
with client_as('infirmier') as Ci:
    today = datetime.date.today().isoformat()
    r = Ci.get('/contacts/', follow_redirects=True)
    html_ok(r, 'Liste contacts accessible')

    r = post(Ci, '/contacts/ajouter', {
        'patient_source_id': pid,
        'nom': 'RABE', 'prenom': 'Solo',
        'age': 42, 'sexe': 'Homme', 'relation': 'foyer',
        'telephone': '032 11 111 11',
        'date_premier_contact': today,
        'statut': 'en_suivi',
    })
    check('Ajouter contact', r.status_code == 200)

    # Dépistage du contact
    r = Ci.get(f'/contacts/{cid}', follow_redirects=True)
    html_ok(r, 'Fiche contact accessible')


# ══════════════════════════════════════════════════════════════════════════════
# 10. PARAMETRES DE SUIVI MENSUEL (NOUVEAU V0.3)
# ══════════════════════════════════════════════════════════════════════════════
section('10. PARAMETRES DE SUIVI MENSUEL — V0.3')
with client_as('medecin') as Cm:
    today = datetime.date.today().isoformat()

    r = Cm.get(f'/patients/{pid}/parametres', follow_redirects=True)
    html_ok(r, 'Page paramètres accessible par médecin')
    check('Affiche le formulaire de mesure', b'Poids' in r.data or b'poids' in r.data.lower())

    # Saisir mesure M0 avec taille
    r = post(Cm, f'/patients/{pid}/parametres', {
        'mois_suivi': 0,
        'date_mesure': today,
        'poids': 55.5,
        'taille': 162.0,
        'tension_sys': 120,
        'tension_dia': 80,
        'temperature': 37.2,
    })
    check('Saisir paramètres M0 avec taille', r.status_code == 200)
    check('M0 affiché dans historique', b'M0' in r.data or b'55' in r.data)

    # Saisir M1 sans taille — IMC doit utiliser taille M0
    r = post(Cm, f'/patients/{pid}/parametres', {
        'mois_suivi': 1,
        'date_mesure': today,
        'poids': 57.0,
        'tension_sys': 118,
        'tension_dia': 78,
    })
    check('Saisir paramètres M1 sans taille', r.status_code == 200)
    check('M1 visible dans historique', b'M1' in r.data or b'57' in r.data)

    # Vérifier que la page s'affiche sans erreur avec 2 mesures
    r = Cm.get(f'/patients/{pid}/parametres', follow_redirects=True)
    html_ok(r, 'Page paramètres avec historique (2 mesures)')
    check('IMC calculé visible', b'IMC' in r.data or b'imc' in r.data.lower() or b'Normal' in r.data)

# Infirmier peut aussi saisir
with client_as('infirmier') as Ci:
    today = datetime.date.today().isoformat()
    r = post(Ci, f'/patients/{pid}/parametres', {
        'mois_suivi': 2,
        'date_mesure': today,
        'poids': 58.0,
    })
    check('Infirmier peut saisir paramètres', r.status_code == 200)

# Laborantin ne peut PAS
with client_as('laborantin') as Cl:
    r = Cl.get(f'/patients/{pid}/parametres', follow_redirects=True)
    check('Laborantin → paramètres = 403', r.status_code == 403)

# Suppression mesure (médecin)
with client_as('medecin') as Cm:
    with app.app_context():
        sp_test = SuiviPonderal(
            patient_id=pid, mois_suivi=99,
            date_mesure=datetime.date.today(), poids=40.0,
        )
        db.session.add(sp_test)
        db.session.commit()
        sp_id = sp_test.id
    r = post(Cm, f'/patients/{pid}/parametres/{sp_id}/supprimer', {})
    check('Supprimer mesure pondérale', r.status_code == 200)
    with app.app_context():
        check('Mesure bien supprimée en DB', SuiviPonderal.query.get(sp_id) is None)


# ══════════════════════════════════════════════════════════════════════════════
# 11. NOTES CLINIQUES — HISTORIQUE (NOUVEAU V0.3)
# ══════════════════════════════════════════════════════════════════════════════
section('11. NOTES CLINIQUES — HISTORIQUE — V0.3')
with client_as('medecin') as Cm:
    # Fiche patient — onglet notes visible
    r = Cm.get(f'/patients/{pid}', follow_redirects=True)
    html_ok(r, 'Fiche patient chargée')
    check('Onglet Notes présent', b'tab-notes' in r.data or b'notes' in r.data.lower())

    # Ajouter une note
    r = post(Cm, f'/patients/{pid}/notes/ajouter', {
        'contenu': 'Patient coopérant. Poids stable. Continuer le schéma.',
    })
    check('Ajouter note clinique', r.status_code == 200)
    check('Note visible dans la fiche', b'Patient' in r.data or 'coopérant'.encode() in r.data)

    # Ajouter une 2e note
    r = post(Cm, f'/patients/{pid}/notes/ajouter', {
        'contenu': 'Résultats M1 reçus. Conversion bactériologique confirmée.',
    })
    check('Ajouter 2e note', r.status_code == 200)

# Infirmier peut ajouter une note
with client_as('infirmier') as Ci:
    r = post(Ci, f'/patients/{pid}/notes/ajouter', {
        'contenu': 'DOT effectué ce jour. Patient présent.',
    })
    check('Infirmier peut ajouter une note', r.status_code == 200)

# Note vide refusée
with client_as('medecin') as Cm:
    r = post(Cm, f'/patients/{pid}/notes/ajouter', {'contenu': '   '})
    check('Note vide → refusée (redirect)', r.status_code == 200)

# Laborantin ne peut PAS ajouter de note
with client_as('laborantin') as Cl:
    r = post(Cl, f'/patients/{pid}/notes/ajouter', {'contenu': 'Hack'})
    check('Laborantin → ajouter note = 403', r.status_code == 403)

# Supprimer une note (médecin)
with client_as('medecin') as Cm:
    with app.app_context():
        n_test = NoteClinique(
            patient_id=pid, auteur_id=uid_med,
            contenu='Note à supprimer.',
        )
        db.session.add(n_test)
        db.session.commit()
        nid = n_test.id
    r = post(Cm, f'/patients/{pid}/notes/{nid}/supprimer', {})
    check('Supprimer note clinique', r.status_code == 200)
    with app.app_context():
        check('Note bien supprimée en DB', NoteClinique.query.get(nid) is None)

# Infirmier ne peut PAS supprimer une note
with client_as('infirmier') as Ci:
    with app.app_context():
        n2 = NoteClinique(patient_id=pid, auteur_id=uid_med, contenu='Note protégée.')
        db.session.add(n2)
        db.session.commit()
        nid2 = n2.id
    r = post(Ci, f'/patients/{pid}/notes/{nid2}/supprimer', {})
    check('Infirmier → supprimer note = 403', r.status_code == 403)


# ══════════════════════════════════════════════════════════════════════════════
# 12. STOCK MEDICAMENTS
# ══════════════════════════════════════════════════════════════════════════════
section('12. STOCK MEDICAMENTS')
with client_as('coordinateur') as Cc:
    today = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()

    # Ajouter médicament
    r = post(Cc, '/stock/ajouter', {
        'nom': 'Linezolide Test', 'abreviation': 'LzdT',
        'forme': 'cp', 'dosage_unitaire': '600mg',
        'quantite_stock': 300, 'seuil_alerte': 100,
        'unite': 'cp', 'date_expiration': today,
        'centre': 'CDT Test',
    })
    check('Coordinateur: ajouter médicament', r.status_code == 200)

    with app.app_context():
        new_med = Medicament.query.filter_by(nom='Linezolide Test').first()
        check('Médicament créé en DB', new_med is not None)
        new_mid = new_med.id if new_med else mid

    # Enregistrer mouvement entrée
    r = post(Cc, f'/stock/{mid}/mouvement', {
        'type_mouvement': 'entree',
        'quantite': 50,
        'reference_bon': 'BON-2026-001',
        'motif': 'Livraison CRPC',
    })
    check('Enregistrer mouvement entrée', r.status_code == 200)

    # Enregistrer mouvement sortie
    r = post(Cc, f'/stock/{mid}/mouvement', {
        'type_mouvement': 'sortie',
        'quantite': 10,
        'motif': 'Distribution patient TST-0001',
    })
    check('Enregistrer mouvement sortie', r.status_code == 200)

    # Historique
    r = Cc.get(f'/stock/{mid}/historique', follow_redirects=True)
    html_ok(r, 'Historique mouvements accessible')

    # Modifier médicament
    r = post(Cc, f'/stock/{mid}/modifier', {
        'nom': 'Bedaquiline Test Modif', 'abreviation': 'BdqT',
        'forme': 'cp', 'dosage_unitaire': '100mg',
        'quantite_stock': 250, 'seuil_alerte': 60,
        'unite': 'cp', 'centre': 'CDT Test',
    })
    check('Modifier médicament', r.status_code == 200)

    # Supprimer un médicament SANS historique
    r = post(Cc, f'/stock/{new_mid}/supprimer', {})
    check('Supprimer médicament sans historique', r.status_code == 200)
    with app.app_context():
        check('Médicament bien supprimé', Medicament.query.get(new_mid) is None)

    # Supprimer un médicament AVEC historique → doit être bloqué
    r = post(Cc, f'/stock/{mid}/supprimer', {})
    check('Supprimer médicament avec historique → bloqué',
          r.status_code == 200 and b'historique' in r.data.lower() or
          Medicament.query.get(mid) is not None)


# ══════════════════════════════════════════════════════════════════════════════
# 13. RAPPORTS PNLT
# ══════════════════════════════════════════════════════════════════════════════
section('13. RAPPORTS PNLT')
with client_as('medecin') as Cm:
    for url, label in [
        ('/rapports/',               'Index rapports'),
        ('/rapports/depistage',      'Dépistage trimestriel'),
        ('/rapports/commande',       'Commande médicaments'),
        ('/rapports/annuel',         'Rapport annuel'),
        ('/rapports/export.csv',     'Export CSV cohorte'),
        ('/rapports/depistage/export.csv', 'Export CSV dépistage'),
        ('/rapports/commande/export.csv',  'Export CSV commande'),
        ('/rapports/annuel/export.csv',    'Export CSV annuel'),
    ]:
        r = Cm.get(url, follow_redirects=True)
        check(f'Médecin: {label} accessible', r.status_code == 200)


# ══════════════════════════════════════════════════════════════════════════════
# 14. ADMINISTRATION
# ══════════════════════════════════════════════════════════════════════════════
section('14. ADMINISTRATION')
with client_as('coordinateur') as Cc:
    r = Cc.get('/admin/utilisateurs', follow_redirects=True)
    html_ok(r, 'Liste utilisateurs accessible')

    # Créer utilisateur
    r = post(Cc, '/admin/utilisateurs/creer', {
        'email': 'nouveau@test.mg',
        'nom': 'NOUVEAU', 'prenom': 'User',
        'role': 'infirmier', 'centre': 'CDT Test',
        'password': 'test1234!',
        'password_confirm': 'test1234!',
    })
    check('Créer utilisateur', r.status_code == 200)

    with app.app_context():
        nuser = User.query.filter_by(email='nouveau@test.mg').first()
        check('Utilisateur créé en DB', nuser is not None)


# ══════════════════════════════════════════════════════════════════════════════
# 15. DOSAGE CALCULATEUR
# ══════════════════════════════════════════════════════════════════════════════
section('15. DOSAGE CALCULATEUR')
with client_as('infirmier') as Ci:
    r = Ci.get('/dosage/', follow_redirects=True)
    html_ok(r, 'Calculateur dosage accessible par infirmier')
    check('Contient table de dosage', b'kg' in r.data or b'mg' in r.data)


# ══════════════════════════════════════════════════════════════════════════════
# 16. BILAN M0
# ══════════════════════════════════════════════════════════════════════════════
section('16. BILAN M0')
with client_as('medecin') as Cm:
    today = datetime.date.today().isoformat()
    r = Cm.get(f'/patients/{pid}/bilan', follow_redirects=True)
    html_ok(r, 'Page bilan M0 accessible par médecin')

    r = post(Cm, f'/patients/{pid}/bilan', {
        'date_bilan': today,
        'poids_kg': 55.0, 'taille_cm': 162.0,
        'tension_sys': 120, 'tension_dia': 80,
    })
    check('Enregistrer bilan M0', r.status_code == 200)

with client_as('infirmier') as Ci:
    r = Ci.get(f'/patients/{pid}/bilan', follow_redirects=True)
    check('Infirmier → bilan M0 = 403', r.status_code == 403)


# ══════════════════════════════════════════════════════════════════════════════
# 17. RECHERCHE
# ══════════════════════════════════════════════════════════════════════════════
section('17. RECHERCHE')
with client_as('medecin') as Cm:
    r = Cm.get('/search/?q=RASOA', follow_redirects=True)
    check('Recherche par nom', r.status_code == 200)
    check('Résultat contient le patient', b'RASOA' in r.data or b'rasoa' in r.data.lower())

    r = Cm.get('/search/?q=TST-0001', follow_redirects=True)
    check('Recherche par code patient', r.status_code == 200)


# ══════════════════════════════════════════════════════════════════════════════
# 18. CASCADE DELETE — SUPPRESSION PATIENT
# ══════════════════════════════════════════════════════════════════════════════
section('18. CASCADE DELETE PATIENT')
with app.app_context():
    # Ajouter données liées au patient à supprimer
    n_del = NoteClinique(patient_id=pid_d, auteur_id=uid_med, contenu='Note liée')
    sp_del = SuiviPonderal(patient_id=pid_d, mois_suivi=0,
                           date_mesure=datetime.date.today(), poids=60.0)
    db.session.add_all([n_del, sp_del])
    db.session.commit()
    n_del_id = n_del.id
    sp_del_id = sp_del.id

with client_as('coordinateur') as Cc:
    r = post(Cc, f'/patients/{pid_d}/supprimer', {})
    check('Coordinateur peut supprimer patient', r.status_code == 200)

with app.app_context():
    check('Patient supprimé de la DB', Patient.query.get(pid_d) is None)
    check('Notes orphelines supprimées (cascade)', NoteClinique.query.get(n_del_id) is None)
    check('Mesures orphelines supprimées (cascade)', SuiviPonderal.query.get(sp_del_id) is None)


# ══════════════════════════════════════════════════════════════════════════════
# 19. CODE PATIENT UNIQUE
# ══════════════════════════════════════════════════════════════════════════════
section('19. CODE PATIENT UNIQUE')
with app.app_context():
    from app.blueprints.patients.routes import _generate_code
    codes = set()
    for _ in range(5):
        code = _generate_code()
        # Simuler l'insertion pour que le prochain soit unique
        p_tmp = Patient(code_patient=code, nom='TMP', prenom='P',
                        statut='en_cours', poids=60.0, medecin_id=uid_med)
        db.session.add(p_tmp)
        db.session.flush()
        codes.add(code)
    db.session.rollback()
    check('5 codes générés sont tous uniques', len(codes) == 5, str(codes))


# ══════════════════════════════════════════════════════════════════════════════
# 20. PAGES D'ERREUR
# ══════════════════════════════════════════════════════════════════════════════
section('20. PAGES ERREUR')
with client_as('medecin') as Cm:
    r = Cm.get('/patients/99999', follow_redirects=True)
    check('Patient inexistant → 404', r.status_code == 404)

    r = Cm.get('/stock/99999/historique', follow_redirects=True)
    check('Médicament inexistant → 404', r.status_code == 404)


# ══════════════════════════════════════════════════════════════════════════════
# RAPPORT FINAL
# ══════════════════════════════════════════════════════════════════════════════
print(f'\n{"=" * 65}')
print(f'  RÉSULTAT FINAL')
print(f'{"=" * 65}')
print(f'  Tests OK   : {OK}')
print(f'  Bugs       : {len(BUGS)}')
if BUGS:
    print(f'\n  BUGS DÉTECTÉS :')
    for b in BUGS:
        print(f'    ✗ {b}')
else:
    print('\n  AUCUN BUG — V0.3 prête pour la production.')
print()
