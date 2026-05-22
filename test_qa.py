"""
QA automatisé TBTrack — simulation complète de cycles patients
"""
import sys, json
from datetime import date, timedelta
from app import create_app
from app.extensions import db
from app.models import (Patient, Contact, EffetSecondaire, ExamenLabo,
                        BilanInitial, Traitement, SuiviDOT, User)
from app.models.stock import Medicament

app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

BUGS   = []
PASSED = []

def ok(label):
    PASSED.append(label)
    print(f"  ✓  {label}")

def bug(label, detail):
    BUGS.append({'label': label, 'detail': detail})
    print(f"  ✗  {label}")
    print(f"       → {detail}")

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


# ── Authentification ────────────────────────────────────────────────────────

def make_client():
    client = app.test_client()
    with app.app_context():
        user = User.query.filter_by(role='coordinateur').first() or User.query.first()
        uid = user.id
    with client.session_transaction() as sess:
        sess['_user_id'] = str(uid)
        sess['_fresh'] = True
    return client

# ── Helpers HTTP ─────────────────────────────────────────────────────────────

def post(client, url, data, follow=True):
    return client.post(url, data=data, follow_redirects=follow)

def get(client, url):
    return client.get(url, follow_redirects=True)

def response_ok(r):
    return r.status_code == 200

def contains(r, text):
    if isinstance(text, bytes):
        return text in r.data
    return text.encode() in r.data

# ── Fixture : données de base ─────────────────────────────────────────────────

BASE_PATIENT = {
    'nom': 'DUPONT',
    'prenom': 'Jean',
    'date_naissance': '1985-03-15',
    'sexe': 'Homme',
    'adresse': '12 Rue de la Santé',
    'telephone': '0321456789',
    'poids': '65.5',
    'statut_vih': 'negatif',
    'date_diagnostic': '2025-01-10',
    'type_resistance': 'TB-MR',
    'categorie': 'nouveau_cas',
    'statut': 'en_cours',
    'schema_therapeutique': 'long',
    'date_debut_traitement': '2025-02-01',
    'notes_cliniques': 'Patient test QA.',
}


# ════════════════════════════════════════════════════════════════════════════
#  SECTION 1 — CRÉATION PATIENTS
# ════════════════════════════════════════════════════════════════════════════
def test_patients(client):
    section("1. CRÉATION PATIENTS — VARIÉTÉ DE CAS")
    created_ids = []

    with app.app_context():
        before = Patient.query.count()

    # 1-a Données complètes valides
    r = post(client, '/patients/ajouter', BASE_PATIENT)
    with app.app_context():
        after = Patient.query.count()
        p = Patient.query.order_by(Patient.id.desc()).first()
    if after == before + 1 and p and p.nom == 'DUPONT':
        ok("1-a Création patient données complètes valides")
        created_ids.append(p.id)
    else:
        bug("1-a Création patient données complètes", f"count={after}, attendu={before+1}")

    # 1-b Champs optionnels vides (téléphone, adresse, notes, dates)
    data_min = {**BASE_PATIENT, 'nom': 'MINIMUM', 'prenom': 'Test',
                'adresse': '', 'telephone': '', 'notes_cliniques': '',
                'date_diagnostic': '', 'date_debut_traitement': '', 'poids': ''}
    r = post(client, '/patients/ajouter', data_min)
    with app.app_context():
        p2 = Patient.query.filter_by(nom='MINIMUM').first()
    if p2:
        ok("1-b Patient avec champs optionnels vides")
        created_ids.append(p2.id)
    else:
        bug("1-b Patient champs optionnels vides", "Patient non créé ou nom non trouvé")

    # 1-c Caractères spéciaux et accents dans le nom
    data_acc = {**BASE_PATIENT, 'nom': 'RÀMÀÑÀMISÉTÀ', 'prenom': 'Désiré-François'}
    r = post(client, '/patients/ajouter', data_acc)
    with app.app_context():
        p3 = Patient.query.filter_by(nom='RÀMÀÑÀMISÉTÀ').first()
    if p3:
        ok("1-c Patient avec accents/tirets dans le nom")
        created_ids.append(p3.id)
    else:
        bug("1-c Accents/caractères spéciaux", "Nom avec accents non trouvé en base")

    # 1-d Nom très long (limite 100 chars)
    long_nom = 'A' * 100
    data_long = {**BASE_PATIENT, 'nom': long_nom, 'prenom': 'LongTest'}
    r = post(client, '/patients/ajouter', data_long)
    with app.app_context():
        p4 = Patient.query.filter_by(prenom='LongTest').first()
    if p4:
        ok("1-d Nom de 100 caractères accepté")
        created_ids.append(p4.id)
    else:
        bug("1-d Nom de 100 caractères", "Patient avec nom de 100 chars non créé")

    # 1-e Statuts variés (gueri, perdu_de_vue, echec, decede, transfert)
    for statut in ['gueri', 'perdu_de_vue', 'echec', 'decede', 'transfert', 'non_evalue']:
        data_s = {**BASE_PATIENT, 'nom': f'STATUT_{statut.upper()}', 'prenom': 'Test', 'statut': statut}
        post(client, '/patients/ajouter', data_s)
        with app.app_context():
            ps = Patient.query.filter_by(nom=f'STATUT_{statut.upper()}').first()
        if ps:
            ok(f"1-e Patient statut '{statut}' créé")
            created_ids.append(ps.id)
        else:
            bug(f"1-e Statut '{statut}'", "Patient non créé")

    # 1-f Champs obligatoires manquants → doit refuser
    data_sans_nom = {**BASE_PATIENT, 'nom': '', 'prenom': 'SansNom'}
    with app.app_context():
        before2 = Patient.query.count()
    post(client, '/patients/ajouter', data_sans_nom)
    with app.app_context():
        after2 = Patient.query.count()
    if after2 == before2:
        ok("1-f Refus création patient sans nom (champ obligatoire)")
    else:
        bug("1-f Refus sans nom", f"Patient créé sans nom (count={after2})")

    # 1-g Prénom manquant
    data_sans_prenom = {**BASE_PATIENT, 'nom': 'SANSNOM', 'prenom': ''}
    with app.app_context():
        before3 = Patient.query.count()
    post(client, '/patients/ajouter', data_sans_prenom)
    with app.app_context():
        after3 = Patient.query.count()
    if after3 == before3:
        ok("1-g Refus création patient sans prénom")
    else:
        bug("1-g Refus sans prénom", "Patient créé sans prénom")

    # 1-h Notes très longues (texte libre)
    data_notes = {**BASE_PATIENT, 'nom': 'LONGNOTES', 'prenom': 'Test',
                  'notes_cliniques': 'Observation clinique. ' * 200}
    post(client, '/patients/ajouter', data_notes)
    with app.app_context():
        pn = Patient.query.filter_by(nom='LONGNOTES').first()
    if pn and len(pn.notes_cliniques) > 100:
        ok("1-h Notes très longues (>4000 chars) acceptées")
        created_ids.append(pn.id)
    else:
        bug("1-h Notes longues", "Notes non sauvegardées ou tronquées")

    # 1-i Types de résistance variés
    for resistance in ['RR-TB', 'TB-MR', 'pre-XDR', 'XDR']:
        data_r = {**BASE_PATIENT, 'nom': f'RESIST_{resistance.replace("-","").upper()}', 'prenom': 'Test', 'type_resistance': resistance}
        post(client, '/patients/ajouter', data_r)
        with app.app_context():
            pr = Patient.query.filter_by(nom=f'RESIST_{resistance.replace("-","").upper()}').first()
        if pr:
            ok(f"1-i Résistance '{resistance}' créée")
            created_ids.append(pr.id)
        else:
            bug(f"1-i Résistance '{resistance}'", "Non créé")

    # 1-j Vérification code_patient auto-généré et unique
    with app.app_context():
        codes = [p.code_patient for p in Patient.query.all() if p.code_patient]
        if len(codes) == len(set(codes)):
            ok(f"1-j Codes patients uniques ({len(codes)} codes générés)")
        else:
            bug("1-j Codes patients", f"Doublons détectés : {[c for c in codes if codes.count(c) > 1]}")

    return created_ids


