from datetime import date, datetime, timedelta
from ..extensions import db
from ..models import User, Patient, Traitement, EffetSecondaire, Contact, Medicament, ExamenLabo


def seed_demo_data():
    if User.query.first():
        return  # Already seeded

    # ── Utilisateurs ──────────────────────────────────────────────
    coord = User(email='coordinateur@pnlt.mg', nom='RAKOTONDRAMANANA', prenom='Jean-Baptiste',
                 role='coordinateur', centre='PNLT Antananarivo', actif=True)
    coord.set_password('tbtrack2025')

    medecin = User(email='medecin@crpc.mg', nom='RAZAFIMAHAZO', prenom='Isabelle',
                   role='medecin', centre='CRPC Mahajanga', actif=True)
    medecin.set_password('tbtrack2025')

    infirmier = User(email='infirmier@cdt.mg', nom='RASOLOFO', prenom='Patrick',
                     role='infirmier', centre='CDT Toamasina', actif=True)
    infirmier.set_password('tbtrack2025')

    laborantin = User(email='labo@crpc.mg', nom='RANDRIAMIARANA', prenom='Aina',
                      role='laborantin', centre='CRPC Mahajanga', actif=True)
    laborantin.set_password('tbtrack2025')

    db.session.add_all([coord, medecin, infirmier, laborantin])
    db.session.flush()

    # ── Patients ──────────────────────────────────────────────────
    today = date.today()

    p1 = Patient(
        code_patient='TB-MR-0001', nom='RAKOTO', prenom='Jean-Paul',
        date_naissance=date(1979, 3, 14), sexe='Homme', adresse='Lot II L 45, Antananarivo',
        telephone='034 12 345 67', poids=60.0, statut_vih='negatif',
        date_diagnostic=today - timedelta(days=80), type_resistance='TB-MR',
        categorie='nouveau_cas', statut='en_cours', schema_therapeutique='court',
        date_debut_traitement=today - timedelta(days=55),
        notes_cliniques='Patient coopérant. Conversion bactériologique positive à M2.',
        medecin_id=medecin.id
    )
    p2 = Patient(
        code_patient='TB-MR-0002', nom='RASOA', prenom='Marie-Claire',
        date_naissance=date(1992, 7, 22), sexe='Femme', adresse='Rue du Commerce, Mahajanga',
        telephone='033 98 765 43', poids=52.0, statut_vih='positif',
        date_diagnostic=today - timedelta(days=160), type_resistance='RR-TB',
        categorie='echec_primo', statut='en_cours', schema_therapeutique='long',
        date_debut_traitement=today - timedelta(days=120),
        notes_cliniques='Co-infection VIH. ARV démarrés. Suivi mensuel CD4.',
        medecin_id=medecin.id
    )
    p3 = Patient(
        code_patient='TB-MR-0003', nom='ANDRY', prenom='Fifaliana',
        date_naissance=date(1996, 11, 5), sexe='Homme', adresse='Fokontany Ankadifotsy',
        telephone='032 11 222 33', poids=48.0, statut_vih='negatif',
        date_diagnostic=today - timedelta(days=600), type_resistance='pre-XDR',
        categorie='nouveau_cas', statut='gueri', schema_therapeutique='long',
        date_debut_traitement=today - timedelta(days=560),
        notes_cliniques='Guérison confirmée. Cultures négatives à M6. Suivi post-traitement.',
        medecin_id=medecin.id
    )
    p4 = Patient(
        code_patient='TB-MR-0004', nom='RASOAMAMPIONONA', prenom='Hery',
        date_naissance=date(1969, 4, 30), sexe='Homme', adresse='Quartier Ambohibao',
        telephone='034 44 555 66', poids=70.0, statut_vih='inconnu',
        date_diagnostic=today - timedelta(days=300), type_resistance='TB-MR',
        categorie='rechute_primo', statut='perdu_de_vue', schema_therapeutique='court',
        date_debut_traitement=today - timedelta(days=260),
        notes_cliniques='Interruption de traitement à M3. Adresse actuelle inconnue. Recherche en cours.',
        medecin_id=medecin.id
    )
    p5 = Patient(
        code_patient='TB-MR-0005', nom='NOMENA', prenom='Lalaina',
        date_naissance=date(2005, 9, 18), sexe='Femme', adresse='Lot VK 12, Toliara',
        telephone='038 77 888 99', poids=45.0, statut_vih='negatif',
        date_diagnostic=today - timedelta(days=20), type_resistance='TB-MR',
        categorie='nouveau_cas', statut='en_cours', schema_therapeutique='court',
        date_debut_traitement=today - timedelta(days=15),
        notes_cliniques='Nouveau cas. Phase intensive démarrée. Bonne tolérance initiale.',
        medecin_id=infirmier.id
    )
    p6 = Patient(
        code_patient='TB-MR-0006', nom='RAZAFY', prenom='Bruno',
        date_naissance=date(1961, 12, 2), sexe='Homme', adresse='Cité Mahamasina',
        telephone='034 66 777 88', poids=65.0, statut_vih='positif',
        date_diagnostic=today - timedelta(days=700), type_resistance='XDR',
        categorie='echec_retrait', statut='echec', schema_therapeutique='long',
        date_debut_traitement=today - timedelta(days=650),
        notes_cliniques='XDR-TB. Échec thérapeutique à M8. Passage au schéma de sauvetage discuté en comité.',
        medecin_id=medecin.id
    )
    db.session.add_all([p1, p2, p3, p4, p5, p6])
    db.session.flush()

    # ── Traitements ───────────────────────────────────────────────
    t1 = Traitement(patient_id=p1.id, schema_nom='4Bdq-Mfx-Cfz-Pto-H-Z-E / 2Bdq-Mfx-Cfz-Z-E / 3Mfx-Cfz-Z-E',
                    phase='intensive', date_debut=p1.date_debut_traitement,
                    date_fin_prevue=p1.date_debut_traitement + timedelta(days=270))
    t1.medicaments = ['Bedaquiline', 'Moxifloxacine', 'Clofazimine', 'Prothionamide', 'Isoniazide', 'Pyrazinamide', 'Ethambutol']

    t2 = Traitement(patient_id=p2.id, schema_nom='6Bdq-Lzd-Lfx-Cfz-Cs / 12Lfx-Cfz-Cs',
                    phase='continuation', date_debut=p2.date_debut_traitement,
                    date_fin_prevue=p2.date_debut_traitement + timedelta(days=540))
    t2.medicaments = ['Bedaquiline', 'Linezolide', 'Levofloxacine', 'Clofazimine', 'Cycloserine']

    t5 = Traitement(patient_id=p5.id, schema_nom='4Bdq-Mfx-Cfz-Pto-H-Z-E',
                    phase='intensive', date_debut=p5.date_debut_traitement,
                    date_fin_prevue=p5.date_debut_traitement + timedelta(days=330))
    t5.medicaments = ['Bedaquiline', 'Moxifloxacine', 'Clofazimine', 'Prothionamide', 'Isoniazide', 'Pyrazinamide', 'Ethambutol']

    db.session.add_all([t1, t2, t5])

    # ── Effets secondaires ────────────────────────────────────────
    e1 = EffetSecondaire(
        patient_id=p1.id, medicament_incrimine='Ethambutol',
        symptome='Troubles visuels — baisse d\'acuité visuelle', severite='severe',
        date_declaration=datetime.utcnow() - timedelta(hours=14),
        notifie_crpc=False, declare_par='Inf. RASOLOFO Patrick',
        notes='Ophtalmologue consulté. Arrêt de l\'Ethambutol envisagé.'
    )
    e2 = EffetSecondaire(
        patient_id=p2.id, medicament_incrimine='Prothionamide',
        symptome='Nausées persistantes et vomissements', severite='modere',
        date_declaration=datetime.utcnow() - timedelta(days=2),
        notifie_crpc=True, date_notification=datetime.utcnow() - timedelta(days=1, hours=20),
        declare_par='Dr. RAZAFIMAHAZO Isabelle',
        notes='Prise après repas recommandée. Métoclopramide prescrit.'
    )
    e3 = EffetSecondaire(
        patient_id=p5.id, medicament_incrimine='Pyrazinamide',
        symptome='Intolérance gastrique légère', severite='leger',
        date_declaration=datetime.utcnow() - timedelta(days=3),
        notifie_crpc=True, date_notification=datetime.utcnow() - timedelta(days=2, hours=22),
        declare_par='Inf. RASOLOFO Patrick', notes='Bien toléré après adaptation horaire.'
    )
    e4 = EffetSecondaire(
        patient_id=p6.id, medicament_incrimine='Linezolide',
        symptome='Neuropathie périphérique — engourdissements membres inférieurs', severite='severe',
        date_declaration=datetime.utcnow() - timedelta(days=10),
        notifie_crpc=True, date_notification=datetime.utcnow() - timedelta(days=9, hours=21),
        declare_par='Dr. RAZAFIMAHAZO Isabelle',
        notes='Réduction de dose Linezolide à 300mg. Vitamine B6 ajoutée.'
    )
    db.session.add_all([e1, e2, e3, e4])

    # ── Contacts ─────────────────────────────────────────────────
    c1 = Contact(patient_source_id=p1.id, nom='RAKOTO', prenom='Voahangy', age=42,
                 sexe='Femme', relation='foyer', telephone='034 12 345 68',
                 date_premier_contact=today - timedelta(days=55),
                 statut='en_suivi', date_prochaine_visite=today + timedelta(days=14))
    c2 = Contact(patient_source_id=p1.id, nom='RAKOTO', prenom='Tsiory', age=17,
                 sexe='Homme', relation='foyer', telephone='—',
                 date_premier_contact=today - timedelta(days=55),
                 statut='en_suivi', date_prochaine_visite=today + timedelta(days=14))
    c3 = Contact(patient_source_id=p1.id, nom='RATSIMBA', prenom='Solo', age=48,
                 sexe='Homme', relation='travail', telephone='032 88 000 11',
                 date_premier_contact=today - timedelta(days=50),
                 statut='negatif', date_prochaine_visite=today + timedelta(days=90))
    c4 = Contact(patient_source_id=p2.id, nom='RASOA', prenom='Clarisse', age=28,
                 sexe='Femme', relation='famille', telephone='033 55 444 22',
                 date_premier_contact=today - timedelta(days=120),
                 statut='en_suivi', date_prochaine_visite=today + timedelta(days=7))
    c5 = Contact(patient_source_id=p2.id, nom='RAMIANDRISOA', prenom='Odile', age=58,
                 sexe='Femme', relation='foyer', telephone='033 22 111 33',
                 date_premier_contact=today - timedelta(days=120),
                 statut='tb_mr_confirmee', date_prochaine_visite=today + timedelta(days=3))
    db.session.add_all([c1, c2, c3, c4, c5])

    # ── Stock médicaments ─────────────────────────────────────────
    stocks = [
        Medicament(nom='Levofloxacine', abreviation='Lfx', forme='cp', dosage_unitaire='250 mg',
                   quantite_stock=450, seuil_alerte=200, unite='cp',
                   date_expiration=date(2026, 8, 1), centre='CRPC Mahajanga'),
        Medicament(nom='Moxifloxacine', abreviation='Mfx', forme='cp', dosage_unitaire='400 mg',
                   quantite_stock=280, seuil_alerte=150, unite='cp',
                   date_expiration=date(2026, 6, 15), centre='CRPC Mahajanga'),
        Medicament(nom='Bedaquiline', abreviation='Bdq', forme='cp', dosage_unitaire='100 mg',
                   quantite_stock=140, seuil_alerte=200, unite='cp',
                   date_expiration=date(2026, 4, 30), centre='CRPC Mahajanga'),
        Medicament(nom='Linezolide', abreviation='Lzd', forme='cp', dosage_unitaire='600 mg',
                   quantite_stock=320, seuil_alerte=150, unite='cp',
                   date_expiration=date(2026, 12, 1), centre='CRPC Mahajanga'),
        Medicament(nom='Cycloserine', abreviation='Cs', forme='gel', dosage_unitaire='250 mg',
                   quantite_stock=680, seuil_alerte=300, unite='gel',
                   date_expiration=date(2026, 9, 1), centre='CRPC Mahajanga'),
        Medicament(nom='Clofazimine', abreviation='Cfz', forme='gel', dosage_unitaire='100 mg',
                   quantite_stock=420, seuil_alerte=200, unite='gel',
                   date_expiration=date(2027, 1, 15), centre='CRPC Mahajanga'),
        Medicament(nom='Prothionamide', abreviation='Pto', forme='cp', dosage_unitaire='250 mg',
                   quantite_stock=155, seuil_alerte=200, unite='cp',
                   date_expiration=date(2026, 5, 20), centre='CRPC Mahajanga'),
        Medicament(nom='Pyrazinamide', abreviation='Z', forme='cp', dosage_unitaire='400 mg',
                   quantite_stock=890, seuil_alerte=400, unite='cp',
                   date_expiration=date(2026, 11, 1), centre='CRPC Mahajanga'),
        Medicament(nom='Ethambutol', abreviation='E', forme='cp', dosage_unitaire='400 mg',
                   quantite_stock=650, seuil_alerte=300, unite='cp',
                   date_expiration=date(2026, 10, 1), centre='CRPC Mahajanga'),
        Medicament(nom='PAS (Acide p-amino salicylique)', abreviation='PAS', forme='sachet',
                   dosage_unitaire='4 g', quantite_stock=85, seuil_alerte=100, unite='sachet',
                   date_expiration=date(2026, 7, 1), centre='CRPC Mahajanga'),
        Medicament(nom='Delamanide', abreviation='Dlm', forme='cp', dosage_unitaire='50 mg',
                   quantite_stock=360, seuil_alerte=150, unite='cp',
                   date_expiration=date(2027, 3, 1), centre='CRPC Mahajanga'),
        Medicament(nom='Isoniazide', abreviation='H', forme='cp', dosage_unitaire='300 mg',
                   quantite_stock=780, seuil_alerte=350, unite='cp',
                   date_expiration=date(2026, 8, 15), centre='CRPC Mahajanga'),
    ]
    db.session.add_all(stocks)
    db.session.flush()

    # ── Examens laboratoire ───────────────────────────────────────
    # Patient p1 (TB-MR-0001) — en cours schéma court, 55 jours
    ex1_m0 = ExamenLabo(
        patient_id=p1.id, laborantin_id=laborantin.id, mois_suivi=0,
        date_prelevement=p1.date_debut_traitement - timedelta(days=3),
        date_resultat=p1.date_debut_traitement,
        genexpert_effectue=True, genexpert_resultat='positif',
        genexpert_resistance_rif='detected',
        frottis_effectue=True, frottis_resultat='positif', frottis_quantite='3+',
        culture_effectuee=True, culture_resultat='positif', culture_milieu='LJ+MGIT',
        dst_effectue=True,
        dst_isoniazide='resistant', dst_rifampicine='resistant',
        dst_ethambutol='sensible', dst_pyrazinamide='sensible',
        dst_levofloxacine='sensible', dst_moxifloxacine='sensible',
        dst_bedaquiline='sensible', dst_linezolide='sensible',
        notes='M0 — diagnostic confirmé TB-MR. GeneXpert RIF résistant. DST complet réalisé.'
    )
    ex1_m1 = ExamenLabo(
        patient_id=p1.id, laborantin_id=laborantin.id, mois_suivi=1,
        date_prelevement=p1.date_debut_traitement + timedelta(days=30),
        date_resultat=p1.date_debut_traitement + timedelta(days=32),
        frottis_effectue=True, frottis_resultat='positif', frottis_quantite='1+',
        notes='M1 — frottis encore positif mais charge réduite. Culture en attente.'
    )
    ex1_m2 = ExamenLabo(
        patient_id=p1.id, laborantin_id=laborantin.id, mois_suivi=2,
        date_prelevement=p1.date_debut_traitement + timedelta(days=58),
        date_resultat=p1.date_debut_traitement + timedelta(days=60),
        frottis_effectue=True, frottis_resultat='negatif',
        culture_effectuee=True, culture_resultat='negatif', culture_milieu='MGIT',
        notes='M2 (pivot) — CONVERSION BACTÉRIOLOGIQUE CONFIRMÉE. Cultures négatives. Passage phase continuation.'
    )

    # Patient p2 (TB-MR-0002) — en cours schéma long, 120 jours
    ex2_m0 = ExamenLabo(
        patient_id=p2.id, laborantin_id=laborantin.id, mois_suivi=0,
        date_prelevement=p2.date_debut_traitement - timedelta(days=5),
        date_resultat=p2.date_debut_traitement + timedelta(days=2),
        genexpert_effectue=True, genexpert_resultat='positif',
        genexpert_resistance_rif='detected',
        frottis_effectue=True, frottis_resultat='positif', frottis_quantite='2+',
        culture_effectuee=True, culture_resultat='positif', culture_milieu='LJ',
        dst_effectue=True,
        dst_isoniazide='resistant', dst_rifampicine='resistant',
        dst_ethambutol='resistant', dst_pyrazinamide='sensible',
        dst_levofloxacine='sensible', dst_moxifloxacine='sensible',
        notes='M0 — RR-TB confirmé. Résistance additionnelle à E. Schéma long adapté.'
    )
    ex2_m2 = ExamenLabo(
        patient_id=p2.id, laborantin_id=laborantin.id, mois_suivi=2,
        date_prelevement=p2.date_debut_traitement + timedelta(days=60),
        date_resultat=p2.date_debut_traitement + timedelta(days=65),
        frottis_effectue=True, frottis_resultat='positif', frottis_quantite='scanty',
        culture_effectuee=True, culture_resultat='en_attente', culture_milieu='LJ+MGIT',
        notes='M2 — Frottis encore positif (scanty). Culture en cours (4 semaines LJ).'
    )

    # Patient p5 (TB-MR-0005) — en cours, 15 jours
    ex5_m0 = ExamenLabo(
        patient_id=p5.id, laborantin_id=laborantin.id, mois_suivi=0,
        date_prelevement=p5.date_debut_traitement - timedelta(days=2),
        date_resultat=p5.date_debut_traitement,
        genexpert_effectue=True, genexpert_resultat='positif',
        genexpert_resistance_rif='detected',
        frottis_effectue=True, frottis_resultat='positif', frottis_quantite='2+',
        culture_effectuee=True, culture_resultat='en_attente', culture_milieu='MGIT',
        dst_effectue=False,
        notes='M0 — GeneXpert positif RIF-R. Culture en cours. DST prévu sur culture positive.'
    )

    db.session.add_all([ex1_m0, ex1_m1, ex1_m2, ex2_m0, ex2_m2, ex5_m0])
    db.session.commit()
