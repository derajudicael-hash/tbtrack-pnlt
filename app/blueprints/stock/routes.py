from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ...models import Medicament, MouvementStock
from ...extensions import db
from .forms import MouvementForm, MedicamentForm

stock_bp = Blueprint('stock', __name__, url_prefix='/stock')


@stock_bp.route('/')
@login_required
def inventaire():
    medicaments = Medicament.query.order_by(Medicament.quantite_stock.asc()).all()
    alerts = [m for m in medicaments if m.stock_bas or m.expire_bientot]
    return render_template('stock/inventaire.html', medicaments=medicaments, alerts=alerts)


@stock_bp.route('/ajouter', methods=['GET', 'POST'])
@login_required
def ajouter():
    form = MedicamentForm()
    if form.validate_on_submit():
        med = Medicament(
            nom=form.nom.data,
            abreviation=form.abreviation.data,
            forme=form.forme.data,
            dosage_unitaire=form.dosage_unitaire.data,
            quantite_stock=form.quantite_stock.data or 0,
            seuil_alerte=form.seuil_alerte.data,
            date_expiration=form.date_expiration.data,
            centre=form.centre.data,
        )
        db.session.add(med)
        db.session.commit()
        flash(f'Médicament "{med.nom}" ajouté au stock.', 'success')
        return redirect(url_for('stock.inventaire'))
    return render_template('stock/medicament_form.html', form=form, titre='Ajouter un médicament')


@stock_bp.route('/<int:med_id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier(med_id):
    med = Medicament.query.get_or_404(med_id)
    form = MedicamentForm(obj=med)
    if form.validate_on_submit():
        form.populate_obj(med)
        db.session.commit()
        flash(f'Médicament "{med.nom}" mis à jour.', 'success')
        return redirect(url_for('stock.inventaire'))
    return render_template('stock/medicament_form.html', form=form, titre='Modifier le médicament', med=med)


@stock_bp.route('/<int:med_id>/mouvement', methods=['GET', 'POST'])
@login_required
def mouvement(med_id):
    med = Medicament.query.get_or_404(med_id)
    form = MouvementForm()
    if form.validate_on_submit():
        qte = form.quantite.data
        type_mv = form.type_mouvement.data
        qte_avant = med.quantite_stock

        # Calcul de la nouvelle quantité selon le type
        if type_mv == 'entree':
            qte_apres = qte_avant + qte
        elif type_mv in ('sortie', 'perte', 'expiration'):
            qte_apres = max(0, qte_avant - qte)
        else:  # ajustement
            qte_apres = max(0, qte_avant + qte)

        # Enregistrement du mouvement
        mv = MouvementStock(
            medicament_id=med_id,
            type_mouvement=type_mv,
            quantite=qte,
            quantite_avant=qte_avant,
            quantite_apres=qte_apres,
            utilisateur_id=current_user.id,
            reference_bon=form.reference_bon.data,
            motif=form.motif.data,
        )
        med.quantite_stock = qte_apres
        db.session.add(mv)
        db.session.commit()
        flash(f'Mouvement enregistré : {mv.type_label} de {qte} {med.unite}. '
              f'Stock : {qte_avant} → {qte_apres} {med.unite}.', 'success')
        return redirect(url_for('stock.historique', med_id=med_id))

    mouvements = MouvementStock.query.filter_by(
        medicament_id=med_id
    ).order_by(MouvementStock.date_mouvement.desc()).limit(10).all()

    return render_template('stock/mouvement.html', form=form, med=med, mouvements=mouvements)


@stock_bp.route('/<int:med_id>/historique')
@login_required
def historique(med_id):
    med = Medicament.query.get_or_404(med_id)
    mouvements = MouvementStock.query.filter_by(
        medicament_id=med_id
    ).order_by(MouvementStock.date_mouvement.desc()).all()
    return render_template('stock/historique.html', med=med, mouvements=mouvements)


@stock_bp.route('/<int:med_id>/supprimer', methods=['POST'])
@login_required
def supprimer(med_id):
    med = Medicament.query.get_or_404(med_id)
    if med.mouvements:
        flash(f'Impossible de supprimer "{med.nom}" : il a un historique de mouvements.', 'danger')
        return redirect(url_for('stock.inventaire'))
    db.session.delete(med)
    db.session.commit()
    flash(f'Médicament "{med.nom}" supprimé.', 'success')
    return redirect(url_for('stock.inventaire'))


# Route rétro-compatible avec l'ancien système delta +/-
@stock_bp.route('/<int:med_id>/ajuster', methods=['POST'])
@login_required
def ajuster_stock(med_id):
    med = Medicament.query.get_or_404(med_id)
    try:
        delta = int(request.form.get('delta', 0))
        if delta == 0:
            flash('Aucune modification : delta de 0.', 'warning')
            return redirect(url_for('stock.inventaire'))
        qte_avant = med.quantite_stock
        med.quantite_stock = max(0, med.quantite_stock + delta)
        type_mv = 'entree' if delta > 0 else 'sortie'
        mv = MouvementStock(
            medicament_id=med_id,
            type_mouvement=type_mv,
            quantite=abs(delta),
            quantite_avant=qte_avant,
            quantite_apres=med.quantite_stock,
            utilisateur_id=current_user.id,
            motif='Ajustement rapide depuis inventaire',
        )
        db.session.add(mv)
        db.session.commit()
        flash(f'Stock de {med.nom} mis à jour : {med.quantite_stock} {med.unite}', 'success')
    except ValueError:
        flash('Valeur invalide.', 'danger')
    return redirect(url_for('stock.inventaire'))
