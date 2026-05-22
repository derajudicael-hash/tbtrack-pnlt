/**
 * patients.js — Gestion de la fiche patient
 * TBTrack v0.2
 */

'use strict';

// ── Persistance de l'onglet actif ────────────────────────────────────────────

const STORAGE_KEY_TAB = 'tbtrack_patient_tab';

document.addEventListener('DOMContentLoaded', function () {
  // Priorité 1 : hash dans l'URL (vient d'une redirection avec _anchor)
  const hash = window.location.hash;
  // Priorité 2 : onglet sauvegardé en sessionStorage
  const tabToShow = hash || sessionStorage.getItem(STORAGE_KEY_TAB);
  if (tabToShow) {
    const tabLink = document.querySelector('[href="' + tabToShow + '"][data-bs-toggle="tab"]');
    if (tabLink) {
      new bootstrap.Tab(tabLink).show();
    }
  }

  // Sauvegarder l'onglet actif lors du changement
  document.querySelectorAll('[data-bs-toggle="tab"]').forEach(link => {
    link.addEventListener('shown.bs.tab', function (e) {
      sessionStorage.setItem(STORAGE_KEY_TAB, e.target.getAttribute('href'));
    });
  });

  // Validation poids dans les formulaires
  const poidsInput = document.querySelector('input[name="poids"]');
  if (poidsInput) {
    poidsInput.addEventListener('input', function () {
      const val = parseFloat(this.value);
      if (val < 1 || val > 200) {
        this.setCustomValidity('Le poids doit être compris entre 1 et 200 kg.');
      } else {
        this.setCustomValidity('');
      }
    });
  }
});

// ── Confirmation avant suppression patient ────────────────────────────────────

/**
 * Demande confirmation avant de soumettre un formulaire de suppression.
 * @param {string} nom - Nom du patient
 * @returns {boolean}
 */
function confirmerSuppression(nom) {
  return confirm(
    `Supprimer définitivement le patient "${nom}" ?\n\n` +
    'Cette action supprimera également tous les traitements, effets secondaires et contacts associés. ' +
    'Elle est IRRÉVERSIBLE.'
  );
}

// ── Impression de la fiche ────────────────────────────────────────────────────

/**
 * Prépare et lance l'impression de la fiche patient.
 */
function printFiche() {
  // Message d'avertissement avant ouverture boîte de dialogue
  const msg = document.createElement('div');
  msg.id = 'printMsg';
  msg.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
    'background:#000;color:#fff;padding:16px 32px;border-radius:8px;z-index:9999;font-size:14px;';
  msg.textContent = 'Préparation de l\'impression…';
  document.body.appendChild(msg);

  setTimeout(function () {
    document.body.removeChild(msg);
    window.print();
  }, 300);
}
