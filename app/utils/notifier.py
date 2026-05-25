"""
Utilitaires de création de notifications in-app.
Toutes les fonctions ajoutent à la session SQLAlchemy sans commiter —
c'est au code appelant de faire db.session.commit() après.
"""
from ..extensions import db


def notifier_roles(roles, message, type_notif='info', url=None, ref=None):
    """Crée une notification pour tous les utilisateurs actifs des rôles listés.

    Si `ref` est fourni, on ne crée pas de doublon si une notification non lue
    avec la même ref existe déjà pour cet utilisateur.
    """
    from ..models import User, Notification

    utilisateurs = User.query.filter(
        User.role.in_(roles),
        User.actif == True,
    ).all()

    for u in utilisateurs:
        if ref:
            existante = Notification.query.filter_by(
                user_id=u.id, ref=ref, lue=False
            ).first()
            if existante:
                continue
        notif = Notification(
            user_id=u.id,
            message=message,
            type_notif=type_notif,
            url=url,
            ref=ref,
        )
        db.session.add(notif)


def notifier_user(user_id, message, type_notif='info', url=None, ref=None):
    """Crée une notification pour un utilisateur précis.

    Si `ref` est fourni, vérifie l'absence de doublon non lu avant de créer.
    """
    from ..models import Notification

    if ref:
        existante = Notification.query.filter_by(
            user_id=user_id, ref=ref, lue=False
        ).first()
        if existante:
            return

    notif = Notification(
        user_id=user_id,
        message=message,
        type_notif=type_notif,
        url=url,
        ref=ref,
    )
    db.session.add(notif)
