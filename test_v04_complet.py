"""
TEST V0.4 COMPLET — Avant déploiement production
Couvre : Jinja2, round-trip DB, logique clinique, routes, formulaires,
         migration, filtres, alertes, calculateur, edge cases.
Usage : python test_v04_complet.py
"""
import sys, os, subprocess, sqlite3, importlib
sys.path.insert(0, os.path.dirname(__file__))

OK = FAIL = 0

def ok(msg):
    global OK; OK += 1; print(f"  OK   {msg}")

def fail(msg, detail=""):
    global FAIL; FAIL += 1
    d = f"\n       >> {detail}" if detail else ""
    print(f"  FAIL {msg}{d}")

def section(title):
    print(f"\n{'='*62}\n  {title}\n{'='*62}")

# ─────────────────────────────────────────────────────────────
section("1. SYNTAXE PYTHON — tous les modules de l'app")
# ─────────────────────────────────────────────────────────────
import py_compile, glob as gglob
py_files = gglob.glob("app/**/*.py", recursive=True)
py_files += gglob.glob("*.py")
for f in sorted(py_files):
    if '.venv' in f or '__pycache__' in f:
        continue
    try:
        py_compile.compile(f, doraise=True)
        ok(f"Syntaxe OK : {f}")
    except py_compile.PyCompileError as e:
        fail(f"Erreur syntaxe : {f}", str(e))

# ─────────────────────────────────────────────────────────────
section("2. JINJA2 — syntaxe de tous les templates")
# ─────────────────────────────────────────────────────────────
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError

env = Environment(loader=FileSystemLoader("app/templates"))
html_files = gglob.glob("app/templates/**/*.html", recursive=True)
for f in sorted(html_files):
    rel = f.replace("app/templates/", "").replace("app\\templates\\", "").replace("\\", "/")
    try:
        env.parse(open(f, encoding="utf-8").read())
        ok(f"Jinja2 OK : {rel}")
    except TemplateSyntaxError as e:
        fail(f"Jinja2 erreur : {rel}", f"ligne {e.lineno}: {e.message}")

# ─────────────────────────────────────────────────────────────
section("3. JINJA2 — filtre selectattr 'ge' (suivi_patient.html)")
# ─────────────────────────────────────────────────────────────
from jinja2 import Environment as JEnv

jenv = JEnv()
class FakeExamen:
    def __init__(self, mois, culture):
        self.mois_suivi = mois
        self.culture_resultat = culture

fake_examens = [
    FakeExamen(2, 'negatif'), FakeExamen(5, 'negatif'),
    FakeExamen(6, 'positif'), FakeExamen(8, 'positif'),
]
tmpl = jenv.from_string(
    "{% set r = items | selectattr('mois_suivi','ge',6) | selectattr('culture_resultat','equalto','positif') | list %}"
    "{{ r | length }}"
)
result = tmpl.render(items=fake_examens)
if result.strip() == '2':
    ok("Filtre selectattr 'ge' fonctionne (2 résultats ≥ M6 positifs)")
else:
    fail("Filtre selectattr 'ge'", f"résultat={result}, attendu=2")

# ─────────────────────────────────────────────────────────────
section("4. IMPORT — create_app et tous les blueprints")
# ─────────────────────────────────────────────────────────────
from app import create_app
try:
    app = create_app()
    ok("create_app() sans erreur")
except Exception as e:
    fail("create_app() a levé une exception", str(e))
    sys.exit(1)

with app.app_context():
    from app.models import (Patient, BilanInitial, ExamenLabo,
                             SuiviPonderal, ExamenLabo, NoteClinique)
    from app.models.traitement import Traitement
    from app.models.user import User
    from app.extensions import db
    ok("Tous les modèles importés")

# Helper : injecter directement l'id user dans la session Flask-Login
def login_test_client(client, user_id):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True

def get_or_create_test_user():
    """Retourne (user_id, created) d'un user coordinateur de test."""
    u = User.query.filter_by(email='v04test@tbtrack.mg').first()
    if not u:
        u = User(email='v04test@tbtrack.mg', nom='TESTV04', prenom='Auto',
                 role='coordinateur', centre='Test')
        u.set_password('TestAuto2026!')
        db.session.add(u)
        db.session.commit()
        return u.id, True
    return u.id, False

# Nettoyage des données de test résidus de runs précédents
with app.app_context():
    Patient.query.filter(Patient.code_patient.like('TEST-V04-%')).delete(synchronize_session=False)
    Patient.query.filter(Patient.code_patient.like('TCAT-%')).delete(synchronize_session=False)
    db.session.commit()

