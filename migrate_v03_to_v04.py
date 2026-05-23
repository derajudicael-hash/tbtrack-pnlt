"""
Migration V0.3 → V0.4 — Corrections PNLT Guide 2021
Ajoute les colonnes manquantes identifiées lors de l'audit clinique.
Exécuter UNE SEULE FOIS sur la base de données existante.
Usage : python migrate_v03_to_v04.py
"""
import sqlite3
import os
import sys

DB_PATH = os.environ.get('DATABASE_URL', 'tbtrack.db')
if DB_PATH.startswith('sqlite:///'):
    DB_PATH = DB_PATH[len('sqlite:///'):]

if not os.path.exists(DB_PATH):
    # Chercher dans le dossier instance
    candidate = os.path.join('instance', 'tbtrack.db')
    if os.path.exists(candidate):
        DB_PATH = candidate
    else:
        print(f"[ERREUR] Base de données introuvable : {DB_PATH}")
        print("Spécifiez le chemin : DATABASE_URL=sqlite:///chemin/vers/tbtrack.db python migrate_v03_to_v04.py")
        sys.exit(1)

print(f"[INFO] Base : {DB_PATH}")

# Colonnes à ajouter : (table, colonne, type_sql)
MIGRATIONS = [
    # bilans_initiaux — examens M0 obligatoires
    ('bilans_initiaux', 'test_grossesse',    'BOOLEAN'),
    ('bilans_initiaux', 'rx_thorax_normale', 'BOOLEAN'),
    ('bilans_initiaux', 'lpa_1ere_ligne',    'VARCHAR(200)'),
    ('bilans_initiaux', 'lpa_2eme_ligne',    'VARCHAR(200)'),
    # bilans_initiaux — NFS complète
    ('bilans_initiaux', 'leucocytes_g_l',    'FLOAT'),
    ('bilans_initiaux', 'plaquettes_g_l',    'FLOAT'),
    # bilans_initiaux — ECG J7 + TSH numérique
    ('bilans_initiaux', 'ecg_j7_qt_ms',      'INTEGER'),
    ('bilans_initiaux', 'tsh_miu_l',         'FLOAT'),
    # examens_labo — DST aminoglycosides + ofloxacine (classification XDR)
    ('examens_labo', 'dst_amikacine',        'VARCHAR(20)'),
    ('examens_labo', 'dst_kanamycine',       'VARCHAR(20)'),
    ('examens_labo', 'dst_capreomycine',     'VARCHAR(20)'),
    ('examens_labo', 'dst_ofloxacine',       'VARCHAR(20)'),
    # suivi_ponderal — bilan biologique mensuel
    ('suivi_ponderal', 'kaliemie_mmol_l',    'FLOAT'),
    ('suivi_ponderal', 'creatinine_umol_l',  'FLOAT'),
    ('suivi_ponderal', 'gpt_u_l',            'FLOAT'),
    ('suivi_ponderal', 'got_u_l',            'FLOAT'),
    ('suivi_ponderal', 'leucocytes_g_l',     'FLOAT'),
    ('suivi_ponderal', 'plaquettes_g_l',     'FLOAT'),
]

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Créer suivi_ponderal si elle n'existe pas (nouvelle table V0.4)
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='suivi_ponderal'")
if not cur.fetchone():
    cur.execute("""
        CREATE TABLE suivi_ponderal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL REFERENCES patients(id),
            mois_suivi INTEGER NOT NULL,
            date_mesure DATE NOT NULL,
            poids FLOAT,
            taille FLOAT,
            tension_sys INTEGER,
            tension_dia INTEGER,
            temperature FLOAT,
            kaliemie_mmol_l FLOAT,
            creatinine_umol_l FLOAT,
            gpt_u_l FLOAT,
            got_u_l FLOAT,
            leucocytes_g_l FLOAT,
            plaquettes_g_l FLOAT,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  [OK]    Table suivi_ponderal créée")
else:
    print("  [SKIP]  Table suivi_ponderal — déjà présente")

ok = 0
skip = 0
err = 0

for table, col, col_type in MIGRATIONS:
    # Vérifier si la colonne existe déjà
    cur.execute(f"PRAGMA table_info({table})")
    existing = [row[1] for row in cur.fetchall()]
    if col in existing:
        print(f"  [SKIP]  {table}.{col} — déjà présente")
        skip += 1
        continue
    try:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
        print(f"  [OK]    {table}.{col} ({col_type}) ajoutée")
        ok += 1
    except Exception as e:
        print(f"  [ERREUR] {table}.{col} : {e}")
        err += 1

conn.commit()
conn.close()

print(f"\nRésultat : {ok} ajoutée(s), {skip} ignorée(s), {err} erreur(s)")
if err == 0:
    print("Migration réussie.")
else:
    print("Des erreurs sont survenues — vérifier les messages ci-dessus.")
