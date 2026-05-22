from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from .calculateur import calculer_doses, SCHEMAS

dosage_bp = Blueprint('dosage', __name__, url_prefix='/dosage')


@dosage_bp.route('/', methods=['GET', 'POST'])
@login_required
def calculateur():
    resultat = None
    if request.method == 'POST':
        try:
            poids = float(request.form.get('poids', 0))
            adulte = request.form.get('groupe_age') == 'adulte'
            schema = request.form.get('schema', 'court_nouveau')
            resultat = calculer_doses(poids, adulte, schema)
        except (ValueError, TypeError):
            pass
    return render_template('dosage/calculateur.html', schemas=SCHEMAS, resultat=resultat)