# ─────────────────────────────────────────────────────────────
section("5. ROUND-TRIP DB — BilanInitial : tous les nouveaux champs")
# ─────────────────────────────────────────────────────────────
with app.app_context():
    from app.models import Patient
    # Créer un patient de test
    p_test = Patient(
        code_patient='TEST-V04-BILAN', nom='TESTBILAN', prenom='V04',
        statut='en_cours', statut_vih='inconnu',
    )
    db.session.add(p_test)
    db.session.flush()

    b = BilanInitial(
        patient_id=p_test.id,
        date_bilan=__import__('datetime').date.today(),
        poids_kg=65.0, taille_cm=170.0,
        creatinine_umol_l=88.0, clairance_creatinine=82.0,
        hb_g_dl=12.5, leucocytes_g_l=5.2, plaquettes_g_l=230.0,
        alt_u_l=35.0, ast_u_l=28.0,
        glycemie_mmol_l=5.1, kaliemie_mmol_l=4.0,
        test_grossesse=False, rx_thorax_normale=True,
        lpa_1ere_ligne='H résistant / R résistant',
        lpa_2eme_ligne='FQ sensible / Am sensible',
        ecg_qt_ms=420, ecg_j7_qt_ms=460,
        tsh_miu_l=3.2,
        audiogramme_normal=True, acuite_visuelle_normale=True,
        thyroide_normale=True,
    )
    db.session.add(b)
    db.session.commit()
    pid = p_test.id
    bid = b.id

    # Relire depuis la DB
    b2 = db.session.get(BilanInitial, bid)
    for field, expected in [
        ('lpa_1ere_ligne',  'H résistant / R résistant'),
        ('lpa_2eme_ligne',  'FQ sensible / Am sensible'),
        ('leucocytes_g_l',  5.2),
        ('plaquettes_g_l',  230.0),
        ('ecg_j7_qt_ms',    460),
        ('tsh_miu_l',       3.2),
        ('rx_thorax_normale', True),
        ('test_grossesse',    False),
    ]:
        val = getattr(b2, field)
        if val == expected:
            ok(f"BilanInitial.{field} = {expected}")
        else:
            fail(f"BilanInitial.{field}", f"attendu={expected}, obtenu={val}")

    # Propriétés calculées
    if b2.ecg_alerte is None:
        ok("ecg_alerte M0 QTc=420 → None (normal)")
    else:
        fail("ecg_alerte M0 QTc=420", str(b2.ecg_alerte))

    if b2.ecg_alerte_j7 == 'surveillance':
        ok("ecg_alerte_j7 QTc=460 → 'surveillance'")
    else:
        fail("ecg_alerte_j7 QTc=460", str(b2.ecg_alerte_j7))

    if not b2.tsh_alerte:
        ok("tsh_alerte TSH=3.2 → False (< 6.75)")
    else:
        fail("tsh_alerte TSH=3.2 devrait être False")

    if b2.imc and abs(b2.imc - 22.5) < 1.0:
        ok(f"IMC calculé = {b2.imc}")
    else:
        fail("IMC", str(b2.imc))

    db.session.delete(p_test)
    db.session.commit()

# ─────────────────────────────────────────────────────────────
section("6. ROUND-TRIP DB — ExamenLabo : 12 champs DST")
# ─────────────────────────────────────────────────────────────
with app.app_context():
    p_test2 = Patient(code_patient='TEST-V04-LABO', nom='TESTLABO', prenom='V04',
                      statut='en_cours', statut_vih='inconnu')
    db.session.add(p_test2)
    from app.models.user import User
    u = User.query.first()
    db.session.flush()

    e = ExamenLabo(
        patient_id=p_test2.id, laborantin_id=u.id,
        mois_suivi=6, date_prelevement=__import__('datetime').date.today(),
        dst_effectue=True,
        dst_isoniazide='resistant', dst_rifampicine='resistant',
        dst_ethambutol='sensible', dst_pyrazinamide='sensible',
        dst_levofloxacine='sensible', dst_moxifloxacine='sensible',
        dst_bedaquiline='sensible', dst_linezolide='sensible',
        dst_amikacine='resistant', dst_kanamycine='resistant',
        dst_capreomycine='sensible', dst_ofloxacine='resistant',
        culture_resultat='positif',
    )
    db.session.add(e)
    db.session.commit()
    eid = e.id

    e2 = db.session.get(ExamenLabo, eid)
    for field, expected in [
        ('dst_amikacine',   'resistant'),
        ('dst_kanamycine',  'resistant'),
        ('dst_capreomycine','sensible'),
        ('dst_ofloxacine',  'resistant'),
    ]:
        if getattr(e2, field) == expected:
            ok(f"ExamenLabo.{field} = {expected}")
        else:
            fail(f"ExamenLabo.{field}", f"attendu={expected}, obtenu={getattr(e2, field)}")

    summary = e2.dst_summary()
    if len(summary) == 12:
        ok(f"dst_summary() retourne 12 molécules")
    else:
        fail("dst_summary()", f"retourne {len(summary)} molécules, attendu 12")

    db.session.delete(p_test2)
    db.session.commit()

