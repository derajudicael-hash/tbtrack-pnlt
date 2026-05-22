"""
Tables de dosage extraites du Guide TBMR-PNLT 2021 (Madagascar).
Tableaux II et III du guide.
"""

# ── Schémas thérapeutiques ────────────────────────────────────────────────────
SCHEMAS = {
    'court_nouveau': {
        'label': 'Schéma court — Nouveau cas TB-MR/RR',
        'duree': '9 à 11 mois',
        'phases': [
            {'phase': 'Intensive (4 mois)', 'medicaments': ['Bdq', 'Mfx', 'Cfz', 'Pto', 'H', 'Z', 'E']},
            {'phase': 'Continuation 1 (2 mois)', 'medicaments': ['Bdq', 'Mfx', 'Cfz', 'Z', 'E']},
            {'phase': 'Continuation 2 (3 mois)', 'medicaments': ['Mfx', 'Cfz', 'Z', 'E']},
        ],
        'note': 'Bdq donnée pendant les 6 premiers mois. Lzd peut remplacer Bdq si intolérance.',
    },
    'long_adulte': {
        'label': 'Schéma long — Adulte (non éligible au schéma court)',
        'duree': '18 mois',
        'phases': [
            {'phase': 'Intensive (6 mois)', 'medicaments': ['Bdq', 'Lzd', 'Lfx', 'Cfz', 'Cs']},
            {'phase': 'Continuation (12 mois)', 'medicaments': ['Lfx', 'Cfz', 'Cs']},
        ],
        'note': 'Bdq et Lzd données pendant les 6 premiers mois.',
    },
    'long_enfant': {
        'label': 'Schéma long — Enfant (non éligible au schéma court)',
        'duree': '18 mois',
        'phases': [
            {'phase': 'Intensive (6 mois)', 'medicaments': ['Dlm', 'Lzd', 'Lfx', 'Cfz', 'Cs']},
            {'phase': 'Continuation (12 mois)', 'medicaments': ['Lfx', 'Cfz', 'Cs']},
        ],
        'note': 'Dlm et Lzd données pendant les 6 premiers mois. Durée totale selon avis pédiatre.',
    },
    'pre_xdr_xdr': {
        'label': 'Schéma Pré-XDR et XDR-TB',
        'duree': '18 mois',
        'phases': [
            {'phase': 'Phase 1 (6 mois)', 'medicaments': ['Bdq', 'Lzd', 'Cfz', 'Cs', 'Dlm', 'Z']},
            {'phase': 'Phase 2 (12 mois)', 'medicaments': ['Bdq', 'Cfz', 'Cs', 'Z']},
        ],
        'note': 'Schéma adapté selon antibiogramme et avis des experts.',
    },
}

# ── Tranches de poids adulte (≥15 ans, ≥30 kg) ───────────────────────────────
TRANCHES_ADULTE = ['30–35 kg', '36–45 kg', '46–55 kg', '56–70 kg', '≥71 kg']
LIMITES_ADULTE = [(30, 35), (36, 45), (46, 55), (56, 70), (71, 999)]

DOSES_ADULTE = {
    'Isoniazide':         {'forme': 'cp 300 mg',  'doses': [1.5, 1.5, 2, 2, 2],        'unite': 'cp'},
    'Pyrazinamide':       {'forme': 'cp 400 mg',  'doses': [3, 4, 4, 4, 5],            'unite': 'cp'},
    'Ethambutol':         {'forme': 'cp 400 mg',  'doses': [2, 2, 3, 3, 3],            'unite': 'cp'},
    'Levofloxacine':      {'forme': 'cp 250 mg',  'doses': [3, 3, 4, 4, 4],            'unite': 'cp'},
    'Moxifloxacine (std)':{'forme': 'cp 400 mg',  'doses': [1, 1, 1, 1, 1],            'unite': 'cp'},
    'Moxifloxacine (élevée)':{'forme': 'cp 400 mg','doses': [1, 1.5, 2, 2, 2],        'unite': 'cp'},
    'Prothionamide':      {'forme': 'cp 250 mg',  'doses': [2, 2, 3, 3, 4],            'unite': 'cp'},
    'Cycloserine':        {'forme': 'gél 250 mg', 'doses': [2, 3, 3, 3, 3],            'unite': 'gél'},
    'Linezolide':         {'forme': 'cp 600 mg',  'doses': [0.5, 0.75, 1, 1, 1],       'unite': 'cp'},
    'PAS':                {'forme': 'sachet 4 g', 'doses': ['1 sachet ×2/j'] * 5,      'unite': ''},
    'Bedaquiline':        {'forme': 'cp 100 mg',  'doses': ['4cp/j×2sem puis 2cp×3/sem×22sem'] * 5, 'unite': ''},
    'Delamanide':         {'forme': 'cp 50 mg',   'doses': ['2 cp ×2/j (200 mg/j)'] * 5, 'unite': ''},
    'Clofazimine':        {'forme': 'gél 100 mg', 'doses': ['1 gél/j'] * 5,             'unite': ''},
}