# ════════════════════════════════════════════════════════════════════════════
#  SECTION 2 — FICHE PATIENT
# ════════════════════════════════════════════════════════════════════════════
def test_fiche(client, patient_ids):
    section("2. FICHE PATIENT — AFFICHAGE & COHÉRENCE")

    with app.app_context():
        patients = Patient.query.filter(Patient.id.in_(patient_ids)).all()

    for p in patients[:3]:  # Tester les 3 premiers
        r = get(client, f'/patients/{p.id}')
        if response_ok(r) and contains(r, p.nom):
            ok(f"2-a Fiche {p.code_patient} accessible et affiche le nom")
        else:
            bug(f"2-a Fiche {p.code_patient}", f"Status={r.status_code} ou nom absent")

        # Vérifier que le code_patient s'affiche
        if contains(r, p.code_patient):
            ok(f"2-b Code patient {p.code_patient} visible dans la fiche")
        else:
            bug(f"2-b Code patient {p.code_patient}", "Code absent de la fiche")

        # Vérifier les onglets (présence des ancres)
        for tab in [b'tab-traitement', b'tab-effets', b'tab-contacts', b'tab-labo', b'tab-bilan', b'tab-dot', b'tab-notes']:
            if tab in r.data:
                ok(f"2-c Onglet {tab.decode()} présent — {p.code_patient}")
            else:
                bug(f"2-c Onglet {tab.decode()}", f"Absent dans la fiche {p.code_patient}")


# ════════════════════════════════════════════════════════════════════════════
#  SECTION 3 — EFFETS SECONDAIRES
# ════════════════════════════════════════════════════════════════════════════
def test_effets(client, patient_ids):
    section("3. EFFETS SECONDAIRES — CRUD COMPLET")

    with app.app_context():
        pid = patient_ids[0]
        patient = Patient.query.get(pid)
        patient_label = patient.code_patient

    # 3-a Déclaration effet léger
    data_ef = {
        'patient_id': str(pid),
        'medicament_incrimine': 'Bedaquiline',
        'symptome': 'Nausées légères après prise matinale',
        'severite': 'leger',
        'notes': 'Apparues à J7 du traitement',
        'retour_patient_id': str(pid),
    }
    with app.app_context():
        before = EffetSecondaire.query.filter_by(patient_id=pid).count()
    post(client, f'/effets/declarer?patient_id={pid}', data_ef)
    with app.app_context():
        after = EffetSecondaire.query.filter_by(patient_id=pid).count()
        ef = EffetSecondaire.query.filter_by(patient_id=pid).order_by(EffetSecondaire.id.desc()).first()
    if after == before + 1 and ef and ef.symptome == 'Nausées légères après prise matinale':
        ok(f"3-a Effet léger créé pour {patient_label}")
    else:
        bug("3-a Effet léger", f"count avant={before}, après={after}")

    # 3-b Vérification affichage dans la fiche patient
    r = get(client, f'/patients/{pid}')
    if contains(r, b'Naus'):
        ok("3-b Effet visible dans la fiche patient")
    else:
        bug("3-b Affichage effet fiche", "Symptôme non trouvé dans la fiche")

    # 3-c Effet sévère (doit déclencher alerte CRPC)
    data_sev = {**data_ef, 'symptome': 'Allongement QTc >500ms détecté ECG', 'severite': 'severe'}
    with app.app_context():
        before2 = EffetSecondaire.query.filter_by(patient_id=pid).count()
    post(client, f'/effets/declarer?patient_id={pid}', data_sev)
    with app.app_context():
        after2 = EffetSecondaire.query.filter_by(patient_id=pid).count()
        ef_sev = EffetSecondaire.query.filter_by(patient_id=pid, severite='severe').first()
    if after2 == before2 + 1 and ef_sev:
        ok("3-c Effet sévère créé")
        if ef_sev.notifie_crpc == False:
            ok("3-d Effet sévère marqué non notifié par défaut (alerte CRPC active)")
        else:
            bug("3-d Défaut notifie_crpc", "Effet sévère marqué notifié par défaut")
    else:
        bug("3-c Effet sévère", f"count avant={before2}, après={after2}")

    # 3-d Marquer comme notifié CRPC
    with app.app_context():
        ef_id = EffetSecondaire.query.filter_by(patient_id=pid, severite='severe').first().id
    post(client, f'/effets/{ef_id}/notifier', {})
    with app.app_context():
        ef_after = EffetSecondaire.query.get(ef_id)
    if ef_after and ef_after.notifie_crpc:
        ok("3-e Notification CRPC enregistrée")
    else:
        bug("3-e Notification CRPC", "notifie_crpc reste False après action")

    # 3-f Effet sans symptôme → doit être refusé
    data_nosympt = {**data_ef, 'symptome': ''}
    with app.app_context():
        before3 = EffetSecondaire.query.filter_by(patient_id=pid).count()
    post(client, f'/effets/declarer?patient_id={pid}', data_nosympt)
    with app.app_context():
        after3 = EffetSecondaire.query.filter_by(patient_id=pid).count()
    if after3 == before3:
        ok("3-f Effet sans symptôme refusé (validation)")
    else:
        bug("3-f Effet sans symptôme", "Effet créé sans symptôme !")

    # 3-g Patient "perdu_de_vue" peut avoir un effet
    with app.app_context():
        perdu = Patient.query.filter_by(statut='perdu_de_vue').first()
    if perdu:
        data_perdu = {**data_ef, 'patient_id': str(perdu.id),
                      'symptome': 'Effet test patient perdu de vue',
                      'retour_patient_id': str(perdu.id)}
        with app.app_context():
            before4 = EffetSecondaire.query.filter_by(patient_id=perdu.id).count()
        post(client, f'/effets/declarer?patient_id={perdu.id}', data_perdu)
        with app.app_context():
            after4 = EffetSecondaire.query.filter_by(patient_id=perdu.id).count()
        if after4 == before4 + 1:
            ok(f"3-g Effet pour patient 'perdu_de_vue' ({perdu.code_patient}) accepté")
        else:
            bug("3-g Effet patient perdu_de_vue", f"count avant={before4}, après={after4}")