# ─────────────────────────────────────────────────────────────
section("7. ROUND-TRIP DB — SuiviPonderal : 6 champs biologiques")
# ─────────────────────────────────────────────────────────────
with app.app_context():
    p_test3 = Patient(code_patient='TEST-V04-SUIVI', nom='TESTSUIVI', prenom='V04',
                      statut='en_cours', statut_vih='inconnu')
    db.session.add(p_test3)
    db.session.flush()

    sp = SuiviPonderal(
        patient_id=p_test3.id, mois_suivi=2,
        date_mesure=__import__('datetime').date.today(),
        poids=58.0, taille=165.0,
        kaliemie_mmol_l=3.8, creatinine_umol_l=92.0,
        gpt_u_l=45.0, got_u_l=38.0,
        leucocytes_g_l=4.5, plaquettes_g_l=210.0,
    )
    db.session.add(sp)
    db.session.commit()
    spid = sp.id

    sp2 = db.session.get(SuiviPonderal, spid)
    for field, expected in [
        ('kaliemie_mmol_l',   3.8),
        ('creatinine_umol_l', 92.0),
        ('gpt_u_l',           45.0),
        ('got_u_l',           38.0),
        ('leucocytes_g_l',    4.5),
        ('plaquettes_g_l',    210.0),
    ]:
        if getattr(sp2, field) == expected:
            ok(f"SuiviPonderal.{field} = {expected}")
        else:
            fail(f"SuiviPonderal.{field}", f"attendu={expected}, obtenu={getattr(sp2, field)}")

    db.session.delete(p_test3)
    db.session.commit()

# ─────────────────────────────────────────────────────────────
section("8. PROPRIÉTÉS PATIENT — alertes cliniques V0.4")
# ─────────────────────────────────────────────────────────────
with app.app_context():
    u = User.query.first()

    # Patient avec ECG stop
    p_ecg = Patient(code_patient='TEST-V04-ECG', nom='TESTECG', prenom='V04',
                    statut='en_cours', statut_vih='inconnu')
    db.session.add(p_ecg)
    db.session.flush()
    b_stop = BilanInitial(patient_id=p_ecg.id,
                          date_bilan=__import__('datetime').date.today(),
                          ecg_qt_ms=510)  # ≥ 500 → stop
    db.session.add(b_stop)
    db.session.commit()
    p_ecg = db.session.get(Patient, p_ecg.id)
    if p_ecg.alerte_ecg_critique:
        ok("Patient.alerte_ecg_critique = True (QTc=510ms)")
    else:
        fail("Patient.alerte_ecg_critique devrait être True pour QTc=510ms")

    # Patient sans ECG alerte
    p_normal = Patient(code_patient='TEST-V04-ECG2', nom='TESTECG2', prenom='V04',
                       statut='en_cours', statut_vih='inconnu')
    db.session.add(p_normal)
    db.session.flush()
    b_ok = BilanInitial(patient_id=p_normal.id,
                        date_bilan=__import__('datetime').date.today(),
                        ecg_qt_ms=420)
    db.session.add(b_ok)
    db.session.commit()
    p_normal = db.session.get(Patient, p_normal.id)
    if not p_normal.alerte_ecg_critique:
        ok("Patient.alerte_ecg_critique = False (QTc=420ms)")
    else:
        fail("Patient.alerte_ecg_critique devrait être False pour QTc=420ms")

    # Patient avec échec thérapeutique (culture+ à M6)
    p_echec = Patient(code_patient='TEST-V04-ECHEC', nom='TESTECHEC', prenom='V04',
                      statut='en_cours', statut_vih='inconnu')
    db.session.add(p_echec)
    db.session.flush()
    e_m6 = ExamenLabo(patient_id=p_echec.id, laborantin_id=u.id,
                      mois_suivi=6, date_prelevement=__import__('datetime').date.today(),
                      culture_resultat='positif')
    db.session.add(e_m6)
    db.session.commit()
    p_echec = db.session.get(Patient, p_echec.id)
    if p_echec.alerte_echec_therapeutique:
        ok("Patient.alerte_echec_therapeutique = True (culture+ M6)")
    else:
        fail("Patient.alerte_echec_therapeutique devrait être True")

    # Même patient avec culture+ uniquement à M2 (pas un échec)
    p_ok2 = Patient(code_patient='TEST-V04-OK2', nom='TESTOK2', prenom='V04',
                    statut='en_cours', statut_vih='inconnu')
    db.session.add(p_ok2)
    db.session.flush()
    e_m2 = ExamenLabo(patient_id=p_ok2.id, laborantin_id=u.id,
                      mois_suivi=2, date_prelevement=__import__('datetime').date.today(),
                      culture_resultat='positif')
    db.session.add(e_m2)
    db.session.commit()
    p_ok2 = db.session.get(Patient, p_ok2.id)
    if not p_ok2.alerte_echec_therapeutique:
        ok("Patient.alerte_echec_therapeutique = False (culture+ M2 seulement)")
    else:
        fail("Patient.alerte_echec_therapeutique devrait être False (M2 < M6)")

    # categorie_label
    p_cat = Patient(code_patient='TEST-V04-CAT', nom='TESTCAT', prenom='V04',
                    statut='en_cours', statut_vih='inconnu', categorie='echec_tbmr')
    db.session.add(p_cat)
    db.session.commit()
    p_cat = db.session.get(Patient, p_cat.id)
    if p_cat.categorie_label == 'E4 — Échec schéma TB-MR':
        ok("Patient.categorie_label = 'E4 — Échec schéma TB-MR'")
    else:
        fail("Patient.categorie_label", str(p_cat.categorie_label))

    # Cleanup
    for obj in [p_ecg, p_normal, p_echec, p_ok2, p_cat]:
        db.session.delete(db.session.get(Patient, obj.id))
    db.session.commit()