# ── Tranches de poids enfant (<15 ans, <30 kg) ───────────────────────────────
TRANCHES_ENFANT = ['5–6 kg', '7–9 kg', '10–15 kg', '16–23 kg', '24–30 kg']
LIMITES_ENFANT = [(5, 6), (7, 9), (10, 15), (16, 23), (24, 30)]

DOSES_ENFANT = {
    'Isoniazide':    {'forme': 'cp 100 mg',   'doses': [1, 1.5, 2, 3, 4],                     'unite': 'cp'},
    'Pyrazinamide':  {'forme': 'cp 400 mg',   'doses': [0.5, 0.75, 1, 2, 2.5],                'unite': 'cp'},
    'Ethambutol':    {'forme': 'cp 400 mg / susp', 'doses': ['3 mL', '4 mL', '6 mL', '1 cp', '1.5 cp'], 'unite': ''},
    'Levofloxacine': {'forme': 'cp 250 mg',   'doses': [0.5, 0.5, 1, 2, 3],                   'unite': 'cp'},
    'Moxifloxacine': {'forme': 'cp 400 mg / susp','doses': ['2 mL', '3 mL', '5 mL', '7 mL', '1 cp'], 'unite': ''},
    'Prothionamide': {'forme': 'cp 250 mg',   'doses': [0.5, 0.5, 1, 2, 2],                   'unite': 'cp'},
    'Cycloserine':   {'forme': 'gél 125 mg',  'doses': [1, 1, 2, 3, 4],                       'unite': 'gél'},
    'Linezolide':    {'forme': 'sp 20 mg/mL', 'doses': ['4 mL', '6 mL', '8 mL', '11 mL', '14 mL'], 'unite': ''},
    'PAS':           {'forme': 'sachet 4 g',  'doses': ['0.75 g×2', '1 g×2', '2 g×2', '3 g×2', '3.5 g×2'], 'unite': ''},
    'Clofazimine':   {'forme': 'gél 50 mg',   'doses': ['1/2j', '1/2j', '1/j', '2/j', '2/j'], 'unite': ''},
    'Delamanide':    {'forme': 'cp 50 mg',    'doses': ['0.5×2', '0.5×2', '1×2', '1×2', '1×2'], 'unite': ''},
    'Bedaquiline':   {'forme': 'cp 100 mg',   'doses': ['Voir protocole pédiatrique'] * 5,     'unite': ''},
}


def get_tranche_index(poids: float, adulte: bool) -> int:
    limites = LIMITES_ADULTE if adulte else LIMITES_ENFANT
    for i, (low, high) in enumerate(limites):
        if low <= poids <= high:
            return i
    return len(limites) - 1


def calculer_doses(poids: float, adulte: bool, schema: str) -> dict:
    idx = get_tranche_index(poids, adulte)
    table = DOSES_ADULTE if adulte else DOSES_ENFANT
    tranches = TRANCHES_ADULTE if adulte else TRANCHES_ENFANT
    tranche = tranches[idx]

    schema_info = SCHEMAS.get(schema, {})
    tous_medicaments = set()
    for phase in schema_info.get('phases', []):
        tous_medicaments.update(phase.get('medicaments', []))

    ABR_TO_NOM = {
        'Bdq': 'Bedaquiline', 'Mfx': 'Moxifloxacine (std)', 'Cfz': 'Clofazimine',
        'Pto': 'Prothionamide', 'H': 'Isoniazide', 'Z': 'Pyrazinamide', 'E': 'Ethambutol',
        'Lzd': 'Linezolide', 'Lfx': 'Levofloxacine', 'Cs': 'Cycloserine',
        'Dlm': 'Delamanide', 'PAS': 'PAS',
    }

    resultats = []
    for abr in sorted(tous_medicaments):
        nom = ABR_TO_NOM.get(abr, abr)
        info = table.get(nom)
        if info:
            dose = info['doses'][idx]
            resultats.append({
                'abreviation': abr,
                'nom': nom,
                'forme': info['forme'],
                'dose': dose,
                'unite': info['unite'],
            })

    return {
        'poids': poids,
        'tranche': tranche,
        'adulte': adulte,
        'schema': schema_info,
        'medicaments': resultats,
    }
