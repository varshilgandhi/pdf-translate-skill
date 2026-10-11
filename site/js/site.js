// Varshil's WhatsApp number, country code first, digits only (e.g. "9198xxxxxxxx"). Empty = button stays disabled.
const WA_NUMBER = "918511140115";

document.documentElement.classList.add("js");

const LANGS = [
  { name: "Gujarati", native: "ગુજરાતી", lang: "gu" },
  { name: "Hindi", native: "हिन्दी", lang: "hi" },
  { name: "Marathi", native: "मराठी", lang: "mr" },
  { name: "Tamil", native: "தமிழ்", lang: "ta" },
  { name: "Telugu", native: "తెలుగు", lang: "te" },
  { name: "Bengali", native: "বাংলা", lang: "bn" },
  { name: "Punjabi", native: "ਪੰਜਾਬੀ", lang: "pa" },
  { name: "Arabic", native: "العربية", lang: "ar" },
  { name: "Other", native: "", lang: "" },
];

// Hero accent: the language word cycles through scripts. Reduced motion keeps the first one.
const word = document.getElementById("lang-word");
const cycle = LANGS.filter(l => l.native);
const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
if (!reduce) {
  let i = 0;
  setInterval(() => {
    if (document.hidden) return;
    word.classList.add("out");
    setTimeout(() => {
      i = (i + 1) % cycle.length;
      word.textContent = cycle[i].native;
      word.lang = cycle[i].lang;
      word.classList.remove("out");
    }, 320);
  }, 2200);
}

// Picker -> WhatsApp message
const chips = document.getElementById("chips");
const otherWrap = document.getElementById("other-wrap");
const other = document.getElementById("other");
const what = document.getElementById("what");
const preview = document.getElementById("preview");
const send = document.getElementById("send");
const sendNote = document.getElementById("send-note");
let chosen = LANGS[0];

LANGS.forEach((l, idx) => {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "chip";
  b.setAttribute("aria-pressed", idx === 0 ? "true" : "false");
  b.innerHTML = l.native ? `${l.name}<span class="native" lang="${l.lang}">${l.native}</span>` : l.name;
  b.addEventListener("click", () => {
    chips.querySelectorAll(".chip").forEach(c => c.setAttribute("aria-pressed", "false"));
    b.setAttribute("aria-pressed", "true");
    chosen = l;
    otherWrap.hidden = l.name !== "Other";
    if (l.name === "Other") other.focus();
    update();
  });
  chips.appendChild(b);
});

function message() {
  const lang = chosen.name === "Other" ? (other.value.trim() || "[language]") : chosen.name;
  const about = what.value.trim();
  return `Hi Varshil, could you convert a PDF into ${lang} for me?` +
    (about ? `\nIt's ${about.replace(/^(it'?s|it is)\s+/i, "")}.` : "") +
    `\nI'll attach it here.`;
}

function update() {
  const text = message();
  preview.textContent = text;
  if (WA_NUMBER) {
    send.href = `https://wa.me/${WA_NUMBER}?text=${encodeURIComponent(text)}`;
    send.removeAttribute("aria-disabled");
  } else {
    send.href = "#";
    send.setAttribute("aria-disabled", "true");
    sendNote.textContent = "WhatsApp link coming soon.";
  }
}
other.addEventListener("input", update);
what.addEventListener("input", update);
update();

// Reveal on arrival
const io = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (!e.isIntersecting) return;
    const el = e.target;
    const sibs = [...el.parentElement.querySelectorAll(":scope > .reveal")];
    el.style.transitionDelay = `${Math.min(sibs.indexOf(el), 5) * 50}ms`;
    el.classList.add("in");
    io.unobserve(el);
  });
}, { rootMargin: "0px 0px -15% 0px" });
document.querySelectorAll(".reveal").forEach(el => io.observe(el));