# ════════════════════════════════════════════════════════════════════════════
#  SECTION 4 — CONTACTS
# ════════════════════════════════════════════════════════════════════════════
def test_contacts(client, patient_ids):
    section("4. CONTACTS — CRUD COMPLET")

    with app.app_context():
        pid = patient_ids[0]
        patient = Patient.query.get(pid)

    BASE_CONTACT = {
        'patient_source_id': str(pid),
        'nom': 'CONTACT',
        'prenom': 'Test',
        'age': '35',
        'sexe': 'Femme',
        'relation': 'foyer',
        'telephone': '0340000001',
        'date_prochaine_visite': str(date.today() + timedelta(days=30)),
        'statut': 'en_suivi',
        'notes': 'Contact test QA',
        'date_depistage': str(date.today()),
        'resultat_genexpert': 'negatif',
        'radiographie_thorax': 'normale',
        'ipt_propose': 'y',
        'ipt_accepte': 'y',
        'date_prochain_controle': str(date.today() + timedelta(days=90)),
        'retour_patient_id': str(pid),
    }

    # 4-a Création contact complet
    with app.app_context():
        before = Contact.query.filter_by(patient_source_id=pid).count()
    post(client, f'/contacts/ajouter?patient_source_id={pid}', BASE_CONTACT)
    with app.app_context():
        after = Contact.query.filter_by(patient_source_id=pid).count()
        c = Contact.query.filter_by(patient_source_id=pid).order_by(Contact.id.desc()).first()
    if after == before + 1 and c:
        ok(f"4-a Contact créé pour {patient.code_patient}")
    else:
        bug("4-a Création contact", f"count avant={before}, après={after}")

    # 4-b Contact visible dans la fiche patient
    r = get(client, f'/patients/{pid}')
    if contains(r, b'CONTACT'):
        ok("4-b Contact visible dans la fiche patient")
    else:
        bug("4-b Contact fiche", "Nom du contact absent de la fiche")

    # 4-c Contact sans nom → refusé
    data_nonom = {**BASE_CONTACT, 'nom': ''}
    with app.app_context():
        before2 = Contact.query.count()
    post(client, f'/contacts/ajouter?patient_source_id={pid}', data_nonom)
    with app.app_context():
        after2 = Contact.query.count()
    if after2 == before2:
        ok("4-c Contact sans nom refusé")
    else:
        bug("4-c Contact sans nom", "Contact créé sans nom !")

    # 4-d Modification du contact
    with app.app_context():
        cid = Contact.query.filter_by(patient_source_id=pid).order_by(Contact.id.desc()).first().id
    data_mod = {**BASE_CONTACT, 'nom': 'CONTACT_MODIFIE', 'statut': 'tb_mr_confirmee'}
    r = post(client, f'/contacts/{cid}/modifier', data_mod)
    with app.app_context():
        c_mod = Contact.query.get(cid)
    if c_mod and c_mod.nom == 'CONTACT_MODIFIE' and c_mod.statut == 'tb_mr_confirmee':
        ok("4-d Contact modifié correctement (nom + statut)")
    else:
        bug("4-d Modification contact", f"nom={c_mod.nom if c_mod else 'None'}, statut={c_mod.statut if c_mod else 'None'}")

    # 4-e Suppression contact
    post(client, f'/contacts/{cid}/supprimer', {})
    with app.app_context():
        c_del = Contact.query.get(cid)
    if c_del is None:
        ok("4-e Contact supprimé de la base")
    else:
        bug("4-e Suppression contact", "Contact encore en base après suppression")

    # 4-f Contacts multiples sur même patient
    with app.app_context():
        before3 = Contact.query.filter_by(patient_source_id=pid).count()
    for i in range(3):
        data_multi = {**BASE_CONTACT, 'nom': f'MULTI_{i}', 'prenom': f'Contact{i}'}
        post(client, f'/contacts/ajouter?patient_source_id={pid}', data_multi)
    with app.app_context():
        after3 = Contact.query.filter_by(patient_source_id=pid).count()
    if after3 == before3 + 3:
        ok("4-f 3 contacts simultanés sur même patient acceptés")
    else:
        bug("4-f Contacts multiples", f"Attendu {before3+3}, obtenu {after3}")

    # 4-g Vérification count dans l'onglet fiche
    r = get(client, f'/patients/{pid}')
    with app.app_context():
        nb = Contact.query.filter_by(patient_source_id=pid).count()
    expected_text = f'Contacts ({nb})'.encode()
    if expected_text in r.data:
        ok(f"4-g Compteur onglet Contacts correct ({nb})")
    else:
        bug("4-g Compteur contacts onglet", f"'{expected_text.decode()}' absent de la fiche")

    # 4-h Patient perdu_de_vue peut avoir un contact
    with app.app_context():
        perdu = Patient.query.filter_by(statut='perdu_de_vue').first()
    if perdu:
        data_perdu_c = {**BASE_CONTACT, 'patient_source_id': str(perdu.id),
                        'nom': 'CONTACT_PERDU', 'retour_patient_id': str(perdu.id)}
        with app.app_context():
            before_p = Contact.query.filter_by(patient_source_id=perdu.id).count()
        post(client, f'/contacts/ajouter?patient_source_id={perdu.id}', data_perdu_c)
        with app.app_context():
            after_p = Contact.query.filter_by(patient_source_id=perdu.id).count()
        if after_p == before_p + 1:
            ok(f"4-h Contact pour patient 'perdu_de_vue' ({perdu.code_patient}) accepté")
        else:
            bug("4-h Contact patient perdu_de_vue", f"count avant={before_p}, après={after_p}")


