"""
Tests ciblés sur les corrections cliniques — guide PNLT 2021
Vérifie chaque logique métier corrigée, une à une.
Usage : python test_corrections_cliniques.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

ok_count = 0
fail_count = 0

def ok(msg):
    global ok_count
    ok_count += 1
    print(f"  OK   {msg}")

def fail(msg, detail=""):
    global fail_count
    fail_count += 1
    d = f" — {detail}" if detail else ""
    print(f"  FAIL {msg}{d}")


print("\n" + "="*60)
print("  TEST 1 — Calculateur DOSES_ENFANT : Delamanide 5-6 kg")
print("="*60)
from app.blueprints.dosage.calculateur import DOSES_ENFANT, DOSES_ADULTE, SCHEMAS, calculer_doses

# Vérifier que 5-6 kg = CI
dlm_doses = DOSES_ENFANT['Delamanide']['doses']
if dlm_doses[0] == 'CI (<7 kg)':
    ok("Delamanide 5-6 kg → 'CI (<7 kg)'")
else:
    fail("Delamanide 5-6 kg devrait être CI", f"Valeur: {dlm_doses[0]}")

# Vérifier que 7-9 kg = dose normale
if dlm_doses[1] == '0.5 cp ×2/j':
    ok("Delamanide 7-9 kg → dose correcte '0.5 cp ×2/j'")
else:
    fail("Delamanide 7-9 kg mauvaise dose", f"Valeur: {dlm_doses[1]}")

# Tranches 10+ kg normales
for i, (tranche_label, expected_start) in enumerate([
    ('10-15 kg', '1 cp'), ('16-23 kg', '1 cp'), ('24-30 kg', '1 cp')
], start=2):
    if str(dlm_doses[i]).startswith('1 cp'):
        ok(f"Delamanide {tranche_label} → dose normale")
    else:
        fail(f"Delamanide {tranche_label} dose incorrecte", f"Valeur: {dlm_doses[i]}")


print("\n" + "="*60)
print("  TEST 2 — Calculateur DOSES_ENFANT : Clofazimine notation")
print("="*60)
cfz_doses = DOSES_ENFANT['Clofazimine']['doses']
# 5-6 kg et 7-9 kg doivent indiquer "1 gél / 2 jours" sans ambiguïté
if cfz_doses[0] == '1 gél / 2 jours':
    ok("Clofazimine 5-6 kg → '1 gél / 2 jours' (sans ambiguïté)")
else:
    fail("Clofazimine 5-6 kg notation ambiguë", f"Valeur: {cfz_doses[0]}")

if cfz_doses[1] == '1 gél / 2 jours':
    ok("Clofazimine 7-9 kg → '1 gél / 2 jours' (sans ambiguïté)")
else:
    fail("Clofazimine 7-9 kg notation ambiguë", f"Valeur: {cfz_doses[1]}")

# Tester que '1/2j' n'existe plus nulle part
for tranche_label, dose in zip(['5-6', '7-9', '10-15', '16-23', '24-30'], cfz_doses):
    if '1/2j' in str(dose):
        fail(f"Clofazimine {tranche_label} kg contient encore '1/2j'", str(dose))
    else:
        ok(f"Clofazimine {tranche_label} kg : notation '1/2j' absente")


print("\n" + "="*60)
print("  TEST 3 — Calculateur DOSES_ENFANT : Bedaquiline CI")
print("="*60)
bdq_doses = DOSES_ENFANT['Bedaquiline']['doses']
# 5-6 kg (<5 ans / <15 kg) et 7-9 kg : CI
for i, (tranche_label, expected_ci) in enumerate([('5-6 kg', True), ('7-9 kg', True)]):
    if str(bdq_doses[i]).startswith('CI'):
        ok(f"Bedaquiline {tranche_label} → CI marqué")
    else:
        fail(f"Bedaquiline {tranche_label} → CI absent", f"Valeur: {bdq_doses[i]}")

# 10-15 kg et plus : mention protocole
for i, tranche_label in enumerate(['10-15 kg', '16-23 kg', '24-30 kg'], start=2):
    if 'protocole' in str(bdq_doses[i]).lower():
        ok(f"Bedaquiline {tranche_label} → mention protocole")
    else:
        fail(f"Bedaquiline {tranche_label} valeur inattendue", f"Valeur: {bdq_doses[i]}")


print("\n" + "="*60)
print("  TEST 4 — Calculateur SCHEMAS : Hr-TB présent")
print("="*60)
if 'hr_tb' in SCHEMAS:
    ok("Schéma Hr-TB présent dans SCHEMAS")
    s = SCHEMAS['hr_tb']
    ok(f"Hr-TB : durée '{s['duree']}'")
    meds = set()
    for ph in s['phases']:
        meds.update(ph['medicaments'])
    for m in ['H', 'Lfx', 'E', 'Z']:
        if m in meds:
            ok(f"Hr-TB contient {m}")
        else:
            fail(f"Hr-TB ne contient pas {m}")
else:
    fail("Schéma Hr-TB absent de SCHEMAS")


print("\n" + "="*60)
print("  TEST 5 — Calculateur : Hr-TB calcul doses adulte/enfant")
print("="*60)
# Adulte 50 kg
r_adulte = calculer_doses(50.0, adulte=True, schema='hr_tb')
noms = [m['nom'] for m in r_adulte['medicaments']]
for expected in ['Isoniazide', 'Levofloxacine', 'Ethambutol', 'Pyrazinamide']:
    if expected in noms:
        ok(f"Hr-TB adulte 50 kg : {expected} présent")
    else:
        fail(f"Hr-TB adulte 50 kg : {expected} absent", f"Noms: {noms}")

# Enfant 12 kg
r_enfant = calculer_doses(12.0, adulte=False, schema='hr_tb')
noms_e = [m['nom'] for m in r_enfant['medicaments']]
for expected in ['Isoniazide', 'Levofloxacine', 'Ethambutol', 'Pyrazinamide']:
    if expected in noms_e:
        ok(f"Hr-TB enfant 12 kg : {expected} présent")
    else:
        fail(f"Hr-TB enfant 12 kg : {expected} absent", f"Noms: {noms_e}")


print("\n" + "="*60)
print("  TEST 6 — BilanInitial : ecg_alerte deux seuils")
print("="*60)
# Simuler sans passer par la DB — on crée l'objet directement
from app.models.bilan_initial import BilanInitial

b_normal = BilanInitial(); b_normal.ecg_qt_ms = 420
if b_normal.ecg_alerte is None:
    ok("ECG QTc=420ms → None (normal, < 450ms)")
else:
    fail("ECG QTc=420ms devrait être None", str(b_normal.ecg_alerte))

b_surv = BilanInitial(); b_surv.ecg_qt_ms = 470
if b_surv.ecg_alerte == 'surveillance':
    ok("ECG QTc=470ms → 'surveillance' (450–499ms)")
else:
    fail("ECG QTc=470ms devrait être 'surveillance'", str(b_surv.ecg_alerte))

b_limite_bas = BilanInitial(); b_limite_bas.ecg_qt_ms = 451
if b_limite_bas.ecg_alerte == 'surveillance':
    ok("ECG QTc=451ms → 'surveillance' (juste au-dessus du seuil 450)")
else:
    fail("ECG QTc=451ms devrait être 'surveillance'", str(b_limite_bas.ecg_alerte))

b_limite_haut = BilanInitial(); b_limite_haut.ecg_qt_ms = 499
if b_limite_haut.ecg_alerte == 'surveillance':
    ok("ECG QTc=499ms → 'surveillance' (juste en-dessous de 500)")
else:
    fail("ECG QTc=499ms devrait être 'surveillance'", str(b_limite_haut.ecg_alerte))

b_stop = BilanInitial(); b_stop.ecg_qt_ms = 500
if b_stop.ecg_alerte == 'stop':
    ok("ECG QTc=500ms → 'stop' (seuil exact ARRÊT selon guide p.27)")
else:
    fail("ECG QTc=500ms devrait être 'stop'", str(b_stop.ecg_alerte))

b_stop2 = BilanInitial(); b_stop2.ecg_qt_ms = 520
if b_stop2.ecg_alerte == 'stop':
    ok("ECG QTc=520ms → 'stop' (ARRÊT médicaments)")
else:
    fail("ECG QTc=520ms devrait être 'stop'", str(b_stop2.ecg_alerte))

b_none = BilanInitial(); b_none.ecg_qt_ms = None
if b_none.ecg_alerte is None:
    ok("ECG QTc=None → None (pas d'alerte si non renseigné)")
else:
    fail("ECG QTc=None devrait être None", str(b_none.ecg_alerte))

# TSH
b_tsh_ok = BilanInitial(); b_tsh_ok.tsh_miu_l = 3.0
if not b_tsh_ok.tsh_alerte:
    ok("TSH 3.0 mIU/L → pas d'alerte (< 6.75)")
else:
    fail("TSH 3.0 ne devrait pas déclencher alerte")

b_tsh_haut = BilanInitial(); b_tsh_haut.tsh_miu_l = 7.5
if b_tsh_haut.tsh_alerte:
    ok("TSH 7.5 mIU/L → alerte (> 1.5× norme haute = 6.75)")
else:
    fail("TSH 7.5 devrait déclencher alerte")


print("\n" + "="*60)
print("  TEST 7 — ExamenLabo : 12 champs DST présents dans dst_summary")
print("="*60)
from app.models.examen_labo import ExamenLabo

e = ExamenLabo()
e.dst_isoniazide = 'resistant'
e.dst_rifampicine = 'resistant'
e.dst_ethambutol = 'sensible'
e.dst_pyrazinamide = 'sensible'
e.dst_levofloxacine = 'sensible'
e.dst_moxifloxacine = 'sensible'
e.dst_bedaquiline = 'sensible'
e.dst_linezolide = 'sensible'
e.dst_amikacine = 'resistant'
e.dst_kanamycine = 'resistant'
e.dst_capreomycine = 'sensible'
e.dst_ofloxacine = 'resistant'

summary = e.dst_summary()
expected_keys = [
    'H (Isoniazide)', 'R (Rifampicine)', 'E (Ethambutol)', 'Z (Pyrazinamide)',
    'Lfx', 'Mfx', 'Bdq', 'Lzd',
    'Am (Amikacine)', 'Km (Kanamycine)', 'Cm (Capréomycine)', 'Ofx (Ofloxacine)',
]
for k in expected_keys:
    if k in summary:
        ok(f"DST : '{k}' présent dans dst_summary()")
    else:
        fail(f"DST : '{k}' absent de dst_summary()")


print("\n" + "="*60)
print("  TEST 8 — PatientForm : catégories PNLT complètes")
print("="*60)
from app import create_app
app = create_app()
with app.app_context():
    from app.blueprints.patients.forms import PatientForm
    with app.test_request_context('/'):
        form = PatientForm()
        cat_values = [c[0] for c in form.categorie.choices]

    expected_categories = [
        'nouveau_cas', 'echec_primo', 'echec_retrait', 'reprise',
        'rechute_primo', 'rechute_retrait', 'transfert',
        'echec_tbmr', 'reprise_tbmr', 'rechute_tbmr', 'autres'
    ]
    for cat in expected_categories:
        if cat in cat_values:
            ok(f"Catégorie '{cat}' présente")
        else:
            fail(f"Catégorie '{cat}' MANQUANTE")

    if len(cat_values) == 11:
        ok(f"Nombre de catégories = 11 (PNLT complet)")
    else:
        fail(f"Nombre de catégories = {len(cat_values)} (attendu 11)")


print("\n" + "="*60)
print("  TEST 9 — SuiviPonderalForm : champs biologiques présents")
print("="*60)
with app.app_context():
    from app.blueprints.patients.forms import SuiviPonderalForm
    with app.test_request_context('/'):
        f = SuiviPonderalForm()
        expected_fields = [
            'kaliemie_mmol_l', 'creatinine_umol_l', 'gpt_u_l',
            'got_u_l', 'leucocytes_g_l', 'plaquettes_g_l'
        ]
        for field in expected_fields:
            if hasattr(f, field):
                ok(f"SuiviPonderalForm : champ '{field}' présent")
            else:
                fail(f"SuiviPonderalForm : champ '{field}' MANQUANT")


print("\n" + "="*60)
print("  TEST 10 — BilanInitialForm : champs M0 obligatoires présents")
print("="*60)
with app.app_context():
    from app.blueprints.traitement.forms import BilanInitialForm
    with app.test_request_context('/'):
        bf = BilanInitialForm()
        expected_fields = [
            'test_grossesse', 'rx_thorax_normale', 'lpa_1ere_ligne',
            'lpa_2eme_ligne', 'tsh_miu_l', 'ecg_j7_qt_ms',
            'leucocytes_g_l', 'plaquettes_g_l'
        ]
        for field in expected_fields:
            if hasattr(bf, field):
                ok(f"BilanInitialForm : champ '{field}' présent")
            else:
                fail(f"BilanInitialForm : champ '{field}' MANQUANT")


print("\n" + "="*60)
print("  TEST 11 — Streptomycine dans MEDICAMENTS_TBMR")
print("="*60)
from app.blueprints.traitement.forms import MEDICAMENTS_TBMR, GROUPES_MEDICAMENTS
if any('Streptomycine' in m for m in MEDICAMENTS_TBMR):
    ok("Streptomycine (S) présente dans MEDICAMENTS_TBMR")
else:
    fail("Streptomycine absente de MEDICAMENTS_TBMR")

if any('Streptomycine' in m for m in GROUPES_MEDICAMENTS.get('Groupe C — Complémentaires', [])):
    ok("Streptomycine dans Groupe C")
else:
    fail("Streptomycine absente du Groupe C")


print("\n" + "="*60)
print("  TEST 12 — Rapport annuel : toutes catégories PNLT")
print("="*60)
# Vérifier que _build_annuel contient les nouvelles catégories dans son dict
import inspect
from app.blueprints.rapports.routes import _build_annuel
src = inspect.getsource(_build_annuel)
for cat in ['echec_tbmr', 'reprise_tbmr', 'rechute_tbmr', 'rechute_retrait', 'autres']:
    if cat in src:
        ok(f"Rapport annuel : catégorie '{cat}' couverte")
    else:
        fail(f"Rapport annuel : catégorie '{cat}' MANQUANTE")


print("\n" + "="*60)
print("  TEST 13 — Modèles DB : nouvelles colonnes présentes")
print("="*60)
from app.models.bilan_initial import BilanInitial
from app.models.examen_labo import ExamenLabo
from app.models.suivi_ponderal import SuiviPonderal

for field in ['test_grossesse', 'rx_thorax_normale', 'lpa_1ere_ligne', 'lpa_2eme_ligne',
              'tsh_miu_l', 'ecg_j7_qt_ms', 'leucocytes_g_l', 'plaquettes_g_l']:
    if hasattr(BilanInitial, field):
        ok(f"BilanInitial.{field} présent")
    else:
        fail(f"BilanInitial.{field} MANQUANT")

for field in ['dst_amikacine', 'dst_kanamycine', 'dst_capreomycine', 'dst_ofloxacine']:
    if hasattr(ExamenLabo, field):
        ok(f"ExamenLabo.{field} présent")
    else:
        fail(f"ExamenLabo.{field} MANQUANT")

for field in ['kaliemie_mmol_l', 'creatinine_umol_l', 'gpt_u_l', 'got_u_l',
              'leucocytes_g_l', 'plaquettes_g_l']:
    if hasattr(SuiviPonderal, field):
        ok(f"SuiviPonderal.{field} présent")
    else:
        fail(f"SuiviPonderal.{field} MANQUANT")


print("\n" + "="*60)
print("  TEST 14 — DB : nouvelles colonnes dans SQLite")
print("="*60)
import sqlite3
DB_PATH = os.path.join('instance', 'tbtrack.db')
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

def check_col(table, col):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    if col in cols:
        ok(f"DB : {table}.{col} présent")
    else:
        fail(f"DB : {table}.{col} MANQUANT")

for col in ['test_grossesse', 'rx_thorax_normale', 'lpa_1ere_ligne', 'lpa_2eme_ligne',
            'tsh_miu_l', 'ecg_j7_qt_ms', 'leucocytes_g_l', 'plaquettes_g_l']:
    check_col('bilans_initiaux', col)

for col in ['dst_amikacine', 'dst_kanamycine', 'dst_capreomycine', 'dst_ofloxacine']:
    check_col('examens_labo', col)

for col in ['kaliemie_mmol_l', 'creatinine_umol_l', 'gpt_u_l', 'got_u_l',
            'leucocytes_g_l', 'plaquettes_g_l']:
    check_col('suivi_ponderal', col)

conn.close()


# ══════════════════════════════════════════════
print("\n" + "="*60)
print(f"  RÉSULTAT : {ok_count} OK  |  {fail_count} ÉCHEC(S)")
print("="*60)
if fail_count == 0:
    print("  Toutes les corrections cliniques sont validées.")
else:
    print(f"  ATTENTION : {fail_count} test(s) en échec — à corriger avant production.")
    sys.exit(1)
