/**
 * traitements.js — Gestion des médicaments par checkboxes et popovers Bootstrap
 * TBTrack v0.2
 */

'use strict';

/**
 * Formate une liste de médicaments en chaîne lisible.
 * @param {string[]} list
 * @returns {string}
 */
function formatMedicamentsList(list) {
  if (!list || list.length === 0) return 'Aucun médicament sélectionné.';
  return list.join(' · ');
}

/**
 * Met à jour le champ JSON caché et le résumé visuel à partir des cases cochées.
 */
function updateResume() {
  const checkboxes = document.querySelectorAll('.med-checkbox:checked');
  const selected = Array.from(checkboxes).map(cb => cb.value);

  // Mise à jour du champ JSON caché
  const jsonField = document.getElementById('medicamentsJson');
  if (jsonField) {
    jsonField.value = JSON.stringify(selected);
  }

  // Mise à jour du résumé visuel
  const resume = document.getElementById('medicamentsSelectionnes');
  const placeholder = document.getElementById('placeholderAucun');
  if (resume) {
    // Supprimer les anciens badges
    resume.querySelectorAll('.badge-med-selected').forEach(el => el.remove());
    if (selected.length === 0) {
      if (placeholder) placeholder.classList.remove('d-none');
    } else {
      if (placeholder) placeholder.classList.add('d-none');
      selected.forEach(med => {
        const span = document.createElement('span');
        span.className = 'badge bg-success border badge-med-selected';
        span.textContent = med;
        resume.appendChild(span);
      });
    }
  }
}

/**
 * Callback appelé à chaque changement d'une checkbox médicament.
 * @param {HTMLInputElement} cb
 */
function toggleMedicament(cb) {
  const card = cb.closest('.med-checkbox-card');
  if (card) {
    card.classList.toggle('selected', cb.checked);
  }
  updateResume();
}

/**
 * Efface tous les médicaments sélectionnés.
 */
function clearMedicaments() {
  document.querySelectorAll('.med-checkbox').forEach(cb => {
    cb.checked = false;
    const card = cb.closest('.med-checkbox-card');
    if (card) card.classList.remove('selected');
  });
  updateResume();
}

/**
 * Initialise tous les popovers Bootstrap sur la page.
 */
function initPopovers() {
  document.querySelectorAll('[data-bs-toggle="popover"]').forEach(el => {
    new bootstrap.Popover(el);
  });
}

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function () {
  initPopovers();
  updateResume();
});
