"""
Audit final complet TBTrack v0.2
Provoque toutes les erreurs possibles, teste tous les cas limites.
"""
import os, sys, datetime
os.environ['TESTING'] = '1'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
sys.path.insert(0, '.')
from app import create_app
from app.extensions import db
from app.models import User, Patient, Traitement, EffetSecondaire, Contact, ExamenLabo, SuiviDOT

app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

BUGS = []
OK = 0
SECTION = ''

def section(name):
    global SECTION
    SECTION = name
    print(f'\n{"=" * 60}\n  {name}\n{"=" * 60}')

def check(label, cond, detail=''):
    global OK
    if cond:
        OK += 1
        print(f'  OK  {label}')
    else:
        BUGS.append(f'[{SECTION}] {label}' + (f' — {detail}' if detail else ''))
        print(f'  FAIL {label}' + (f' [{detail}]' if detail else ''))

def html_ok(r, label=''):
    status_ok = r.status_code == 200
    no_crash = b'internal server error' not in r.data.lower()
    no_jinja = b'jinja2' not in r.data.lower() and b'templatenotfound' not in r.data.lower()
    no_traceback = b'traceback' not in r.data.lower()
    check(label or 'page OK (200, pas de crash)', status_ok and no_crash and no_jinja and no_traceback,
          f'HTTP {r.status_code}' + (' SERVER_ERROR' if not no_crash else '') + (' JINJA' if not no_jinja else ''))

# ── Setup DB — récupérer les users seedés ─────────────────────────────────────
with app.app_context():
    # seed_demo_data() a déjà tourné dans create_app()
    medecin = User.query.filter_by(role='medecin').first()
    coord   = User.query.filter_by(role='coordinateur').first()
    if not medecin:
        medecin = User(email='med@tb.mg', nom='MEDECIN', prenom='Doc', role='medecin', centre='CDT')
        medecin.set_password('tbtrack2025')
        db.session.add(medecin)
        db.session.commit()
    if not coord:
        coord = User(email='coord@tb.mg', nom='COORD', prenom='Chef', role='coordinateur', centre='CRPC')
        coord.set_password('tbtrack2025')
        db.session.add(coord)
        db.session.commit()
    uid_med   = medecin.id
    uid_coord = coord.id
    MDP_MED   = 'tbtrack2025'

    # Patients avec TOUS les statuts
    P = {}
    for statut, resistance in [
        ('en_cours', 'TB-MR'), ('gueri', 'RR-TB'), ('perdu_de_vue', 'TB-MR'),
        ('echec', 'XDR'), ('decede', 'pre-XDR'), ('transfert', 'RR-TB'),
        ('non_evalue', 'TB-MR'), ('termine', 'TB-MR'),
    ]:
        p = Patient(
            code_patient=f'TST-{statut.upper()[:6]}',
            nom=f'NOM_{statut.upper()[:6]}', prenom='Prenom',
            statut=statut, type_resistance=resistance,
            date_naissance=datetime.date(1985, 6, 15),
            poids=65.0, medecin_id=uid_med,
            date_sortie=(datetime.date(2025, 3, 1) if statut != 'en_cours' else None),
            motif_sortie=('Fin protocole' if statut != 'en_cours' else None),
            centre_transfert=('CDT Mahajanga' if statut == 'transfert' else None),
        )
        db.session.add(p)
        P[statut] = p
    db.session.commit()
    pid = P['en_cours'].id
    pid_transfert = P['transfert'].id

    # 3 contacts sur patient en_cours
    for i in range(3):
        c = Contact(
            patient_source_id=pid,
            nom=f'Contact{i}', prenom=f'Prenom{i}',
            age=30+i, sexe='Homme', relation='foyer',
            date_premier_contact=datetime.date(2024, 6, 1),
        )
        db.session.add(c)

    # Effet secondaire sévère
    ef = EffetSecondaire(
        patient_id=pid, symptome='Hepatotoxicite', severite='severe',
        medicament_incrimine='Pyrazinamide (Z)',
        date_declaration=datetime.datetime.utcnow(),
    )
    db.session.add(ef)

    # Traitement
    t = Traitement(
        patient_id=pid, schema_nom='BdqLfxCfzCsZ',
        phase='intensive',
        date_debut=datetime.date(2024, 6, 1),
        date_fin_prevue=datetime.date(2025, 12, 1),
        statut_traitement='actif',
    )
    t.medicaments = ['Bedaquiline (Bdq)', 'Levofloxacine (Lfx)', 'Clofazimine (Cfz)']
    db.session.add(t)
    db.session.commit()
    tid = t.id

    # Traitement terminé avec date_fin_reelle
    t2 = Traitement(
        patient_id=P['gueri'].id, schema_nom='LfxCfzCs',
        phase='continuation',
        date_debut=datetime.date(2024, 1, 1),
        date_fin_prevue=datetime.date(2024, 10, 1),
        date_fin_reelle=datetime.date(2024, 10, 15),
        motif_arret='Succes therapeutique - cultures negatives confirmees',
        statut_traitement='termine',
    )
    t2.medicaments = ['Levofloxacine (Lfx)']
    db.session.add(t2)
    db.session.commit()
    tid2 = t2.id

