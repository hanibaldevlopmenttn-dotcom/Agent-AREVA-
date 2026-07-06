/* ===================================
   ARVEA NATURE — script.js
   =================================== */

const WHATSAPP_NUMBER = "21600000000";
const GOOGLE_SHEETS_URL = ""; // Coller ici l'URL de déploiement Google Apps Script

// ── Pré-sélection produit depuis les cartes ──────────────────────────────────
function selectProduct(nomProduit, prix) {
  const select = document.getElementById("produit");
  if (!select) return;

  for (let i = 0; i < select.options.length; i++) {
    const val = select.options[i].value;
    if (val && val.startsWith(nomProduit)) {
      select.value = val;
      break;
    }
  }
  updateWhatsAppLink();
  const commandeSection = document.getElementById("commande");
  if (commandeSection) {
    commandeSection.scrollIntoView({ behavior: "smooth" });
  }
}

// ── Mise à jour du lien WhatsApp dynamique ───────────────────────────────────
function updateWhatsAppLink() {
  const prenom = document.getElementById("prenom")?.value.trim() || "";
  const produitSelect = document.getElementById("produit");
  const produitVal = produitSelect?.value || "";
  const produitNom = produitVal.split("|")[0] || "un produit";
  const prix = produitVal.split("|")[1] || "";
  const ville = document.getElementById("ville")?.value || "";

  let msg = `Bonjour Arvea Nature 🌿\n\nJe souhaite commander :\n`;
  if (prenom) msg += `👤 Prénom : ${prenom}\n`;
  if (produitNom !== "un produit") msg += `📦 Produit : ${produitNom}${prix ? ` (${prix} TND)` : ""}\n`;
  if (ville) msg += `📍 Ville : ${ville}\n`;
  msg += `\nMerci de me recontacter pour finaliser ma commande.`;

  const link = document.getElementById("whatsapp-link");
  if (link) {
    link.href = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(msg)}`;
  }
}

// ── Validation formulaire ─────────────────────────────────────────────────────
function validateForm(data) {
  const errors = [];
  if (!data.prenom || data.prenom.length < 2) errors.push("Prénom requis (min. 2 caractères).");
  if (!data.nom || data.nom.length < 2) errors.push("Nom requis.");
  if (!data.telephone || data.telephone.length < 8) errors.push("Numéro de téléphone invalide.");
  if (!data.ville) errors.push("Veuillez sélectionner votre ville.");
  if (!data.produit) errors.push("Veuillez sélectionner un produit.");
  return errors;
}

// ── Soumission formulaire ─────────────────────────────────────────────────────
async function handleFormSubmit(e) {
  e.preventDefault();

  const form = document.getElementById("commande-form");
  const btnText = document.getElementById("btn-text");
  const btnLoader = document.getElementById("btn-loader");
  const submitBtn = document.getElementById("submit-btn");
  const formError = document.getElementById("form-error");
  const formSuccess = document.getElementById("form-success");

  formError.classList.add("hidden");

  const rawProduit = document.getElementById("produit").value;
  const [produitNom, produitPrix] = rawProduit.split("|");

  const data = {
    prenom: document.getElementById("prenom").value.trim(),
    nom: document.getElementById("nom").value.trim(),
    telephone: document.getElementById("telephone").value.trim(),
    email: document.getElementById("email")?.value.trim() || "",
    ville: document.getElementById("ville").value,
    produit: produitNom || "",
    prix: produitPrix || "",
    quantite: document.getElementById("quantite").value,
    message: document.getElementById("message")?.value.trim() || "",
    date: new Date().toLocaleString("fr-TN", { timeZone: "Africa/Tunis" }),
    source: "site_web",
  };

  const errors = validateForm(data);
  if (errors.length > 0) {
    formError.textContent = "⚠️ " + errors.join(" ");
    formError.classList.remove("hidden");
    return;
  }

  btnText.classList.add("hidden");
  btnLoader.classList.remove("hidden");
  submitBtn.disabled = true;

  try {
    if (GOOGLE_SHEETS_URL && GOOGLE_SHEETS_URL.startsWith("https://")) {
      const response = await fetch(GOOGLE_SHEETS_URL, {
        method: "POST",
        mode: "no-cors",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
    }

    // Redirection WhatsApp de confirmation
    const waMsg =
      `✅ Nouvelle commande — Arvea Nature\n\n` +
      `👤 ${data.prenom} ${data.nom}\n` +
      `📱 ${data.telephone}\n` +
      `📍 ${data.ville}\n` +
      `📦 ${data.produit} × ${data.quantite} = ${(parseFloat(data.prix || 0) * parseInt(data.quantite)).toFixed(2)} TND\n` +
      (data.message ? `💬 ${data.message}\n` : "") +
      `\nDate : ${data.date}`;

    // Afficher le succès
    form.classList.add("hidden");
    formSuccess.classList.remove("hidden");

    // Ouvrir WhatsApp après 800ms
    setTimeout(() => {
      const waLink = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(waMsg)}`;
      window.open(waLink, "_blank");
    }, 800);

  } catch (err) {
    console.error("Erreur soumission:", err);
    formError.textContent = "⚠️ Erreur lors de l'envoi. Essayez via Telegram ou WhatsApp.";
    formError.classList.remove("hidden");
    btnText.classList.remove("hidden");
    btnLoader.classList.add("hidden");
    submitBtn.disabled = false;
  }
}

// ── Reset formulaire ─────────────────────────────────────────────────────────
function resetForm() {
  const form = document.getElementById("commande-form");
  const formSuccess = document.getElementById("form-success");
  const submitBtn = document.getElementById("submit-btn");
  const btnText = document.getElementById("btn-text");
  const btnLoader = document.getElementById("btn-loader");

  form.reset();
  form.classList.remove("hidden");
  formSuccess.classList.add("hidden");
  submitBtn.disabled = false;
  btnText.classList.remove("hidden");
  btnLoader.classList.add("hidden");
  updateWhatsAppLink();
}

// ── Initialisation ────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", function () {
  // Attacher le gestionnaire de formulaire
  const form = document.getElementById("commande-form");
  if (form) {
    form.addEventListener("submit", handleFormSubmit);
  }

  // Mise à jour dynamique du lien WhatsApp
  ["prenom", "produit", "ville"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("change", updateWhatsAppLink);
    if (el) el.addEventListener("input", updateWhatsAppLink);
  });

  // Init lien WhatsApp
  updateWhatsAppLink();

  // Smooth scroll pour les ancres internes
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute("href"));
      if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });

  // Animation d'apparition au scroll (Intersection Observer)
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = "1";
          entry.target.style.transform = "translateY(0)";
        }
      });
    },
    { threshold: 0.1 }
  );

  document.querySelectorAll(".produit-card, .info-card, .contact-card").forEach((el) => {
    el.style.opacity = "0";
    el.style.transform = "translateY(20px)";
    el.style.transition = "opacity 0.5s ease, transform 0.5s ease";
    observer.observe(el);
  });
});