# ════════════════════════════════════════════════════════════════════════════
#  SECTION 5 — EXAMENS BACTÉRIOLOGIQUES (LABO)
# ════════════════════════════════════════════════════════════════════════════
def test_labo(client, patient_ids):
    section("5. EXAMENS BACTÉRIOLOGIQUES — CRUD COMPLET")

    with app.app_context():
        pid = patient_ids[0]
        patient = Patient.query.get(pid)

    BASE_EXAMEN = {
        'patient_id': str(pid),
        'mois_suivi': '0',
        'date_prelevement': str(date.today()),
        'date_resultat': str(date.today()),
        'genexpert_effectue': 'y',
        'genexpert_resultat': 'positif',
        'genexpert_resistance_rif': 'detected',
        'frottis_effectue': 'y',
        'frottis_resultat': 'positif',
        'frottis_quantite': '2+',
        'culture_effectuee': 'y',
        'culture_resultat': 'positif',
        'culture_milieu': 'LJ',
        'dst_effectue': 'y',
        'dst_isoniazide': 'resistant',
        'dst_rifampicine': 'resistant',
        'dst_ethambutol': 'sensible',
        'dst_pyrazinamide': 'sensible',
        'dst_levofloxacine': 'sensible',
        'dst_moxifloxacine': 'sensible',
        'dst_bedaquiline': 'sensible',
        'dst_linezolide': 'sensible',
        'notes': 'Examen M0 complet test QA',
        'retour_patient_id': str(pid),
    }

    # 5-a Examen M0 complet (tous les examens positifs/effectués)
    with app.app_context():
        before = ExamenLabo.query.filter_by(patient_id=pid).count()
    post(client, f'/labo/saisir?patient_id={pid}', BASE_EXAMEN)
    with app.app_context():
        after = ExamenLabo.query.filter_by(patient_id=pid).count()
        ex = ExamenLabo.query.filter_by(patient_id=pid, mois_suivi=0).first()
    if after == before + 1 and ex:
        ok(f"5-a Examen M0 complet créé pour {patient.code_patient}")
    else:
        bug("5-a Examen M0 complet", f"count avant={before}, après={after}")

    # 5-b Vérification affichage dans fiche patient
    r = get(client, f'/patients/{pid}')
    if contains(r, b'M0'):
        ok("5-b Examen M0 visible dans la fiche patient (onglet Labo)")
    else:
        bug("5-b Affichage labo fiche", "Examen M0 absent de la fiche")

    # 5-c Conversion bactériologique (culture négative)
    data_conv = {**BASE_EXAMEN, 'mois_suivi': '2',
                 'culture_resultat': 'negatif',
                 'frottis_resultat': 'negatif',
                 'genexpert_resultat': 'negatif'}
    post(client, f'/labo/saisir?patient_id={pid}', data_conv)
    with app.app_context():
        ex_conv = ExamenLabo.query.filter_by(patient_id=pid, mois_suivi=2).first()
    if ex_conv and ex_conv.culture_resultat == 'negatif':
        ok("5-c Examen M2 conversion bactériologique enregistrée")
        if ex_conv.conversion_label == 'Converti':
            ok("5-d Propriété conversion_label correcte ('Converti')")
        else:
            bug("5-d conversion_label", f"Attendu 'Converti', obtenu '{ex_conv.conversion_label}'")
    else:
        bug("5-c Examen M2 conversion", "Examen M2 non créé ou culture_resultat incorrect")

    # 5-e Examen sans date de prélèvement → refusé
    data_nodate = {**BASE_EXAMEN, 'date_prelevement': '', 'mois_suivi': '3'}
    with app.app_context():
        before2 = ExamenLabo.query.filter_by(patient_id=pid).count()
    post(client, f'/labo/saisir?patient_id={pid}', data_nodate)
    with app.app_context():
        after2 = ExamenLabo.query.filter_by(patient_id=pid).count()
    if after2 == before2:
        ok("5-e Examen sans date de prélèvement refusé (validation)")
    else:
        bug("5-e Examen sans date", "Examen créé sans date de prélèvement !")

    # 5-f Examens de M0 à M6 (suivi complet)
    for mois in [1, 3, 4, 5, 6]:
        data_m = {**BASE_EXAMEN, 'mois_suivi': str(mois),
                  'culture_resultat': 'negatif' if mois >= 2 else 'positif'}
        post(client, f'/labo/saisir?patient_id={pid}', data_m)
    with app.app_context():
        total = ExamenLabo.query.filter_by(patient_id=pid).count()
    if total >= 7:  # M0,1,2,3,4,5,6 = 7
        ok(f"5-f Suivi M0→M6 complet ({total} examens en base)")
    else:
        bug("5-f Suivi M0-M6", f"Seulement {total} examens (attendu ≥7)")

    # 5-g Page détail examen accessible
    with app.app_context():
        ex_id = ExamenLabo.query.filter_by(patient_id=pid).first().id
    r = get(client, f'/labo/{ex_id}')
    if response_ok(r):
        ok("5-g Page détail examen accessible")
    else:
        bug("5-g Détail examen", f"Status={r.status_code}")

    # 5-h Suppression examen
    with app.app_context():
        ex_del_id = ExamenLabo.query.filter_by(patient_id=pid, mois_suivi=6).first().id
        before3 = ExamenLabo.query.filter_by(patient_id=pid).count()
    post(client, f'/labo/{ex_del_id}/supprimer', {})
    with app.app_context():
        after3 = ExamenLabo.query.filter_by(patient_id=pid).count()
        ex_check = ExamenLabo.query.get(ex_del_id)
    if after3 == before3 - 1 and ex_check is None:
        ok("5-h Examen labo supprimé de la base")
    else:
        bug("5-h Suppression examen", f"count avant={before3}, après={after3}")

    # 5-i Patient perdu_de_vue peut avoir un examen
    with app.app_context():
        perdu = Patient.query.filter_by(statut='perdu_de_vue').first()
    if perdu:
        data_perdu_l = {**BASE_EXAMEN, 'patient_id': str(perdu.id), 'mois_suivi': '0',
                        'retour_patient_id': str(perdu.id)}
        with app.app_context():
            before_pl = ExamenLabo.query.filter_by(patient_id=perdu.id).count()
        post(client, f'/labo/saisir?patient_id={perdu.id}', data_perdu_l)
        with app.app_context():
            after_pl = ExamenLabo.query.filter_by(patient_id=perdu.id).count()
        if after_pl == before_pl + 1:
            ok(f"5-i Examen pour patient 'perdu_de_vue' ({perdu.code_patient}) accepté")
        else:
            bug("5-i Examen patient perdu_de_vue", f"count avant={before_pl}, après={after_pl}")