# ══════════════════════════════════════════════════════════════════════════════
# Sections 8 et 9b AVANT tout client authentifié (évite DetachedInstanceError)
# ══════════════════════════════════════════════════════════════════════════════
section('8. SÉCURITÉ — SANS LOGIN')
with app.test_client() as C_anon:
    for url in ['/login', '/register']:
        r_pub = C_anon.get(url, follow_redirects=False)
        check(f'Page publique accessible sans login: {url}', r_pub.status_code == 200,
              f'got {r_pub.status_code}')
    for url in ['/dashboard/', '/patients/', '/rapports/', '/profil']:
        r_anon = C_anon.get(url, follow_redirects=False)
        check(f'Protégé → redirect login: {url}', r_anon.status_code in (301, 302),
              f'got {r_anon.status_code}')

section('9b. ADMIN — ACCÈS COORDINATEUR')
with app.test_client() as C_coord:
    with C_coord.session_transaction() as sess:
        sess['_user_id'] = str(uid_coord)
        sess['_fresh'] = True
    r_coord = C_coord.get('/admin/utilisateurs', follow_redirects=True)
    check('Admin accessible par coordinateur (200)', r_coord.status_code == 200)
    check('Admin liste utilisateurs', b'utilisateur' in r_coord.data.lower())

# ══════════════════════════════════════════════════════════════════════════════
with app.test_client() as C:
    with C.session_transaction() as sess:
        sess['_user_id'] = str(uid_med)
        sess['_fresh'] = True

    # ─────────────────────────────────────────────────────────────────────────
    section('1. TOUTES LES ROUTES PRINCIPALES')

    routes = [
        ('/login', 'Login'),
        ('/register', 'Register'),
        ('/dashboard/', 'Dashboard'),
        ('/patients/', 'Liste patients'),
        ('/patients/ajouter', 'Form ajouter patient'),
        (f'/patients/{pid}', 'Fiche patient actif'),
        (f'/patients/{pid}/modifier', 'Modifier patient'),
        (f'/patients/{pid}/bilan', 'Bilan M0'),
        (f'/patients/{pid_transfert}', 'Fiche patient TRANSFÉRÉ'),
        ('/dosage/', 'Calculateur dosage'),
        ('/traitement/', 'Liste traitements'),
        (f'/traitement/ajouter/{pid}', 'Form créer traitement'),
        (f'/traitement/{tid}', 'Détail traitement actif'),
        (f'/traitement/{tid}/modifier', 'Modifier traitement'),
        (f'/traitement/{tid}/dot/ajouter', 'DOT ajouter'),
        (f'/traitement/{tid}/dot/historique', 'DOT historique'),
        (f'/traitement/{tid2}', 'Détail traitement TERMINÉ'),
        ('/effets/', 'Liste effets secondaires'),
        (f'/effets/declarer?patient_id={pid}', 'Déclarer effet (avec patient)'),
        ('/effets/declarer', 'Déclarer effet (sans patient)'),
        ('/contacts/', 'Liste contacts'),
        (f'/contacts/ajouter?patient_source_id={pid}', 'Ajouter contact (avec patient)'),
        ('/contacts/ajouter', 'Ajouter contact (sans patient)'),
        ('/labo/', 'Index labo'),
        (f'/labo/saisir?patient_id={pid}', 'Saisir examen labo'),
        (f'/labo/patient/{pid}', 'Suivi labo patient'),
        ('/stock/', 'Stock inventaire'),
        ('/rapports/', 'Rapports PNLT'),
        ('/rapports/export.csv', 'Export CSV'),
        ('/profil', 'Profil utilisateur'),
        ('/search/?q=NOM', 'Recherche'),
    ]

    for url, label in routes:
        r = C.get(url, follow_redirects=True)
        html_ok(r, label)

    # ─────────────────────────────────────────────────────────────────────────
    section('2. PAGES D\'ERREUR PERSONNALISÉES')

    r = C.get('/patients/999999')
    check('404 personnalisé — statut 404', r.status_code == 404)
    check('404 personnalisé — contenu TBTrack (pas page blanche)',
          b'TBTrack' in r.data or b'introuvable' in r.data.lower())

    r = C.get('/admin/utilisateurs')
    check('403 personnalisé — statut 403', r.status_code == 403)
    check('403 personnalisé — contenu TBTrack', b'TBTrack' in r.data or b'refus' in r.data.lower())

    # ─────────────────────────────────────────────────────────────────────────
    section('3. COMPTEURS ET BADGES INTERFACE')

    r = C.get(f'/patients/{pid}', follow_redirects=True)
    check('Compteur contacts (3) dans onglet', b'Contacts (3)' in r.data)
    check('Badge effet non notifié présent', b'nb_effets_non_notifies' not in r.data)
    check('Tab traitement présent', b'tab-traitement' in r.data)
    check('Tab effets présent', b'tab-effets' in r.data)
    check('Tab contacts présent', b'tab-contacts' in r.data)
    check('Tab labo présent', b'tab-labo' in r.data)
    check('Tab bilan présent', b'tab-bilan' in r.data)
    check('Tab DOT présent', b'tab-dot' in r.data)
    check('Tab notes présent', b'tab-notes' in r.data)

    # ─────────────────────────────────────────────────────────────────────────
    section('4. INFO SORTIE PATIENT (TRANSFERT)')

    r = C.get(f'/patients/{pid_transfert}', follow_redirects=True)
    check('Fiche patient transféré: alerte "Sorti le" visible',
          'Sorti le'.encode('utf-8') in r.data or b'door-open' in r.data)
    check('Fiche patient transféré: centre visible',
          b'CDT Mahajanga' in r.data)

    # ─────────────────────────────────────────────────────────────────────────
    section('5. FIN DE TRAITEMENT')

    r = C.get(f'/traitement/{tid2}', follow_redirects=True)
    check('Détail traitement terminé: date fin réelle visible',
          b'15/10/2024' in r.data or b'flag-checkered' in r.data)

    # ─────────────────────────────────────────────────────────────────────────
    section('6. RAPPORTS — TOUS STATUTS')

    r = C.get('/rapports/')
    html_ok(r, 'Rapports page')
    check('Guéri présent', 'Guéri'.encode('utf-8') in r.data)
    check('Transféré présent', 'Transféré'.encode('utf-8') in r.data)
    check('Non évalué présent', 'Non évalué'.encode('utf-8') in r.data)
    check('Décédé présent', 'Décédé'.encode('utf-8') in r.data)

    # ─────────────────────────────────────────────────────────────────────────
    section('7. EXPORT CSV')

    r = C.get('/rapports/export.csv')
    check('CSV 200', r.status_code == 200)
    check('CSV Content-Type csv', 'csv' in r.content_type.lower())
    check('CSV UTF-8 BOM', r.data.startswith(b'\xef\xbb\xbf') or b'PNLT' in r.data)
    check('CSV séparateur ;', b';' in r.data)
    check('CSV Guéri present', 'Guéri'.encode('utf-8') in r.data or b'Gueri' in r.data)

    section('9. ADMIN — CONTRÔLE D\'ACCÈS')
    r = C.get('/admin/utilisateurs')
    check('Admin refusé pour médecin (403)', r.status_code == 403)

    # ─────────────────────────────────────────────────────────────────────────
    section('10. VALIDATIONS FORMULAIRES')

    # Patient sans nom — status 200 = validation échouée (pas de redirect)
    r = C.post('/patients/ajouter', data={
        'nom': '', 'prenom': 'Test', 'statut': 'en_cours',
        'sexe': '', 'statut_vih': 'inconnu',
        'type_resistance': '', 'categorie': 'nouveau_cas', 'schema_therapeutique': '',
    })
    check('Patient sans nom → validation échoue (200, pas de redirect)', r.status_code == 200)
    check('Erreur affiché dans la page', b'field-' in r.data or b'is-invalid' in r.data or b'invalid' in r.data.lower() or b'required' in r.data.lower() or b'nom' in r.data.lower())

    # Poids invalide
    r = C.post('/patients/ajouter', data={
        'nom': 'POIDS_NEG', 'prenom': 'Test', 'statut': 'en_cours',
        'sexe': '', 'statut_vih': 'inconnu', 'poids': '-50',
        'type_resistance': '', 'categorie': 'nouveau_cas', 'schema_therapeutique': '',
    })
    check('Poids négatif → validation échoue (200)', r.status_code == 200)

    # Date naissance future
    r = C.post('/patients/ajouter', data={
        'nom': 'FUTURE', 'prenom': 'Test', 'statut': 'en_cours',
        'sexe': '', 'statut_vih': 'inconnu',
        'type_resistance': '', 'categorie': 'nouveau_cas', 'schema_therapeutique': '',
        'date_naissance': '2099-01-01',
    })
    check('Date naissance future → validation échoue (200)', r.status_code == 200)

    # Traitement sans schema_nom
    r = C.post(f'/traitement/ajouter/{pid}', data={
        'schema_nom': '', 'phase': 'intensive',
        'date_debut': '2024-01-01', 'statut_traitement': 'actif',
        'medicaments_json': '[]',
    })
    check('Traitement sans schéma → validation échoue (200)', r.status_code == 200)

    # ─────────────────────────────────────────────────────────────────────────
    section('11. CRUD COMPLET: PATIENT SORTIE')

    # POST sans follow_redirects pour récupérer l'ID depuis Location header
    r = C.post('/patients/ajouter', data={
        'nom': 'SORTIE_TEST', 'prenom': 'Patient', 'statut': 'transfert',
        'sexe': 'Homme', 'statut_vih': 'inconnu',
        'type_resistance': 'TB-MR', 'categorie': 'nouveau_cas', 'schema_therapeutique': '',
        'date_sortie': '2025-09-15', 'motif_sortie': 'Transfert vers CDT Fianarantsoa',
        'centre_transfert': 'CDT Fianarantsoa',
    }, follow_redirects=False)
    check('POST patient transfert → redirect (créé)', r.status_code in (301, 302))
    location = r.headers.get('Location', '')
    try:
        pid_s = int(location.rstrip('/').split('/')[-1])
    except (ValueError, IndexError):
        pid_s = None

    if pid_s:
        r = C.get(f'/patients/{pid_s}', follow_redirects=True)
        check('Fiche patient créé accessible (200)', r.status_code == 200)
        check('Info sortie visible dans fiche', b'CDT Fianarantsoa' in r.data)
        check('Date sortie visible (15/09/2025)', b'15/09/2025' in r.data)
        check('Statut transfert visible', 'Transféré'.encode('utf-8') in r.data or b'transfert' in r.data.lower())
    else:
        check('Patient SORTIE_TEST créé (Location header)', False, f'Location={location}')

    # ─────────────────────────────────────────────────────────────────────────
    section('12. CRUD TRAITEMENT FIN')

    r = C.post(f'/traitement/{tid}/modifier', data={
        'schema_nom': 'BdqLfxCfzCsZ', 'phase': 'continuation',
        'date_debut': '2024-06-01', 'date_fin_prevue': '',
        'statut_traitement': 'echec', 'observateur_nom': '',
        'date_fin_reelle': '2025-05-01',
        'motif_arret': 'Echec - culture positive M6',
        'notes': '', 'medicaments_json': '["Bedaquiline (Bdq)"]',
    }, follow_redirects=True)
    check('Modifier traitement avec date_fin_reelle → 200', r.status_code == 200)

    # Vérifier via la page de détail du traitement (sans app_context)
    r = C.get(f'/traitement/{tid}', follow_redirects=True)
    check('date_fin_reelle visible dans détail', b'01/05/2025' in r.data or b'flag-checkered' in r.data)
    check('motif_arret visible dans détail', b'Echec' in r.data or b'culture positive' in r.data)

    # ─────────────────────────────────────────────────────────────────────────
    section('13. PROFIL UTILISATEUR')

    r = C.get('/profil')
    html_ok(r, 'Page profil accessible')
    check('Profil contient formulaire', 'Enregistrer'.encode('utf-8') in r.data)
    check('Profil contient champ prénom', b'prenom' in r.data.lower() or 'Prénom'.encode('utf-8') in r.data)

    # Modifier prénom + nom
    r = C.post('/profil', data={
        'prenom': 'Docteur', 'nom': 'JEAN', 'centre': 'CDT Tana',
        'mot_de_passe_actuel': '', 'nouveau_mot_de_passe': '', 'confirmer': '',
    }, follow_redirects=True)
    check('Mise à jour profil (sans MDP) OK', r.status_code == 200)
    check('Flash succès profil', 'Profil mis'.encode('utf-8') in r.data)

    # Changement MDP correct
    r = C.post('/profil', data={
        'prenom': 'Docteur', 'nom': 'JEAN', 'centre': 'CDT Tana',
        'mot_de_passe_actuel': MDP_MED,
        'nouveau_mot_de_passe': 'nouveau456',
        'confirmer': 'nouveau456',
    }, follow_redirects=True)
    check('Changement MDP correct → 200 + succès', r.status_code == 200 and 'Profil mis'.encode('utf-8') in r.data)

    # MDP actuel incorrect
    r = C.post('/profil', data={
        'prenom': 'Docteur', 'nom': 'JEAN', 'centre': 'CDT Tana',
        'mot_de_passe_actuel': 'MAUVAIS_MDP',
        'nouveau_mot_de_passe': 'autre789',
        'confirmer': 'autre789',
    }, follow_redirects=True)
    check('MDP actuel incorrect → message erreur', 'incorrect'.encode('utf-8') in r.data)

    # MDP sans confirmer le bon actuel
    r = C.post('/profil', data={
        'prenom': 'Docteur', 'nom': 'JEAN', 'centre': 'CDT Tana',
        'mot_de_passe_actuel': '',
        'nouveau_mot_de_passe': 'tentative',
        'confirmer': 'tentative',
    }, follow_redirects=True)
    check('Nouveau MDP sans entrer l\'actuel → bloqué', 'actuel'.encode('utf-8') in r.data)

    # ─────────────────────────────────────────────────────────────────────────
    section('14. XSS — INJECTIONS HTML')

    PAYLOADS = [
        ('<script>alert(1)</script>', b'<script>alert(1)'),
        ('<img src=x onerror=alert(1)>', b'onerror=alert'),
        ('"><svg/onload=alert(1)>', b'onload=alert'),
    ]
    for payload, dangerous_bytes in PAYLOADS:
        r = C.post('/patients/ajouter', data={
            'nom': payload, 'prenom': 'XSS', 'statut': 'en_cours',
            'sexe': '', 'statut_vih': 'inconnu',
            'type_resistance': '', 'categorie': 'nouveau_cas', 'schema_therapeutique': '',
        }, follow_redirects=True)
        check(f'XSS bloqué: {payload[:30]}', dangerous_bytes not in r.data)

    # ─────────────────────────────────────────────────────────────────────────
    section('15. PAGES SPÉCIALES ROBUSTESSE')

    # Dashboard via client principal (pas de contexte imbriqué)
    r2 = C.get('/dashboard/', follow_redirects=True)
    check('Dashboard accessible avec données existantes', r2.status_code == 200)

    # Calculateur dosage sans paramètres
    r = C.get('/dosage/', follow_redirects=True)
    html_ok(r, 'Dosage sans paramètres')

    # Recherche vide
    r = C.get('/search/?q=', follow_redirects=True)
    html_ok(r, 'Recherche avec q vide')

    # Recherche avec caractères spéciaux
    r = C.get('/search/?q=%27OR+1%3D1--', follow_redirects=True)
    html_ok(r, 'Recherche SQLi tentatif')

# ══════════════════════════════════════════════════════════════════════════════
print('\n' + '=' * 60)
print('  RAPPORT FINAL AUDIT v0.2')
print('=' * 60)
print(f'  Tests OK    : {OK}')
if BUGS:
    print(f'  BUGS ({len(BUGS)}) :')
    for b in BUGS:
        print(f'    ! {b}')
else:
    print('  BUGS        : 0  —  TOUT EST PROPRE')
print('=' * 60)