# ─────────────────────────────────────────────────────────────
section("9. ECG — tous les seuils limites précis")
# ─────────────────────────────────────────────────────────────
cases = [
    (None,  None),
    (449,   None),
    (450,   None),
    (451,   'surveillance'),
    (499,   'surveillance'),
    (500,   'stop'),
    (501,   'stop'),
    (600,   'stop'),
]
for qt, expected in cases:
    b = BilanInitial()
    b.ecg_qt_ms = qt
    result = b.ecg_alerte
    if result == expected:
        ok(f"ECG QTc={qt}ms → {expected!r}")
    else:
        fail(f"ECG QTc={qt}ms", f"attendu={expected!r}, obtenu={result!r}")

# ─────────────────────────────────────────────────────────────
section("10. TSH — seuils")
# ─────────────────────────────────────────────────────────────
for tsh, expected in [(None, False), (1.0, False), (6.74, False), (6.75, False), (6.76, True), (10.0, True)]:
    b = BilanInitial(); b.tsh_miu_l = tsh
    if b.tsh_alerte == expected:
        ok(f"TSH={tsh} → tsh_alerte={expected}")
    else:
        fail(f"TSH={tsh}", f"attendu={expected}, obtenu={b.tsh_alerte}")

# ─────────────────────────────────────────────────────────────
section("11. CALCULATEUR — Hr-TB doses précises")
# ─────────────────────────────────────────────────────────────
from app.blueprints.dosage.calculateur import calculer_doses, DOSES_ADULTE, DOSES_ENFANT

# Adulte 36-45 kg (index 1)
r = calculer_doses(40.0, adulte=True, schema='hr_tb')
meds = {m['nom']: m['dose'] for m in r['medicaments']}
if meds.get('Isoniazide') == 1.5:
    ok("Hr-TB adulte 40kg : Isoniazide = 1.5 cp")
else:
    fail("Hr-TB adulte 40kg Isoniazide", str(meds.get('Isoniazide')))
if meds.get('Levofloxacine') == 3:
    ok("Hr-TB adulte 40kg : Levofloxacine = 3 cp")
else:
    fail("Hr-TB adulte 40kg Levofloxacine", str(meds.get('Levofloxacine')))

# Enfant 12 kg (index 2 = 10-15 kg)
r2 = calculer_doses(12.0, adulte=False, schema='hr_tb')
meds2 = {m['nom']: m['dose'] for m in r2['medicaments']}
if meds2.get('Levofloxacine') == 1:
    ok("Hr-TB enfant 12kg : Levofloxacine = 1 cp")
else:
    fail("Hr-TB enfant 12kg Levofloxacine", str(meds2.get('Levofloxacine')))
if meds2.get('Isoniazide') == 2:
    ok("Hr-TB enfant 12kg : Isoniazide = 2 cp")
else:
    fail("Hr-TB enfant 12kg Isoniazide", str(meds2.get('Isoniazide')))

# ─────────────────────────────────────────────────────────────
section("12. CALCULATEUR — CI Delamanide et Bedaquiline pédiatrique")
# ─────────────────────────────────────────────────────────────
# Enfant 5 kg (index 0 = 5-6 kg)
r3 = calculer_doses(5.5, adulte=False, schema='long_enfant')
meds3 = {m['nom']: m['dose'] for m in r3['medicaments']}
dlm_dose = meds3.get('Delamanide')
if dlm_dose == 'CI (<7 kg)':
    ok("Delamanide enfant 5.5kg → dose = 'CI (<7 kg)'")
else:
    fail("Delamanide enfant 5.5kg", str(dlm_dose))