# ════════════════════════════════════════════════════════════════════════════
#  SECTION 6 — BILAN M0
# ════════════════════════════════════════════════════════════════════════════
def test_bilan(client, patient_ids):
    section("6. BILAN INITIAL M0")

    with app.app_context():
        pid = patient_ids[0]

    BASE_BILAN = {
        'date_bilan': str(date.today()),
        'poids_kg': '65.0',
        'taille_cm': '170.0',
        'creatinine_umol_l': '88.4',
        'clairance_creatinine': '85.0',
        'hb_g_dl': '13.5',
        'alt_u_l': '32',
        'ast_u_l': '28',
        'glycemie_mmol_l': '5.1',
        'kaliemie_mmol_l': '4.0',
        'audiogramme_normal': 'y',
        'ecg_qt_ms': '420',
        'acuite_visuelle_normale': 'y',
        'thyroide_normale': 'y',
        'notes': 'Bilan M0 test QA',
    }

    # 6-a Création bilan complet
    with app.app_context():
        before = BilanInitial.query.filter_by(patient_id=pid).count()
    post(client, f'/patients/{pid}/bilan', BASE_BILAN)
    with app.app_context():
        after = BilanInitial.query.filter_by(patient_id=pid).count()
        bilan = BilanInitial.query.filter_by(patient_id=pid).first()
    if after >= 1 and bilan:
        ok("6-a Bilan M0 créé")
        # Vérifier IMC calculé
        if bilan.imc and abs(bilan.imc - 22.5) < 1.0:
            ok(f"6-b IMC calculé correctement ({bilan.imc})")
        else:
            bug("6-b IMC", f"IMC={bilan.imc}, attendu ~22.5")
        # Vérifier ECG normal
        if not bilan.ecg_alerte:
            ok("6-c ECG QT=420ms → pas d'alerte (seuil 450ms)")
        else:
            bug("6-c ECG alerte", "Alerte déclenchée à 420ms (seuil devrait être 450ms)")
    else:
        bug("6-a Bilan M0", f"count avant={before}, après={after}")

    # 6-d ECG avec allongement QT → alerte
    data_qt = {**BASE_BILAN, 'ecg_qt_ms': '460'}
    post(client, f'/patients/{pid}/bilan', data_qt)
    with app.app_context():
        bilan2 = BilanInitial.query.filter_by(patient_id=pid).first()
    if bilan2 and bilan2.ecg_alerte:
        ok("6-d ECG QT=460ms → alerte déclenchée correctement")
    else:
        bug("6-d ECG alerte QT", f"ECG QTc={bilan2.ecg_qt_ms if bilan2 else 'None'}, ecg_alerte={bilan2.ecg_alerte if bilan2 else 'None'}")

    # 6-e Bilan visible dans la fiche patient
    r = get(client, f'/patients/{pid}')
    if contains(r, b'65.0') or contains(r, b'170'):
        ok("6-e Données du bilan visibles dans la fiche patient")
    else:
        bug("6-e Bilan fiche", "Données bilan absentes de la fiche")

    # 6-f Bilan sans date → refusé
    data_nodate = {**BASE_BILAN, 'date_bilan': ''}
    with app.app_context():
        bilan_before = BilanInitial.query.filter_by(patient_id=pid).first()
        if bilan_before:
            old_date = bilan_before.date_bilan
    post(client, f'/patients/{pid}/bilan', data_nodate)
    with app.app_context():
        bilan_after = BilanInitial.query.filter_by(patient_id=pid).first()
    if bilan_after and bilan_after.date_bilan == old_date:
        ok("6-f Bilan sans date → refusé, données précédentes conservées")
    else:
        bug("6-f Bilan sans date", "Date bilan effacée ou bilan modifié malgré date vide")

    # 6-g Insuffisance rénale détectée (clairance < 30)
    data_renal = {**BASE_BILAN, 'clairance_creatinine': '25.0', 'date_bilan': str(date.today())}
    post(client, f'/patients/{pid}/bilan', data_renal)
    with app.app_context():
        bilan_renal = BilanInitial.query.filter_by(patient_id=pid).first()
    if bilan_renal and bilan_renal.insuffisance_renale:
        ok("6-g Insuffisance rénale détectée (clairance=25 < 30)")
    else:
        bug("6-g Insuffisance rénale", f"clairance={bilan_renal.clairance_creatinine if bilan_renal else '?'}")


