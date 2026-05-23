from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from ...models import Contact, Patient
from ...extensions import db
from .forms import ContactForm
from datetime import date

contacts_bp = Blueprint('contacts', __name__, url_prefix='/contacts')


@contacts_bp.route('/')
@login_required
def liste():
    contacts = Contact.query.order_by(Contact.date_prochaine_visite.asc()).all()
    return render_template('contacts/liste.html', contacts=contacts, today=date.today())


@contacts_bp.route('/ajouter', methods=['GET', 'POST'])
@login_required
def ajouter():
    form = ContactForm()
    # Tous les patients — un contact peut être lié à n'importe quel cas index
    patients = Patient.query.order_by(Patient.nom, Patient.prenom).all()
    form.patient_source_id.choices = [(p.id, f'{p.code_patient} — {p.nom} {p.prenom} ({p.statut_label})')
                                      for p in patients]

    # retour_patient_id : GET ou POST échoué
    patient_source_id_param = (request.args.get('patient_source_id', type=int)
                               or request.form.get('retour_patient_id', type=int))
    if request.method == 'GET' and patient_source_id_param:
        form.patient_source_id.data = patient_source_id_param

    if form.validate_on_submit():
        contact = Contact(
            patient_source_id=form.patient_source_id.data,
            nom=form.nom.data.upper(),
            prenom=form.prenom.data,
            age=form.age.data,
            sexe=form.sexe.data,
            relation=form.relation.data,
            telephone=form.telephone.data,
            date_prochaine_visite=form.date_prochaine_visite.data,
            statut=form.statut.data,
            notes=form.notes.data,
            date_depistage=form.date_depistage.data,
            resultat_genexpert=form.resultat_genexpert.data,
            radiographie_thorax=form.radiographie_thorax.data,
            ipt_propose=form.ipt_propose.data,
            ipt_accepte=form.ipt_accepte.data,
            date_prochain_controle=form.date_prochain_controle.data,
        )
        db.session.add(contact)
        db.session.commit()
        flash('Contact enregistré. Suivi sur 2 ans démarré.', 'success')
        # Retour à la fiche patient si on venait de là
        pid = request.form.get('retour_patient_id', type=int)
        if pid:
            return redirect(url_for('patients.fiche', patient_id=pid, _anchor='tab-contacts'))
        return redirect(url_for('contacts.liste'))
    return render_template('contacts/ajouter.html', form=form,
                           retour_patient_id=patient_source_id_param)


@contacts_bp.route('/<int:contact_id>')
@login_required
def fiche(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    return render_template('contacts/fiche.html', contact=contact, today=date.today())


@contacts_bp.route('/<int:contact_id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    form = ContactForm(obj=contact)
    patients = Patient.query.order_by(Patient.nom, Patient.prenom).all()
    form.patient_source_id.choices = [(p.id, f'{p.code_patient} — {p.nom} {p.prenom} ({p.statut_label})')
                                      for p in patients]
    if form.validate_on_submit():
        contact.patient_source_id = form.patient_source_id.data
        contact.nom = form.nom.data.upper()
        contact.prenom = form.prenom.data
        contact.age = form.age.data
        contact.sexe = form.sexe.data
        contact.relation = form.relation.data
        contact.telephone = form.telephone.data
        contact.date_prochaine_visite = form.date_prochaine_visite.data
        contact.statut = form.statut.data
        contact.notes = form.notes.data
        contact.date_depistage = form.date_depistage.data
        contact.resultat_genexpert = form.resultat_genexpert.data
        contact.radiographie_thorax = form.radiographie_thorax.data
        contact.ipt_propose = form.ipt_propose.data
        contact.ipt_accepte = form.ipt_accepte.data
        contact.date_prochain_controle = form.date_prochain_controle.data
        db.session.commit()
        flash('Contact mis à jour.', 'success')
        return redirect(url_for('contacts.liste'))
    return render_template('contacts/modifier.html', form=form, contact=contact)


@contacts_bp.route('/<int:contact_id>/supprimer', methods=['POST'])
@login_required
def supprimer(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    db.session.delete(contact)
    db.session.commit()
    flash('Contact supprimé.', 'info')
    return redirect(url_for('contacts.liste'))