# Enfant 8 kg (index 1 = 7-9 kg) — doit avoir une vraie dose
r4 = calculer_doses(8.0, adulte=False, schema='long_enfant')
meds4 = {m['nom']: m['dose'] for m in r4['medicaments']}
dlm_dose2 = meds4.get('Delamanide')
if dlm_dose2 == '0.5 cp ×2/j':
    ok("Delamanide enfant 8kg → dose = '0.5 cp ×2/j'")
else:
    fail("Delamanide enfant 8kg", str(dlm_dose2))

# Bedaquiline enfant 5.5 kg → CI
r5 = calculer_doses(5.5, adulte=False, schema='pre_xdr_xdr')
meds5 = {m['nom']: m['dose'] for m in r5['medicaments']}
bdq_dose = meds5.get('Bedaquiline')
if bdq_dose and str(bdq_dose).startswith('CI'):
    ok(f"Bedaquiline enfant 5.5kg → CI marqué: '{bdq_dose}'")
else:
    fail("Bedaquiline enfant 5.5kg CI", str(bdq_dose))

# ─────────────────────────────────────────────────────────────
section("13. ROUTES — chaque endpoint répond 200/302 (session auth)")
# ─────────────────────────────────────────────────────────────
app.config['WTF_CSRF_ENABLED'] = False
with app.test_client() as client:
    with app.app_context():
        uid13, _ = get_or_create_test_user()
        pid = Patient.query.first().id if Patient.query.first() else None
    login_test_client(client, uid13)

    routes_to_test = [
        ('GET', '/dashboard/', 200),
        ('GET', '/patients/', 200),
        ('GET', f'/patients/{pid}', 200) if pid else None,
        ('GET', f'/patients/{pid}/bilan', 200) if pid else None,
        ('GET', f'/patients/{pid}/parametres', 200) if pid else None,
        ('GET', '/labo/', 200),
        ('GET', '/labo/saisir', 200),
        ('GET', '/rapports/', 200),
        ('GET', '/rapports/annuel', 200),
        ('GET', '/rapports/depistage', 200),
        ('GET', '/rapports/commande', 200),
        ('GET', '/contacts/', 200),
        ('GET', '/stock/', 200),
        ('GET', '/dosage/', 200),
        ('GET', '/admin/utilisateurs', 200),
    ]
    for item in routes_to_test:
        if item is None:
            continue
        method, url, expected = item
        try:
            r = client.get(url, follow_redirects=True)
            if r.status_code == expected:
                ok(f"{method} {url} → {r.status_code}")
            else:
                fail(f"{method} {url}", f"attendu={expected}, obtenu={r.status_code}")
        except Exception as e:
            fail(f"{method} {url}", str(e))

