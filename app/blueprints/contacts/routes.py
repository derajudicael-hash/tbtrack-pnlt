from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from ...models import Contact, Patient
from ...extensions import db
from .forms import ContactForm
from ...utils.decorators import role_required
from datetime import date, timedelta

contacts_bp = Blueprint('contacts', __name__, url_prefix='/contacts')


@contacts_bp.route('/')
@login_required
def liste():
    q      = request.args.get('q', '').strip()
    filtre = request.args.get('filtre', '')
    today  = date.today()

    query = Contact.query
    if q:
        query = query.filter(
            Contact.nom.ilike(f'%{q}%') |
            Contact.prenom.ilike(f'%{q}%') |
            Contact.telephone.ilike(f'%{q}%')
        )
    contacts     = query.order_by(Contact.date_prochaine_visite.asc()).all()
    urgents      = [c for c in contacts
                    if c.date_prochaine_visite and c.date_prochaine_visite <= today + timedelta(days=7)
                    and c.statut == 'en_suivi']
    tb_confirmes = [c for c in contacts if c.statut == 'tb_mr_confirmee']

    return render_template('contacts/liste.html',
        contacts=contacts, urgents=urgents, tb_confirmes=tb_confirmes,
        today=today, q=q, filtre=filtre)


@contacts_bp.route('/ajouter', methods=['GET', 'POST'])
@login_required
@role_required('coordinateur', 'medecin', 'infirmier')
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
    contact = db.get_or_404(Contact, contact_id)
    return render_template('contacts/fiche.html', contact=contact, today=date.today())


@contacts_bp.route('/<int:contact_id>/modifier', methods=['GET', 'POST'])
@login_required
@role_required('coordinateur', 'medecin', 'infirmier')
def modifier(contact_id):
    contact = db.get_or_404(Contact, contact_id)
    form = ContactForm(obj=contact)
    patients = Patient.query.order_by(Patient.nom, Patient.prenom).all()
    form.patient_source_id.choices = [(p.id, f'{p.code_patient} — {p.nom} {p.prenom} ({p.statut_label})')
                                      for p in patients]
    if form.validate_on_submit():
        form.populate_obj(contact)
        contact.nom = contact.nom.upper()
        db.session.commit()
        flash('Contact mis à jour.', 'success')
        return redirect(url_for('contacts.fiche', contact_id=contact_id))
    return render_template('contacts/modifier.html', form=form, contact=contact)


@contacts_bp.route('/<int:contact_id>/supprimer', methods=['POST'])
@login_required
@role_required('coordinateur', 'medecin')
def supprimer(contact_id):
    contact = db.get_or_404(Contact, contact_id)
    db.session.delete(contact)
    db.session.commit()
    flash('Contact supprimé.', 'info')
    return redirect(url_for('contacts.liste'))