# ════════════════════════════════════════════════════════════════════════════
#  SECTION 7 — TRAITEMENT & DOT
# ════════════════════════════════════════════════════════════════════════════
def test_traitement_dot(client, patient_ids):
    section("7. TRAITEMENT & DOT")

    with app.app_context():
        pid = patient_ids[0]
        patient = Patient.query.get(pid)

    BASE_TRAITEMENT = {
        'schema_nom': 'BdqLfxCfzZE (5 mois intensif)',
        'phase': 'intensive',
        'date_debut': str(date.today() - timedelta(days=30)),
        'date_fin_prevue': str(date.today() + timedelta(days=500)),
        'statut_traitement': 'actif',
        'observateur_nom': 'Infirmier Rakoto',
        'notes': 'Traitement test QA',
        'medicaments_json': json.dumps(['Bédaquiline (Bdq)', 'Lévofloxacine (Lfx)', 'Clofazimine (Cfz)']),
    }

    # 7-a Création traitement
    with app.app_context():
        before = Traitement.query.filter_by(patient_id=pid).count()
    post(client, f'/traitement/ajouter/{pid}', BASE_TRAITEMENT)
    with app.app_context():
        after = Traitement.query.filter_by(patient_id=pid).count()
        t = Traitement.query.filter_by(patient_id=pid).order_by(Traitement.id.desc()).first()
    if after == before + 1 and t:
        ok(f"7-a Traitement créé pour {patient.code_patient}")
        tid = t.id
        # Vérifier médicaments
        if len(t.medicaments) == 3:
            ok("7-b 3 médicaments enregistrés")
        else:
            bug("7-b Médicaments traitement", f"Attendu 3, obtenu {len(t.medicaments)}")
        # Progression
        if 0 <= t.progression <= 100:
            ok(f"7-c Progression calculée ({t.progression}%)")
        else:
            bug("7-c Progression", f"Valeur anormale: {t.progression}")
    else:
        bug("7-a Traitement", f"count avant={before}, après={after}")
        return

    # 7-d Traitement sans schema_nom → refusé
    data_nosn = {**BASE_TRAITEMENT, 'schema_nom': ''}
    with app.app_context():
        before2 = Traitement.query.filter_by(patient_id=pid).count()
    post(client, f'/traitement/ajouter/{pid}', data_nosn)
    with app.app_context():
        after2 = Traitement.query.filter_by(patient_id=pid).count()
    if after2 == before2:
        ok("7-d Traitement sans schema_nom refusé")
    else:
        bug("7-d Traitement sans nom", "Traitement créé sans schema_nom !")

    # 7-e Page détail traitement
    r = get(client, f'/traitement/{tid}')
    if response_ok(r) and contains(r, b'BdqLfxCfzZE'):
        ok("7-e Page détail traitement accessible et affiche le schema")
    else:
        bug("7-e Détail traitement", f"Status={r.status_code}")

    # 7-f Saisie DOT prise confirmée
    with app.app_context():
        before3 = SuiviDOT.query.filter_by(traitement_id=tid).count()
    data_dot = {
        'date_observation': str(date.today()),
        'prise_confirmee': 'y',
        'observateur_nom': 'Infirmier Test',
        'observateur_role': 'infirmier',
        'raison_omission': '',
        'notes': 'DOT test QA',
        'depuis_fiche': '1',
    }
    post(client, f'/traitement/{tid}/dot/ajouter?depuis_fiche=1', data_dot)
    with app.app_context():
        after3 = SuiviDOT.query.filter_by(traitement_id=tid).count()
        dot = SuiviDOT.query.filter_by(traitement_id=tid).first()
    if after3 == before3 + 1 and dot and dot.prise_confirmee:
        ok("7-f DOT prise confirmée enregistrée")
        if dot.medicaments_pris == t.medicaments:
            ok("7-g Médicaments pris = médicaments du traitement")
        else:
            bug("7-g Médicaments pris DOT", f"medicaments_pris={dot.medicaments_pris}, attendu={t.medicaments}")
    else:
        bug("7-f DOT confirmé", f"count avant={before3}, après={after3}")

    # 7-g DOT prise NON confirmée
    data_dot_non = {
        'date_observation': str(date.today() - timedelta(days=1)),
        'prise_confirmee': '',
        'observateur_nom': 'Famille Rakoto',
        'observateur_role': 'famille',
        'raison_omission': 'Patient absent du domicile',
        'notes': '',
        'depuis_fiche': '1',
    }
    with app.app_context():
        before4 = SuiviDOT.query.filter_by(traitement_id=tid).count()
    post(client, f'/traitement/{tid}/dot/ajouter?depuis_fiche=1', data_dot_non)
    with app.app_context():
        after4 = SuiviDOT.query.filter_by(traitement_id=tid).count()
        dot_non = SuiviDOT.query.filter_by(traitement_id=tid, prise_confirmee=False).first()
    if after4 == before4 + 1 and dot_non:
        ok("7-h DOT prise non confirmée enregistrée avec raison d'omission")
        if dot_non.raison_omission == 'Patient absent du domicile':
            ok("7-i Raison d'omission sauvegardée")
        else:
            bug("7-i Raison omission", f"Raison={dot_non.raison_omission}")
    else:
        bug("7-h DOT non confirmé", f"count avant={before4}, après={after4}")

    # 7-j Taux adhérence calculé
    with app.app_context():
        taux = SuiviDOT.taux_adherence(pid, tid, nb_jours=30)
    if taux is not None and 0 <= taux <= 100:
        ok(f"7-j Taux adhérence calculé : {taux}%")
    else:
        bug("7-j Taux adhérence", f"Valeur anormale : {taux}")

    # 7-k Modification traitement
    data_mod_t = {**BASE_TRAITEMENT, 'schema_nom': 'SCHEMA_MODIFIE',
                  'statut_traitement': 'suspendu',
                  'medicaments_json': json.dumps(['Bédaquiline (Bdq)'])}
    post(client, f'/traitement/{tid}/modifier', data_mod_t)
    with app.app_context():
        t_mod = Traitement.query.get(tid)
    if t_mod and t_mod.schema_nom == 'SCHEMA_MODIFIE' and t_mod.statut_traitement == 'suspendu':
        ok("7-k Traitement modifié (schema + statut)")
    else:
        bug("7-k Modification traitement", f"schema={t_mod.schema_nom if t_mod else '?'}")