# ─────────────────────────────────────────────────────────────
section("14. RENDU JINJA2 — templates avec données réelles")
# ─────────────────────────────────────────────────────────────
with app.test_client() as client:
    with app.app_context():
        uid14, _ = get_or_create_test_user()
    login_test_client(client, uid14)

    with app.app_context():
        # Créer patient avec TOUTES les données (bilan complet, ECG, labo)
        p_full = Patient(
            code_patient='TEST-V04-FULL', nom='TESTFULL', prenom='V04',
            statut='en_cours', statut_vih='negatif', categorie='echec_tbmr',
            type_resistance='TB-MR',
        )
        db.session.add(p_full)
        db.session.flush()

        b_full = BilanInitial(
            patient_id=p_full.id,
            date_bilan=__import__('datetime').date.today(),
            poids_kg=60.0, taille_cm=165.0,
            ecg_qt_ms=510,   # → 'stop' alerte critique
            ecg_j7_qt_ms=460,  # → 'surveillance'
            tsh_miu_l=7.8,   # → alerte TSH
            lpa_1ere_ligne='H résistant',
            lpa_2eme_ligne='FQ sensible',
            rx_thorax_normale=False,
            test_grossesse=True,
            leucocytes_g_l=1.8,  # → critique Lzd
            plaquettes_g_l=180.0,
            hb_g_dl=9.5, creatinine_umol_l=95.0, clairance_creatinine=75.0,
        )
        db.session.add(b_full)

        u_first = User.query.first()
        e_m6_full = ExamenLabo(
            patient_id=p_full.id, laborantin_id=u_first.id,
            mois_suivi=6, date_prelevement=__import__('datetime').date.today(),
            culture_resultat='positif',
            dst_effectue=True,
            dst_amikacine='resistant', dst_kanamycine='sensible',
        )
        db.session.add(e_m6_full)
        db.session.commit()
        pfid = p_full.id

    # Fiche patient complète
    r = client.get(f'/patients/{pfid}', follow_redirects=True)
    body = r.data.decode('utf-8', errors='replace')

    checks = [
        ('ALERTE ECG',             "Alerte ECG stop visible"),
        ('ÉCHEC THÉRAPEUTIQUE',     "Alerte échec thérapeutique visible"),
        ('H résistant',             "LPA 1ère ligne visible"),
        ('FQ sensible',             "LPA 2ème ligne visible"),
        ('TSH',                     "TSH visible"),
        ('ECG QTc J7',              "ECG J7 visible"),
        ('Leuco',                   "Leucocytes visibles"),
        ('Plaq',                    "Plaquettes visibles"),
    ]
    for keyword, desc in checks:
        if keyword in body:
            ok(f"Fiche patient : {desc}")
        else:
            fail(f"Fiche patient : {desc}", f"'{keyword}' absent de la réponse")

    # Bilan M0 — formulaire avec nouveaux champs
    r2 = client.get(f'/patients/{pfid}/bilan', follow_redirects=True)
    body2 = r2.data.decode('utf-8', errors='replace')
    for field_name in ['test_grossesse', 'rx_thorax_normale', 'lpa_1ere_ligne',
                        'lpa_2eme_ligne', 'tsh_miu_l', 'ecg_j7_qt_ms',
                        'leucocytes_g_l', 'plaquettes_g_l']:
        if field_name in body2:
            ok(f"Bilan M0 formulaire : champ '{field_name}' rendu")
        else:
            fail(f"Bilan M0 formulaire : champ '{field_name}' absent du rendu")

    # Dashboard — alertes cliniques
    r3 = client.get('/dashboard/', follow_redirects=True)
    body3 = r3.data.decode('utf-8', errors='replace')
    if 'ECG CRITIQUE' in body3:
        ok("Dashboard : panel ECG CRITIQUE visible")
    else:
        fail("Dashboard : panel ECG CRITIQUE absent")
    if 'ÉCHEC THÉRAPEUTIQUE' in body3:
        ok("Dashboard : panel ÉCHEC THÉRAPEUTIQUE visible")
    else:
        fail("Dashboard : panel ÉCHEC THÉRAPEUTIQUE absent")

    # Suivi labo — alerte échec
    r4 = client.get(f'/labo/patient/{pfid}', follow_redirects=True)
    body4 = r4.data.decode('utf-8', errors='replace')
    if 'ÉCHEC THÉRAPEUTIQUE POTENTIEL' in body4:
        ok("Suivi labo : alerte échec thérapeutique visible")
    else:
        fail("Suivi labo : alerte échec thérapeutique absente")

    # Saisie labo — 4 nouveaux champs DST
    r5 = client.get('/labo/saisir', follow_redirects=True)
    body5 = r5.data.decode('utf-8', errors='replace')
    for mol in ['dst_amikacine', 'dst_kanamycine', 'dst_capreomycine', 'dst_ofloxacine']:
        if mol in body5:
            ok(f"Saisie labo : champ '{mol}' rendu")
        else:
            fail(f"Saisie labo : champ '{mol}' absent")

    # Calculateur dosage — schéma Hr-TB visible
    r6 = client.get('/dosage/', follow_redirects=True)
    body6 = r6.data.decode('utf-8', errors='replace')
    if 'Hr-TB' in body6:
        ok("Calculateur : schéma Hr-TB affiché")
    else:
        fail("Calculateur : schéma Hr-TB absent")

    # Cleanup
    with app.app_context():
        db.session.delete(db.session.get(Patient, pfid))
        db.session.commit()

