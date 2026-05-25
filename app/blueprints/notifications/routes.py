from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from ...models import Notification
from ...extensions import db

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/')
@login_required
def centre():
    notifs = (Notification.query
              .filter_by(user_id=current_user.id)
              .order_by(Notification.lue.asc(), Notification.created_at.desc())
              .all())
    nb_non_lues = sum(1 for n in notifs if not n.lue)
    return render_template('notifications/centre.html',
                           notifs=notifs,
                           nb_non_lues=nb_non_lues)


@notifications_bp.route('/<int:notif_id>/lire', methods=['POST'])
@login_required
def marquer_lue(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.id:
        return '', 403
    notif.lue = True
    db.session.commit()
    # Si la notification a une URL cible, y rediriger
    retour = notif.url or url_for('notifications.centre')
    return redirect(retour)


@notifications_bp.route('/tout-lire', methods=['POST'])
@login_required
def tout_lire():
    (Notification.query
     .filter_by(user_id=current_user.id, lue=False)
     .update({'lue': True}))
    db.session.commit()
    return redirect(url_for('notifications.centre'))


@notifications_bp.route('/<int:notif_id>/supprimer', methods=['POST'])
@login_required
def supprimer(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.id:
        return '', 403
    db.session.delete(notif)
    db.session.commit()
    return redirect(url_for('notifications.centre'))