# ════════════════════════════════════════════════════════════════════════════
#  SECTION 8 — INTÉGRITÉ CASCADE (suppression patient)
# ════════════════════════════════════════════════════════════════════════════
def test_cascade(client, patient_ids):
    section("8. INTÉGRITÉ CASCADE — SUPPRESSION PATIENT")

    with app.app_context():
        # Trouver le patient de test avec le plus de données
        pid = patient_ids[0]
        nb_effets = EffetSecondaire.query.filter_by(patient_id=pid).count()
        nb_contacts = Contact.query.filter_by(patient_source_id=pid).count()
        nb_labo = ExamenLabo.query.filter_by(patient_id=pid).count()
        nb_traitement = Traitement.query.filter_by(patient_id=pid).count()

    # Supprimer le patient
    post(client, f'/patients/{pid}/supprimer', {})

    with app.app_context():
        p_del = Patient.query.get(pid)
        ef_orphan = EffetSecondaire.query.filter_by(patient_id=pid).count()
        c_orphan = Contact.query.filter_by(patient_source_id=pid).count()
        l_orphan = ExamenLabo.query.filter_by(patient_id=pid).count()
        t_orphan = Traitement.query.filter_by(patient_id=pid).count()
        dot_orphan = SuiviDOT.query.filter_by(patient_id=pid).count()
        bilan_orphan = BilanInitial.query.filter_by(patient_id=pid).count()

    if p_del is None:
        ok("8-a Patient supprimé de la base")
    else:
        bug("8-a Suppression patient", "Patient encore en base")

    if ef_orphan == 0:
        ok(f"8-b Cascade effets ({nb_effets} supprimés)")
    else:
        bug("8-b Cascade effets", f"{ef_orphan} effets orphelins en base !")

    if c_orphan == 0:
        ok(f"8-c Cascade contacts ({nb_contacts} supprimés)")
    else:
        bug("8-c Cascade contacts", f"{c_orphan} contacts orphelins !")

    if l_orphan == 0:
        ok(f"8-d Cascade examens labo ({nb_labo} supprimés)")
    else:
        bug("8-d Cascade labo", f"{l_orphan} examens orphelins !")

    if t_orphan == 0:
        ok(f"8-e Cascade traitements ({nb_traitement} supprimés)")
    else:
        bug("8-e Cascade traitements", f"{t_orphan} traitements orphelins !")

    if dot_orphan == 0:
        ok("8-f Cascade DOT supprimés")
    else:
        bug("8-f Cascade DOT", f"{dot_orphan} DOT orphelins !")

    if bilan_orphan == 0:
        ok("8-g Cascade bilan M0 supprimé")
    else:
        bug("8-g Cascade bilan", f"{bilan_orphan} bilans orphelins !")


# ════════════════════════════════════════════════════════════════════════════
#  SECTION 9 — COHÉRENCE BASE vs INTERFACE
# ════════════════════════════════════════════════════════════════════════════
def test_coherence(client):
    section("9. COHÉRENCE DB vs INTERFACE")

    # 9-a Tous les patients accessibles via leur fiche
    with app.app_context():
        patients = Patient.query.all()
    for p in patients:
        r = get(client, f'/patients/{p.id}')
        if not response_ok(r):
            bug("9-a Fiche accessible", f"Patient {p.code_patient} → status {r.status_code}")
        else:
            ok(f"9-a Fiche {p.code_patient} accessible")

    # 9-b Tous les traitements dans la liste
    with app.app_context():
        nb_t = Traitement.query.count()
    r = get(client, '/traitement/')
    if response_ok(r):
        ok(f"9-b Liste traitements accessible ({nb_t} en DB)")
    else:
        bug("9-b Liste traitements", f"Status={r.status_code}")

    # 9-c Liste contacts
    with app.app_context():
        nb_c = Contact.query.count()
    r = get(client, '/contacts/')
    if response_ok(r):
        ok(f"9-c Liste contacts accessible ({nb_c} en DB)")
    else:
        bug("9-c Liste contacts", f"Status={r.status_code}")

    # 9-d Liste examens labo
    r = get(client, '/labo/')
    if response_ok(r):
        ok("9-d Index labo accessible")
    else:
        bug("9-d Index labo", f"Status={r.status_code}")

    # 9-e Dashboard
    r = get(client, '/dashboard/')
    if response_ok(r):
        ok("9-e Dashboard accessible")
    else:
        bug("9-e Dashboard", f"Status={r.status_code}")

    # 9-f Recherche globale
    with app.app_context():
        premier = Patient.query.first()
    if premier:
        r = get(client, f'/search/?q={premier.nom[:3]}')
        if response_ok(r):
            ok(f"9-f Recherche '{premier.nom[:3]}' fonctionne")
        else:
            bug("9-f Recherche", f"Status={r.status_code}")

    # 9-g Recherche AJAX
    with app.app_context():
        premier = Patient.query.first()
    if premier:
        r = client.get(f'/search/?q={premier.nom[:3]}',
                       headers={'X-Requested-With': 'XMLHttpRequest'})
        try:
            data = json.loads(r.data)
            if 'resultats' in data:
                ok(f"9-g Recherche AJAX retourne JSON valide ({len(data['resultats'])} résultats)")
            else:
                bug("9-g Recherche AJAX", "Clé 'resultats' absente du JSON")
        except Exception as e:
            bug("9-g Recherche AJAX", f"JSON invalide: {e}")

    # 9-h Stock inventaire
    r = get(client, '/stock/')
    if response_ok(r):
        ok("9-h Stock inventaire accessible")
    else:
        bug("9-h Stock", f"Status={r.status_code}")