# ─────────────────────────────────────────────────────────────
section("15. FORMULAIRES — POST nouveaux champs biologiques sauvegardés")
# ─────────────────────────────────────────────────────────────
with app.test_client() as client:
    with app.app_context():
        uid15, _ = get_or_create_test_user()
        p_form = Patient(code_patient='TEST-V04-FORM', nom='TESTFORM', prenom='V04',
                         statut='en_cours', statut_vih='inconnu')
        db.session.add(p_form)
        db.session.commit()
        pfm_id = p_form.id

    login_test_client(client, uid15)

    # POST SuiviPonderal avec nouveaux champs
    resp = client.post(f'/patients/{pfm_id}/parametres', data={
        'mois_suivi': '3', 'date_mesure': '2026-05-23',
        'poids': '62.0',
        'kaliemie_mmol_l': '3.2',
        'creatinine_umol_l': '110.0',
        'gpt_u_l': '85.0',
        'got_u_l': '70.0',
        'leucocytes_g_l': '3.1',
        'plaquettes_g_l': '195.0',
    }, follow_redirects=True)

    with app.app_context():
        sp = SuiviPonderal.query.filter_by(patient_id=pfm_id, mois_suivi=3).first()
    if sp:
        checks = [
            ('kaliemie_mmol_l', 3.2), ('creatinine_umol_l', 110.0),
            ('gpt_u_l', 85.0), ('got_u_l', 70.0),
            ('leucocytes_g_l', 3.1), ('plaquettes_g_l', 195.0),
        ]
        for field, expected in checks:
            val = getattr(sp, field)
            if val is not None and abs(val - expected) < 0.01:
                ok(f"POST SuiviPonderal : {field}={val} sauvegardé")
            else:
                fail(f"POST SuiviPonderal : {field}", f"attendu={expected}, obtenu={val}")
    else:
        fail("POST SuiviPonderal", "Mesure non créée en DB")

    # POST BilanInitial avec nouveaux champs
    resp2 = client.post(f'/patients/{pfm_id}/bilan', data={
        'date_bilan': '2026-05-23',
        'poids_kg': '62.0', 'taille_cm': '168.0',
        'lpa_1ere_ligne': 'Test LPA 1',
        'lpa_2eme_ligne': 'Test LPA 2',
        'ecg_j7_qt_ms': '455',
        'tsh_miu_l': '8.5',
        'leucocytes_g_l': '2.1',
        'plaquettes_g_l': '155.0',
    }, follow_redirects=True)

    with app.app_context():
        bfm = BilanInitial.query.filter_by(patient_id=pfm_id).first()
    if bfm:
        for field, expected in [
            ('lpa_1ere_ligne', 'Test LPA 1'),
            ('lpa_2eme_ligne', 'Test LPA 2'),
            ('ecg_j7_qt_ms', 455),
            ('tsh_miu_l', 8.5),
            ('leucocytes_g_l', 2.1),
            ('plaquettes_g_l', 155.0),
        ]:
            val = getattr(bfm, field)
            if val == expected or (isinstance(expected, float) and abs(val - expected) < 0.01):
                ok(f"POST BilanInitial : {field}={val} sauvegardé")
            else:
                fail(f"POST BilanInitial : {field}", f"attendu={expected}, obtenu={val}")

        # Vérifier alerte TSH (8.5 > 6.75)
        if bfm.tsh_alerte:
            ok("POST BilanInitial : tsh_alerte = True (8.5 > 6.75)")
        else:
            fail("POST BilanInitial : tsh_alerte devrait être True pour 8.5")

        # Vérifier ECG J7 alerte (455 → surveillance)
        if bfm.ecg_alerte_j7 == 'surveillance':
            ok("POST BilanInitial : ecg_alerte_j7 = 'surveillance' (455ms)")
        else:
            fail("POST BilanInitial : ecg_alerte_j7", str(bfm.ecg_alerte_j7))
    else:
        fail("POST BilanInitial", "Bilan non créé en DB")

    # POST ExamenLabo avec 4 nouveaux champs DST
    with app.app_context():
        labo_uid = User.query.first().id
    resp3 = client.post('/labo/saisir', data={
        'patient_id': str(pfm_id),
        'mois_suivi': '7',
        'date_prelevement': '2026-05-23',
        'dst_effectue': 'y',
        'dst_amikacine': 'resistant',
        'dst_kanamycine': 'sensible',
        'dst_capreomycine': 'intermediaire',
        'dst_ofloxacine': 'resistant',
        'culture_resultat': 'positif',
    }, follow_redirects=True)

    with app.app_context():
        efm = ExamenLabo.query.filter_by(patient_id=pfm_id, mois_suivi=7).first()
    if efm:
        for field, expected in [
            ('dst_amikacine', 'resistant'),
            ('dst_kanamycine', 'sensible'),
            ('dst_capreomycine', 'intermediaire'),
            ('dst_ofloxacine', 'resistant'),
        ]:
            if getattr(efm, field) == expected:
                ok(f"POST ExamenLabo : {field}={expected}")
            else:
                fail(f"POST ExamenLabo : {field}", f"attendu={expected}, obtenu={getattr(efm, field)}")
    else:
        fail("POST ExamenLabo", "Examen non créé en DB")

    with app.app_context():
        db.session.delete(db.session.get(Patient, pfm_id))
        db.session.commit()

# ─────────────────────────────────────────────────────────────
section("16. MIGRATION — idempotente (run 2x sans erreur)")
# ─────────────────────────────────────────────────────────────
result = subprocess.run(
    [sys.executable, 'migrate_v03_to_v04.py'],
    capture_output=True, text=True
)
if 'Migration réussie' in result.stdout and '0 erreur' in result.stdout:
    ok("Migration 2e exécution : 0 erreur")
else:
    fail("Migration 2e exécution", result.stdout[-300:])

# Vérifier que 0 colonnes ont été ajoutées (toutes déjà présentes)
if 'ajoutée(s)' in result.stdout:
    import re
    m = re.search(r'(\d+) ajoutée', result.stdout)
    added = int(m.group(1)) if m else -1
    if added == 0:
        ok("Migration idempotente : 0 colonne ajoutée au 2e run")
    else:
        fail("Migration idempotente", f"{added} colonnes ajoutées au 2e run (attendu 0)")

# ─────────────────────────────────────────────────────────────
section("17. COLONNES DB — vérification directe SQLite")
# ─────────────────────────────────────────────────────────────
conn = sqlite3.connect('instance/tbtrack.db')
cur = conn.cursor()

