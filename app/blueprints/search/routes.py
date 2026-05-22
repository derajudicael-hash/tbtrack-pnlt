from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from ...models import Patient

search_bp = Blueprint('search', __name__, url_prefix='/search')


@search_bp.route('/')
@login_required
def recherche():
    q = request.args.get('q', '').strip()
    resultats = []

    if q and len(q) >= 2:
        # Recherche dans tous les champs pertinents
        terme = f'%{q}%'
        patients_bruts = Patient.query.filter(
            Patient.nom.ilike(terme) |
            Patient.prenom.ilike(terme) |
            Patient.code_patient.ilike(terme) |
            Patient.telephone.ilike(terme) |
            Patient.adresse.ilike(terme)
        ).limit(20).all()

        # Trier par pertinence : correspondance exacte du code_patient d'abord
        def pertinence(p):
            if p.code_patient.lower() == q.lower():
                return 0
            elif p.code_patient.lower().startswith(q.lower()):
                return 1
            elif p.nom.lower() == q.lower() or p.prenom.lower() == q.lower():
                return 2
            else:
                return 3

        resultats = sorted(patients_bruts, key=pertinence)

    # Réponse JSON si requête AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = [
            {
                'id': p.id,
                'code': p.code_patient,
                'nom': f'{p.nom} {p.prenom}',
                'statut': p.statut_label,
                'statut_badge': p.statut_badge,
                'resistance': p.type_resistance or '',
                'url': f'/patients/{p.id}',
            }
            for p in resultats[:10]
        ]
        return jsonify({'resultats': data, 'total': len(data), 'query': q})

    return render_template('search/results.html', resultats=resultats, q=q)