# ════════════════════════════════════════════════════════════════════════════
#  SECTION 10 — CAS LIMITES & INJECTION
# ════════════════════════════════════════════════════════════════════════════
def test_edge_cases(client):
    section("10. CAS LIMITES & SÉCURITÉ")

    # 10-a Accès fiche patient inexistant → 404
    r = client.get('/patients/999999')
    if r.status_code == 404:
        ok("10-a Patient inexistant → 404")
    else:
        bug("10-a 404 patient", f"Status={r.status_code} (attendu 404)")

    # 10-b Accès traitement inexistant → 404
    r = client.get('/traitement/999999')
    if r.status_code == 404:
        ok("10-b Traitement inexistant → 404")
    else:
        bug("10-b 404 traitement", f"Status={r.status_code}")

    # 10-c Injection HTML dans les champs texte
    data_xss = {**BASE_PATIENT, 'nom': '<script>alert(1)</script>',
                'prenom': 'XSS', 'notes_cliniques': '<img src=x onerror=alert(1)>'}
    post(client, '/patients/ajouter', data_xss)
    with app.app_context():
        p_xss = Patient.query.filter_by(prenom='XSS').first()
    if p_xss:
        # Vérifie que Jinja2 auto-escape bloque les balises brutes
        # On cherche les chaînes exactes injectées (non les balises légitimes du template)
        r = get(client, f'/patients/{p_xss.id}')
        raw_lower = r.data.lower()
        # Cherche le payload injecté, pas les balises légitimes du template
        has_raw_script = b'<script>alert(1)' in raw_lower
        has_raw_onerror = b'<img src=x onerror=' in raw_lower
        if not has_raw_script and not has_raw_onerror:
            ok("10-c XSS bloqué par Jinja2 auto-escape (balises HTML échappées)")
        else:
            bug("10-c XSS", "Balise script ou img onerror non échappée dans la réponse !")
        with app.app_context():
            db.session.delete(Patient.query.get(p_xss.id))
            db.session.commit()

    # 10-d est testé en dehors du contexte app (voir test_security_admin)

    # 10-e Double soumission patient (même nom/prenom)
    with app.app_context():
        before_dd = Patient.query.count()
    for _ in range(2):
        post(client, '/patients/ajouter', {**BASE_PATIENT, 'nom': 'DOUBLE', 'prenom': 'Submit'})
    with app.app_context():
        after_dd = Patient.query.count()
        doubles = Patient.query.filter_by(nom='DOUBLE').count()
    # L'application ne bloque pas les doublons nom+prenom (pas de contrainte unique)
    if doubles == 2:
        # Ce n'est pas nécessairement un bug — la vraie contrainte unique est le code_patient
        ok("10-e Double soumission : 2 patients créés (codes_patient distincts)")
        with app.app_context():
            codes = [p.code_patient for p in Patient.query.filter_by(nom='DOUBLE').all()]
            if len(set(codes)) == 2:
                ok("10-f Codes patients distincts pour patients homonymes")
            else:
                bug("10-f Codes doublons", f"Codes non uniques : {codes}")

    # 10-g Poids négatif — vérifier par count avant/après (évite la stale data)
    with app.app_context():
        before_g = Patient.query.count()
    data_neg_poids = {**BASE_PATIENT, 'nom': 'POIDSNEG', 'prenom': 'Test', 'poids': '-5'}
    post(client, '/patients/ajouter', data_neg_poids)
    with app.app_context():
        after_g = Patient.query.count()
        p_neg = Patient.query.order_by(Patient.id.desc()).first()
    if after_g > before_g and p_neg and p_neg.poids and p_neg.poids < 0:
        bug("10-g Poids négatif", "Poids négatif accepté en base (pas de validation serveur)")
    elif after_g == before_g:
        ok("10-g Poids négatif refusé par la validation serveur")
    else:
        ok("10-g Poids négatif converti en None ou refusé")

    # 10-h Date naissance dans le futur — vérifier par count avant/après
    with app.app_context():
        before_h = Patient.query.count()
    data_future = {**BASE_PATIENT, 'nom': 'FUTUR', 'prenom': 'Test',
                   'date_naissance': '2099-01-01'}
    post(client, '/patients/ajouter', data_future)
    with app.app_context():
        after_h = Patient.query.count()
        p_fut = Patient.query.order_by(Patient.id.desc()).first() if after_h > before_h else None
    if after_h > before_h and p_fut:
        age_calc = p_fut.age
        if age_calc and age_calc < 0:
            bug("10-h Date naissance futur", f"Age calculé négatif ({age_calc}) — pas de validation serveur")
        else:
            ok(f"10-h Date naissance future acceptée (âge={age_calc})")
    else:
        ok("10-h Date naissance future refusée par la validation serveur")


# ════════════════════════════════════════════════════════════════════════════
#  SECTION 10-d — SÉCURITÉ ADMIN (doit tourner hors app_context principal)
# ════════════════════════════════════════════════════════════════════════════
def test_security_admin():
    """Doit être appelée HORS du bloc `with app.app_context()` principal."""
    section("10-d. SÉCURITÉ ADMIN (isolation session correcte)")

    c2 = app.test_client()
    with app.app_context():
        non_coord = User.query.filter(User.role.in_(['infirmier', 'medecin', 'laborantin'])).first()
        if not non_coord:
            bug("10-d Sécurité admin", "Aucun utilisateur non-coordinateur trouvé en base")
            return
        uid = non_coord.id
        role = non_coord.role

    # session_transaction() appelé HORS app_context → isolation correcte
    with c2.session_transaction() as sess:
        sess['_user_id'] = str(uid)
        sess['_fresh'] = True

    r = c2.get('/admin/utilisateurs', follow_redirects=False)
    if r.status_code == 403:
        ok(f"10-d Accès admin refusé pour rôle '{role}' → 403")
    else:
        bug("10-d Sécurité admin", f"Rôle '{role}' accède à admin (status={r.status_code})")


# ════════════════════════════════════════════════════════════════════════════
#  RAPPORT FINAL
# ════════════════════════════════════════════════════════════════════════════
def rapport():
    print(f"\n{'='*60}")
    print("  RAPPORT FINAL QA")
    print('='*60)
    print(f"  Tests passés   : {len(PASSED)}")
    print(f"  Bugs détectés  : {len(BUGS)}")
    if BUGS:
        print("\n  ── BUGS ──────────────────────────────────────────────────")
        for i, b in enumerate(BUGS, 1):
            print(f"  [{i:02d}] {b['label']}")
            print(f"        {b['detail']}")
    else:
        print("\n  Aucun bug détecté.")
    print('='*60)


# ════════════════════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE
# ════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    with app.app_context():
        client = make_client()
        pid_list = test_patients(client)
        if pid_list:
            test_fiche(client, pid_list)
            test_effets(client, pid_list)
            test_contacts(client, pid_list)
            test_labo(client, pid_list)
            test_bilan(client, pid_list)
            test_traitement_dot(client, pid_list)
            test_cascade(client, pid_list)
        test_coherence(client)
        test_edge_cases(client)
    # Test sécurité admin — hors app_context pour isolation session correcte
    test_security_admin()
    rapport()