all_expected = {
    'bilans_initiaux': ['test_grossesse', 'rx_thorax_normale', 'lpa_1ere_ligne',
                        'lpa_2eme_ligne', 'leucocytes_g_l', 'plaquettes_g_l',
                        'ecg_j7_qt_ms', 'tsh_miu_l'],
    'examens_labo':    ['dst_amikacine', 'dst_kanamycine',
                        'dst_capreomycine', 'dst_ofloxacine'],
    'suivi_ponderal':  ['kaliemie_mmol_l', 'creatinine_umol_l',
                        'gpt_u_l', 'got_u_l', 'leucocytes_g_l', 'plaquettes_g_l'],
}
for table, cols in all_expected.items():
    cur.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cur.fetchall()}
    for col in cols:
        if col in existing:
            ok(f"DB {table}.{col} ✓")
        else:
            fail(f"DB {table}.{col} MANQUANT")
conn.close()

# ─────────────────────────────────────────────────────────────
section("18. RAPPORT ANNUEL — catégories PNLT dans le rendu HTML")
# ─────────────────────────────────────────────────────────────
with app.test_client() as client:
    with app.app_context():
        uid18, _ = get_or_create_test_user()
        import datetime as _dt
        # Nettoyer les éventuels résidus de tests précédents
        Patient.query.filter(Patient.code_patient.like('TCAT-%')).delete(synchronize_session=False)
        db.session.commit()
        # Créer un patient par catégorie pour que chaque label apparaisse dans le rendu
        test_pats_cat = []
        for i, cat in enumerate(['echec_tbmr', 'reprise_tbmr', 'rechute_tbmr', 'rechute_retrait']):
            tp = Patient(
                code_patient=f'TCAT-{i+1:02d}', nom='TESTCAT',
                prenom='V04', statut='en_cours', statut_vih='inconnu',
                categorie=cat,
                date_diagnostic=_dt.date(_dt.date.today().year, 1, 1),
            )
            db.session.add(tp)
            test_pats_cat.append(tp)
        db.session.commit()
        cat_ids = [tp.id for tp in test_pats_cat]

    login_test_client(client, uid18)
    r = client.get('/rapports/annuel', follow_redirects=True)
    body = r.data.decode('utf-8', errors='replace')
    for label in ['E4', 'RT4', 'R4', 'R2']:
        if label in body:
            ok(f"Rapport annuel : catégorie '{label}' visible")
        else:
            fail(f"Rapport annuel : catégorie '{label}' absente")

    with app.app_context():
        for cid in cat_ids:
            obj = db.session.get(Patient, cid)
            if obj:
                db.session.delete(obj)
        db.session.commit()

# ─────────────────────────────────────────────────────────────
section("19. CALCULATEUR — template CI badge rendu")
# ─────────────────────────────────────────────────────────────
with app.test_client() as client:
    with app.app_context():
        uid19, _ = get_or_create_test_user()
    login_test_client(client, uid19)

    # Calculer doses enfant 5.5 kg schéma long_enfant → Delamanide doit afficher CI
    r = client.post('/dosage/', data={
        'poids': '5.5', 'groupe_age': 'enfant', 'schema': 'long_enfant'
    }, follow_redirects=True)
    body = r.data.decode('utf-8', errors='replace')
    if 'fa-ban' in body and 'CI' in body:
        ok("Calculateur : badge CI (fa-ban) affiché pour Delamanide 5.5kg")
    else:
        fail("Calculateur : badge CI absent pour Delamanide 5.5kg")

# ─────────────────────────────────────────────────────────────
section("20. MODÈLES — pas de référence cassée dans __init__.py")
# ─────────────────────────────────────────────────────────────
with app.app_context():
    from app import models
    expected_models = ['Patient', 'BilanInitial', 'ExamenLabo', 'SuiviPonderal',
                       'NoteClinique', 'Traitement', 'EffetSecondaire', 'Contact',
                       'SuiviDOT', 'Medicament', 'MouvementStock']
    for m in expected_models:
        if hasattr(models, m):
            ok(f"models.{m} accessible")
        else:
            fail(f"models.{m} manquant dans __init__.py")

# Cleanup : supprimer l'utilisateur de test créé pour les sessions
with app.app_context():
    tu = User.query.filter_by(email='v04test@tbtrack.mg').first()
    if tu:
        db.session.delete(tu)
        db.session.commit()

# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*62}")
print(f"  RÉSULTAT FINAL V0.4 : {OK} OK  |  {FAIL} ÉCHEC(S)")
print(f"{'='*62}")
if FAIL == 0:
    print("  V0.4 VALIDÉE — Prête pour le déploiement.")
    sys.exit(0)
else:
    print(f"  BLOQUANT : {FAIL} test(s) en échec. NE PAS déployer.")
    sys.exit(1)
