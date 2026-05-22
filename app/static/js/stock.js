/**
 * stock.js — Gestion du formulaire de mouvement de stock
 * TBTrack v0.2
 */

'use strict';

// stockActuel, seuilAlerte et unite sont injectés par le template

/**
 * Met à jour l'aperçu du stock après le mouvement en temps réel.
 */
function majCalcul() {
  const typeSelect = document.getElementById('typeMouvement');
  const quantiteInput = document.getElementById('quantite');
  const stockApresEl = document.getElementById('stockApres');
  const submitBtn = document.getElementById('submitBtn');
  const preview = document.getElementById('stockPreview');

  if (!typeSelect || !quantiteInput || !stockApresEl) return;

  const type = typeSelect.value;
  const qte = parseInt(quantiteInput.value, 10) || 0;

  let apres;
  if (type === 'entree') {
    apres = stockActuel + qte;
  } else if (['sortie', 'perte', 'expiration'].includes(type)) {
    apres = Math.max(0, stockActuel - qte);
  } else {
    // ajustement — ajoute (peut être négatif si l'utilisateur saisit une valeur négative)
    apres = Math.max(0, stockActuel + qte);
  }

  stockApresEl.textContent = apres + ' ' + unite;

  // Alerte si le stock résultant est inférieur au seuil
  if (preview) {
    if (apres < seuilAlerte && type !== 'entree') {
      preview.classList.remove('alert-secondary');
      preview.classList.add('alert-warning');
      let alertMsg = preview.querySelector('.alert-stock-bas');
      if (!alertMsg) {
        alertMsg = document.createElement('div');
        alertMsg.className = 'alert-stock-bas mt-2 small text-warning fw-bold';
        alertMsg.innerHTML = '<i class="fa fa-triangle-exclamation me-1"></i>Le stock résultant sera inférieur au seuil d\'alerte (' + seuilAlerte + ' ' + unite + ').';
        preview.appendChild(alertMsg);
      }
    } else {
      preview.classList.add('alert-secondary');
      preview.classList.remove('alert-warning');
      const alertMsg = preview.querySelector('.alert-stock-bas');
      if (alertMsg) alertMsg.remove();
    }
  }

  // Confirmation supplémentaire pour les sorties importantes
  if (submitBtn && ['sortie', 'perte', 'expiration'].includes(type)) {
    submitBtn.onclick = function (e) {
      if (qte > stockActuel) {
        e.preventDefault();
        alert('La quantité saisie (' + qte + ') est supérieure au stock disponible (' + stockActuel + ' ' + unite + ').\n\nLe stock sera plafonné à 0.');
        return confirm('Confirmer quand même ce mouvement ?');
      }
      if (apres <= seuilAlerte) {
        return confirm(
          'Attention : ce mouvement fera passer le stock à ' + apres + ' ' + unite +
          ' (seuil d\'alerte : ' + seuilAlerte + ').\n\nConfirmer ?'
        );
      }
      return true;
    };
  } else if (submitBtn) {
    submitBtn.onclick = null;
  }
}

// Initialisation au chargement
document.addEventListener('DOMContentLoaded', function () {
  majCalcul();
});
