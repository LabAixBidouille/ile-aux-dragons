#!/usr/bin/env python3
"""Construit index.html à partir de source/texte.md.

Le moteur Harlowe (repris au départ du site de La Lune de Rambo, puis de Violette et Patate) est
conservé tel quel dans index.html : seules les pages et la feuille de style du livre sont régénérées.

Usage, depuis la racine du dépôt : python3 source/construire_site.py
"""
import html
import re
import uuid
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
TEXTE = RACINE / "source" / "texte.md"
SORTIE = RACINE / "index.html"
NOINDEX = '<meta name="robots" content="noindex, nofollow, noarchive">'
# Favicon : l'œuf de dragon
FAVICON = ('<link rel="icon" type="image/png" sizes="48x48" href="images/favicon-48.png">'
           '<link rel="icon" type="image/png" sizes="180x180" href="images/favicon.png">'
           '<link rel="apple-touch-icon" href="images/favicon.png">')

TITRE = "L'île aux dragons"
AUTRICES = "Louisa et June"

# Résumé provisoire, à remplacer par celui de Manon
SYNOPSIS = (
    "Anna a quatorze ans, une tuque rouge et une crosse de hockey dont elle ne se sépare jamais. "
    "Quand sa grand-mère l'invite à passer l'hiver sur l'île où elle est née, elle quitte la neige "
    "de Montréal pour une terre que les cartes ne montrent pas.\n\n"
    "Là-bas, les dragons vivent enchaînés, un sorcier règne depuis son château noir, et le dernier "
    "dragon libre, Croquemou, déteste les humains. Anna avait promis de ne rien changer… "
    "Lance le dé et découvre si elle tiendra sa promesse !"
)

# Texte écrit par Manon le 03/11/2026, modèle commun aux livres de l'atelier : seuls les noms et la
# phrase sur le genre changent
CONTEXTE = [
    "En octobre 2026, le L.A.B a animé l’atelier « La quête du curry, une histoire dont tu es le héros » "
    "dans les bibliothèques Méjanes d’Aix-en-Provence. Les enfants ont été accompagnés dans la création "
    "d’un récit complet, depuis l’invention des personnages jusqu’à la construction d’une intrigue "
    "reliant les différentes étapes de leur aventure.",
    "Nous leur avons proposé d’introduire une part de hasard dans leur récit. Le résultat d’un lancer de "
    "dé pouvait modifier le déroulement de certains passages et conduire le lecteur vers un chapitre ou "
    "un autre.",
    "Les enfants ont ainsi exploré, sans écran, des notions liées à la pensée computationnelle, une "
    "manière de décomposer un problème et d’organiser les étapes pour le résoudre. Ils ont formulé des "
    "règles de type « si… alors… », créé des embranchements et réfléchi à la façon dont les chemins se "
    "rejoignent pour former une histoire cohérente.",
    "Louisa et June ont choisi d’inventer une histoire fantastique. Un défi pour une histoire à "
    "embranchements, puisque le monde imaginaire doit garder ses règles et sa cohérence, quel que soit "
    "le chemin emprunté.",
    "L’atelier ne durant que deux heures, nous tenions à offrir à chaque enfant un livre complet pour "
    "illustrer leur travail et les rendre fiers de leurs productions. Le L.A.B a donc prolongé et mis en "
    "forme leur récit à l’aide d’outils numériques (l’intelligence artificielle a notamment permis "
    "d’aboutir à une histoire achevée et à un ensemble de visuels correspondant à leurs descriptions mais "
    "uniformes tout au long de la lecture).\n\n<b>À son origine, il y a avant tout les idées et les "
    "personnages de Louisa et de June.</b>",
]
# Une phrase de leur fiche récit, à peine remise au propre
CITATION = ("Anna affronte le sorcier. Grâce à son intelligence et son habileté, elle arrive à libérer "
            "les dragons.")

CSS = """
@font-face { font-family: "Cinzel"; font-weight: 400 900; font-display: swap; src: url("fonts/Cinzel.woff2") format("woff2"); }
@font-face { font-family: "Marcellus"; font-display: swap; src: url("fonts/Marcellus.woff2") format("woff2"); }
/* Dans Cinzel et Marcellus, le 1 ressemble à un I : les chiffres sont pris dans Lora */
@font-face { font-family: "Cinzel"; font-display: swap; src: url("fonts/Lora.woff2") format("woff2"); unicode-range: U+0030-0039; }
@font-face { font-family: "Marcellus"; font-display: swap; src: url("fonts/Lora.woff2") format("woff2"); unicode-range: U+0030-0039; }
@font-face { font-family: "Lora"; font-style: normal; font-weight: 400 700; font-display: swap; src: url("fonts/Lora.woff2") format("woff2"); }
@font-face { font-family: "Lora"; font-style: italic; font-weight: 400 700; font-display: swap; src: url("fonts/Lora-i.woff2") format("woff2"); }
@font-face { font-family: "Nunito"; font-style: normal; font-weight: 400 800; font-display: swap; src: url("fonts/Nunito.woff2") format("woff2"); }

/* « Braise et neige » : la nuit bleue de l'île pour la couverture et le moment du tirage, la page
   blanche pour la lecture, l'or et la braise de Croquemou pour les titres et les lueurs */
:root {
  --nuit: #24305a;
  --nuit-fonce: #18203d;
  --nuit-clair: #3b4f86;
  --or: #f2b25b;
  --or-clair: #ffe1a8;
  --or-fonce: #b9692a;
  --braise: #e0782f;
  --encre: #2a2c3d;
  --gris: #6a6e80;
  --papier: #ffffff;
}
html, body, tw-story { background-color: var(--papier); color: var(--encre); }
tw-story {
  font-family: "Lora", Georgia, serif;
  font-size: 1.04em;
  line-height: 1.75;
  padding: 4em 1.25em 4em;
}
tw-passage { max-width: 1180px; margin: 0 auto; }

/* Pages de lecture : le texte à gauche, l'illustration à droite, qui suit le défilement */
.page {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
  gap: 2.8em;
  align-items: start;
}
.cote { position: sticky; top: 1.5em; margin-top: 2.5em; }
.illustration { display: flex; flex-direction: column; gap: 1.4em; }
.halo { display: block; }
.illustration img {
  display: block;
  width: 100%;
  max-height: 88vh;
  object-fit: contain;
  border-radius: 10px;
  box-shadow: 0 0 0 1px rgba(224, 138, 51, 0.55), 0 0 36px -6px rgba(242, 178, 91, 0.6);
}
.page:not(:has(.cote)) { grid-template-columns: minmax(0, 40em); justify-content: center; }
@media (max-width: 800px) {
  .page { grid-template-columns: minmax(0, 1fr); gap: 1.4em; }
  .cote { position: static; order: -1; margin-top: 0; }
}
tw-sidebar { display: none; }
tw-story { overflow: clip; }

/* Titres de chapitre : le numéro en petites capitales dorées, le titre gravé en bleu nuit */
.chapitre { font-size: 1em; font-weight: 400; margin: 0 0 1.1em; line-height: 1.1; }
.chapitre .numero {
  display: block;
  font-family: "Marcellus", Georgia, serif;
  font-size: 0.88em;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--or-fonce);
  margin-bottom: 0.4em;
}
.chapitre .titre {
  display: block;
  font-family: "Cinzel", Georgia, serif;
  font-weight: 500;
  font-size: 2.1em;
  color: var(--nuit);
}

/* Page de garde : la seule page sur fond de nuit */
html:has(.garde), html:has(.garde) body, tw-story:has(.garde) {
  background: radial-gradient(ellipse at 70% 0%, var(--nuit-clair) 0%, var(--nuit) 45%, var(--nuit-fonce) 100%) fixed;
  color: #eef1fb;
}
tw-story:has(.garde) { padding-top: 1em; padding-bottom: 1em; }
.garde {
  min-height: calc(100vh - 2.2em);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: clamp(0.8em, 3vh, 2em);
}
.garde-entete { display: flex; flex-direction: column; align-items: center; text-align: center; }
.garde-corps {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(24em, 1fr);
  gap: 3.2em;
  align-items: center;
  width: 100%;
  max-width: 1140px;
  margin: 0 auto;
}
.garde-image img {
  display: block;
  width: 100%;
  height: auto;
  border-radius: 10px;
  box-shadow: 0 0 0 1px rgba(242, 178, 91, 0.5), 0 0 40px -6px rgba(242, 178, 91, 0.45);
}
.garde-texte { display: flex; flex-direction: column; gap: clamp(1.1em, 3.4vh, 1.9em); text-align: center; }
@media (max-width: 800px) {
  .garde { min-height: 0; }
  .garde-corps { grid-template-columns: minmax(0, 1fr); gap: 1.6em; }
}
.garde .surtitre {
  font-family: "Marcellus", Georgia, serif;
  font-size: 0.88em;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #b9c4e6;
}
/* Titre doré qui luit dans la nuit */
.garde .grand-titre {
  font-family: "Cinzel", Georgia, serif;
  font-weight: 500;
  font-size: clamp(2.4em, 8vh, 4.4em);
  line-height: 1.05;
  background: linear-gradient(180deg, #fff3d0, var(--or) 60%, var(--braise));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  filter: drop-shadow(0 0 18px rgba(242, 178, 91, 0.45));
  margin: 0.25em 0 0.2em;
}
.garde .nom-auteur {
  font-family: "Marcellus", Georgia, serif;
  font-size: clamp(1.2em, 3.4vh, 1.5em);
  letter-spacing: 0.12em;
  color: var(--or);
}
.garde .synopsis { margin: 0 auto; max-width: 38em; font-size: 1.02em; line-height: 1.75; color: #dfe4f5; }
/* Commencer : un bouton d'or qui luit */
.garde .commencer tw-link, .garde .commencer .enchantment-link {
  display: inline-block;
  font-family: "Marcellus", Georgia, serif;
  font-weight: 400;
  font-size: 1.3em;
  letter-spacing: 0.1em;
  color: #1a2244;
  background: linear-gradient(180deg, #ffd890, #f0a04b);
  padding: 0.5em 1.8em;
  border-radius: 6px;
  box-shadow: 0 0 24px rgba(240, 160, 75, 0.55);
  transition: box-shadow 0.2s ease;
}
.garde .commencer tw-link:hover, .garde .commencer .enchantment-link:hover {
  color: #1a2244;
  box-shadow: 0 0 34px 6px rgba(240, 160, 75, 0.7);
}
.garde .secondaires { display: flex; flex-wrap: wrap; justify-content: center; gap: 0.8em 1.4em; }

/* Petits boutons secondaires : un liseré d'or */
.secondaires tw-link, .secondaires .enchantment-link {
  display: inline-block;
  font-family: "Marcellus", Georgia, serif;
  font-weight: 400;
  font-size: 1em;
  letter-spacing: 0.06em;
  color: var(--nuit);
  border: 1px solid var(--or);
  border-radius: 6px;
  padding: 0.3em 1.1em;
  background: var(--papier);
  transition: box-shadow 0.2s ease;
}
.secondaires tw-link:hover, .secondaires .enchantment-link:hover { color: var(--nuit); box-shadow: 0 0 16px rgba(242, 178, 91, 0.5); }
.garde .secondaires tw-link, .garde .secondaires .enchantment-link { color: var(--or-clair); background: transparent; border-color: rgba(242, 178, 91, 0.6); }
.garde .secondaires tw-link:hover, .garde .secondaires .enchantment-link:hover { color: #fff; }

/* Lien Couverture */
.retour { margin: 0 auto 1.2em; text-align: left; }
.retour tw-link, .retour .enchantment-link,
.lien-retour tw-link, .lien-retour .enchantment-link {
  font-family: "Marcellus", Georgia, serif;
  font-weight: 400;
  font-size: 0.9em;
  letter-spacing: 0.06em;
  color: var(--gris);
}
.retour tw-link::before, .lien-retour tw-link::before { content: "← "; }
.retour tw-link:hover, .lien-retour tw-link:hover { color: var(--or-fonce); }

/* Le moment du tirage : un encart de nuit sur la page blanche, la consigne, les choix et l'œuf */
.de {
  display: flex;
  align-items: center;
  gap: 1.6em;
  margin-top: 0.4em;
  padding: 1.3em 1.6em;
  border-radius: 12px;
  background: radial-gradient(ellipse at 80% 0%, var(--nuit-clair), var(--nuit) 55%, var(--nuit-fonce));
  color: #eef1fb;
  box-shadow: 0 10px 26px -12px rgba(24, 32, 61, 0.7);
}
.de-texte { flex: 1; min-width: 0; }
.de .consigne {
  display: block;
  font-style: italic;
  font-size: 1.12em;
  line-height: 1.45;
  color: var(--or-clair);
  margin-bottom: 0.6em;
}
.choix { display: flex; flex-direction: column; align-items: flex-start; gap: 0.45em; }
.choix tw-link, .choix .enchantment-link {
  color: var(--nuit);
  font-weight: 600;
  border-bottom: 1px solid rgba(224, 120, 47, 0.6);
}
.choix tw-link:hover, .choix .enchantment-link:hover { color: var(--braise); }
.de .choix tw-link, .de .choix .enchantment-link { color: #fff; border-bottom-color: rgba(242, 178, 91, 0.6); }
.de .choix tw-link:hover, .de .choix .enchantment-link:hover { color: var(--or); }
.choix .relance { font-style: italic; color: var(--gris); }
.de .choix .relance { color: #b9c4e6; }
.suite { margin-top: 0.8em; }

/* Séparateur : une étincelle dorée entre deux traits qui s'effacent */
.separateur { display: flex; align-items: center; justify-content: center; gap: 0.7em; margin: 1.6em 0 1.2em; }
.separateur::before, .separateur::after { content: ""; width: 5.5em; height: 1px; background: linear-gradient(to right, transparent, var(--or)); }
.separateur::after { background: linear-gradient(to left, transparent, var(--or)); }
.separateur .embleme {
  width: 1em;
  height: 1em;
  background: radial-gradient(circle, #fff3d0 0 20%, var(--or) 45%, transparent 70%);
  filter: drop-shadow(0 0 6px rgba(242, 178, 91, 0.9));
}
.garde .separateur { margin: 0; }

/* Renvoi seul : un bouton blanc au liseré d'or */
.elan { align-items: center; margin-top: 2.2em; }
.choix.elan tw-link, .choix.elan .enchantment-link {
  display: inline-block;
  font-family: "Marcellus", Georgia, serif;
  font-weight: 400;
  font-size: 1.1em;
  letter-spacing: 0.08em;
  color: var(--nuit);
  background: var(--papier);
  border: 1px solid var(--or);
  border-radius: 6px;
  padding: 0.45em 1.4em;
  box-shadow: 0 0 16px rgba(242, 178, 91, 0.35);
  transition: box-shadow 0.2s ease;
}
.choix.elan tw-link:hover, .choix.elan .enchantment-link:hover { color: var(--nuit); box-shadow: 0 0 26px 4px rgba(242, 178, 91, 0.55); }

/* L'œuf de dragon de Manon : il tremble, éclot et laisse voir le nombre tiré. L'image est carrée et
   l'œuf est en son centre : il est centré dans sa colonne et dans la hauteur de l'encart. Le résultat
   écrit n'est lu que par les lecteurs d'écran. */
.lancer { flex: none; width: 7em; align-self: stretch; display: flex; align-items: center; justify-content: center; }
.oeuf {
  position: relative;
  width: 7em;
  height: 7em;
  margin: -0.8em 0;
  padding: 0;
  border: none;
  background: none;
  font: inherit;
  cursor: pointer;
}
.oeuf .coque {
  position: absolute;
  inset: 0;
  background: url("images/oeuf.png") no-repeat center / contain;
  transition: transform 0.5s ease, opacity 0.5s ease, filter 0.2s ease;
}
.oeuf:hover .coque { filter: brightness(1.12) drop-shadow(0 0 10px rgba(242, 178, 91, 0.6)); }
.oeuf .dedans {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: "Cinzel", Georgia, serif;
  font-weight: 500;
  font-size: 2.8em;
  line-height: 1;
  color: var(--or-clair);
  text-shadow: 0 0 10px var(--or), 0 0 22px var(--braise);
  opacity: 0;
  transition: opacity 0.4s ease 0.2s;
}
.oeuf.tremble .coque { animation: tremble 0.12s linear infinite; }
@keyframes tremble { 0%, 100% { transform: rotate(-6deg); } 50% { transform: rotate(6deg); } }
.oeuf.ouvert .coque { transform: scale(1.3); opacity: 0; }
.oeuf.ouvert .dedans { opacity: 1; }
.resultat {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}
@media (max-width: 600px) {
  .de { gap: 0.6em; padding: 1.1em 1.1em; }
  .lancer { width: 5.2em; }
  .oeuf { width: 5.2em; height: 5.2em; margin: -0.5em 0; }
  .oeuf .dedans { font-size: 2.2em; }
}

/* Fin */
.fin { margin-top: 0.6em; text-align: center; }
.fin .mot-fin {
  display: block;
  font-family: "Cinzel", Georgia, serif;
  font-weight: 500;
  font-size: 3em;
  letter-spacing: 0.15em;
  background: linear-gradient(180deg, #f6c46f, #df8a33 55%, #a9531f);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  filter: drop-shadow(0 0 12px rgba(242, 178, 91, 0.45));
  margin-bottom: 0.4em;
}
.appel { display: block; text-align: center; font-family: "Cinzel", Georgia, serif; font-weight: 500; font-size: 1.35em; color: var(--nuit); }

/* Page « Comment est née cette histoire » : texte centré, citation, fiches de l'atelier */
.contexte { font-size: 0.95em; text-align: center; }
.contexte .lien-retour { display: block; text-align: left; margin-bottom: 1em; }
.contexte h1, .arbre h1 {
  font-family: "Cinzel", Georgia, serif;
  font-weight: 500;
  font-size: 2.4em;
  line-height: 1.1;
  color: var(--nuit);
  margin: 0.2em 0 0.1em;
}
.contexte-texte { max-width: 38em; margin: 0 auto; }
.citation {
  max-width: 30em;
  margin: 2em auto;
  padding: 0.2em 0;
  font-style: italic;
  font-size: 1.35em;
  line-height: 1.45;
  color: var(--nuit);
}
.citation .source {
  display: block;
  margin-top: 0.5em;
  font-family: "Marcellus", Georgia, serif;
  font-style: normal;
  font-size: 0.55em;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--or-fonce);
}
.table-fiches {
  margin: 2.6em auto 0;
  max-width: 62em;
  padding: 1.8em 1.5em 2.2em;
  border-radius: 12px;
  background: radial-gradient(ellipse at 80% 0%, var(--nuit-clair), var(--nuit) 55%, var(--nuit-fonce));
  color: #eef1fb;
}
.table-fiches .titre-table {
  display: block;
  font-family: "Marcellus", Georgia, serif;
  font-size: 1em;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--or);
  margin-bottom: 1.3em;
}
.miniatures { display: flex; justify-content: center; align-items: flex-start; flex-wrap: wrap; gap: 2em; }
.miniatures figure { margin: 0; }
.miniatures figcaption { margin-top: 0.8em; font-style: italic; color: var(--or-clair); }
.miniature { display: block; padding: 0; border: none; background: none; cursor: zoom-in; }
.miniature img { display: block; height: 15em; width: auto; border-radius: 6px; box-shadow: 0 0 0 1px rgba(242, 178, 91, 0.5), 0 0 26px -6px rgba(242, 178, 91, 0.6); transition: transform 0.2s ease; }
.miniatures .miniature:hover img { transform: scale(1.04); }
.contexte .credits { display: block; margin-top: 1.6em; font-size: 0.92em; color: var(--gris); }
.contexte .secondaires { display: flex; justify-content: center; margin-top: 1.4em; }
.agrandi { position: fixed; inset: 0; z-index: 100; display: flex; align-items: center; justify-content: center; padding: 2vh 2vw; background: rgba(24, 32, 61, 0.88); cursor: zoom-out; }
.agrandi img { max-width: 100%; max-height: 96vh; border-radius: 6px; }
@media (max-width: 600px) { .miniature img { height: 11em; } }

/* Page de l'arbre */
.arbre .lien-retour { display: block; font-size: 0.9em; }
.arbre-tete { text-align: center; margin-bottom: 1.5em; }
.arbre h1 { margin: 0; }
.arbre .arbre-sous-titre { display: block; font-style: italic; font-size: 1.15em; color: var(--gris); margin: 0.4em 0 1em; }
.arbre img { display: block; width: 100%; max-width: 760px; height: auto; margin: 0 auto; }

tw-link, .enchantment-link { color: var(--nuit); font-weight: 600; text-decoration: none; }
tw-link:hover, .enchantment-link:hover { color: var(--braise); }

@media (max-width: 600px) {
  tw-story { font-size: 0.98em; }
  .garde .grand-titre { font-size: 2.6em; }
  .chapitre .titre { font-size: 1.7em; }
}
@media (max-height: 620px) and (min-width: 801px) {
  tw-story:has(.garde) { padding-top: 0.6em; padding-bottom: 0.6em; }
  .garde { min-height: calc(100vh - 1.4em); gap: 0.6em; }
  .garde .synopsis { font-size: 0.95em; line-height: 1.5; }
}
"""


def e(texte):
    return html.escape(texte, quote=True)


def lire_chapitres():
    blocs = re.split(r"^## ", TEXTE.read_text(encoding="utf-8"), flags=re.M)[1:]
    chapitres = []
    for bloc in blocs:
        lignes = bloc.strip().split("\n")
        titre_complet = lignes[0].strip()
        numero, titre = titre_complet.split(". ", 1)
        nom = numero
        paragraphes = [p.strip() for p in "\n".join(lignes[1:]).split("\n\n") if p.strip()]
        chapitres.append({"nom": nom, "numero": numero, "titre": titre, "paragraphes": paragraphes})
    return chapitres


SEPARATEUR = '<div class="separateur"><span class="embleme"></span></div>'


DE_VIRTUEL = (
    # Un œuf de dragon à la place du dé : on le touche, il tremble, éclot et montre le nombre tiré
    '<div class="lancer"><button class="oeuf" type="button" aria-label="Toucher l’œuf de dragon pour lancer le dé">'
    '<span class="coque"></span><span class="dedans"></span></button>'
    '<span class="resultat" aria-live="polite"></span></div>'
)

# Script commun à toutes les pages : fait rouler le dé puis affiche la face tirée, sans choisir
SCRIPT_DE = """
// L'œuf tremble, éclot puis montre le nombre tiré ; il ne choisit jamais à la place du lecteur
document.addEventListener('click', function (evenement) {
  var oeuf = evenement.target.closest('.oeuf');
  if (!oeuf || oeuf.classList.contains('tremble')) return;
  var resultat = oeuf.parentNode.querySelector('.resultat');
  var face = 1 + Math.floor(Math.random() * 6);
  oeuf.classList.remove('ouvert');
  oeuf.classList.add('tremble');
  resultat.textContent = '';
  setTimeout(function () {
    oeuf.classList.remove('tremble');
    oeuf.querySelector('.dedans').textContent = face;
    oeuf.classList.add('ouvert');
    resultat.textContent = 'L’œuf montre ' + face + '.';
  }, 900);
});

// Page de contexte : une miniature s'ouvre en grand, un clic referme
document.addEventListener('click', function (evenement) {
  var ouvert = document.querySelector('.agrandi');
  if (ouvert) { ouvert.remove(); return; }
  var miniature = evenement.target.closest('.miniature');
  if (!miniature) return;
  var fond = document.createElement('div');
  fond.className = 'agrandi';
  var image = document.createElement('img');
  image.src = miniature.querySelector('img').src;
  image.alt = miniature.querySelector('img').alt;
  fond.appendChild(image);
  document.body.appendChild(fond);
});
document.addEventListener('keydown', function (evenement) {
  var ouvert = document.querySelector('.agrandi');
  if (ouvert && evenement.key === 'Escape') ouvert.remove();
});
"""

def lien(texte, cible):
    return f"[[{texte}->{cible}]]"


def passage_chapitre(ch):
    corps = []
    tirage = any(p.startswith("**Lance le dé") for p in ch["paragraphes"])
    consigne = None
    choix = []
    fin = False
    appel = False
    for p in ch["paragraphes"]:
        if p.startswith("- "):
            for ligne in p.split("\n"):
                if " -> " not in ligne:
                    # « Un autre nombre : relance le dé » : pas de lien, une simple indication
                    relance = ligne[2:].replace("relance le dé", "touche de nouveau l’œuf")
                    choix.append(f'<span class="relance">{relance}</span>')
                    continue
                texte, cible = ligne[2:].rsplit(" -> ", 1)
                choix.append(lien(texte, f"Chapitre {cible}"))
        elif p == "FIN":
            fin = True
        elif p.startswith("**") and p.endswith("**"):
            interieur = p[2:-2]
            if interieur.startswith("Lance le dé") or interieur.startswith("Te souviens-tu"):
                consigne = interieur
            else:
                corps.append(SEPARATEUR + f'<span class="appel">{interieur}</span>')
                appel = True
        else:
            corps.append(p)

    suite = []
    if not appel:
        suite.append(SEPARATEUR)
    if consigne:
        # Sur les vrais tirages, un œuf à toucher à droite du bloc consigne et choix ; il montre la face sans choisir
        lancer = DE_VIRTUEL if tirage else ""
        if tirage:
            # Sur le site, on lance le dé en touchant l'œuf de dragon : la consigne le dit
            consigne = consigne.replace("Lance le dé", "Touche l’œuf de dragon", 1)
        suite.append(f'<div class="de"><div class="de-texte"><span class="consigne">{consigne}</span>'
                     f'<div class="choix">{"".join(choix)}</div></div>{lancer}</div>')
    elif len(choix) == 1:
        # Un renvoi seul, sans lancer de dé, devient un bouton
        suite.append(f'<div class="choix suite elan">{"".join(choix)}</div>')
    elif choix:
        # Les épreuves de la route : le lecteur choisit selon ce qu'il a déjà lu, en liste comme les tirages
        suite.append(f'<div class="choix suite">{"".join(choix)}</div>')
    if fin:
        suite.append('<div class="fin"><span class="mot-fin">FIN</span>'
                     f'<div class="secondaires">{lien("Comment est née cette histoire", "Comment est née cette histoire")}</div></div>')
    texte = ('<div class="texte">'
             f'<h1 class="chapitre"><span class="numero">{ch["numero"]}</span>'
             f'<span class="titre">{ch["titre"]}</span></h1>'
             + "\n\n".join(corps) + "".join(suite) + "</div>")
    # Colonne de droite : l'illustration, qui suit la lecture au défilement
    base = illustration(ch['nom'])
    images = [f"images/chapitres/{base}{suffixe}.jpg" for suffixe in ("", "b")
              if (RACINE / f"images/chapitres/{base}{suffixe}.jpg").exists()]
    cote = ""
    if images:
        cote = ('<div class="cote"><div class="illustration">'
                + "".join(f'<span class="halo"><img src="{i}" alt="{ch["titre"]}"></span>' for i in images)
                + '</div></div>')
    return f'<div class="page">{texte}{cote}</div>'


def illustration(nom):
    """Nom du fichier d'illustration : prologue, chapitre-01, chapitre-02…"""
    return "prologue" if nom == "Prologue" else f"chapitre-{int(nom.split()[-1]):02d}"


def passage_garde():
    return (
        '<div class="garde"><div class="garde-entete">'
        '<span class="surtitre">Une histoire dont le lecteur est le héros</span>'
        f'<div class="grand-titre">{TITRE}</div>'
        f'<span class="nom-auteur">{AUTRICES}</span></div>'
        '<div class="garde-corps"><div class="garde-image"><img src="images/couverture.jpg" '
        'alt="Anna, tuque rouge et crosse de hockey, arrive en bateau devant l’île et son château noir"></div>'
        f'<div class="garde-texte"><div class="synopsis">{SYNOPSIS}</div>'
        f'<div class="commencer">{lien("Commencer l\'histoire", "Prologue")}</div>'
        f'<div class="secondaires">{lien("Comment est née cette histoire", "Comment est née cette histoire")} '
        f'{lien("L\'arbre de l\'histoire", "L\'arbre de l\'histoire")}</div>'
        "</div></div></div>"
    )


def miniature(fichier, legende, description):
    return (f'<figure><button class="miniature" type="button" aria-label="Agrandir {description}">'
            f'<img src="images/fiches/{fichier}" alt="{description}"></button>'
            f'<figcaption>{legende}</figcaption></figure>')


def portrait(fichier, nom, autrice):
    return (f'<figure><img src="images/portraits/{fichier}" alt="{nom}, dessinée par {autrice}">'
            f'<figcaption>{nom}</figcaption></figure>')


def passage_contexte():
    return (
        '<div class="contexte"><span class="lien-retour">[[Couverture->Page de garde]]</span>\n'
        f'<h1>Comment est née cette histoire</h1>{SEPARATEUR}'
        '<div class="contexte-texte">'
        + "\n\n".join(CONTEXTE[:4])
        + f'<div class="citation">« {CITATION} »<span class="source">Louisa et June, sur leur fiche récit</span></div>'
        + CONTEXTE[4]
        + '</div><div class="table-fiches"><span class="titre-table">Les fiches de l’atelier</span>'
        '<div class="miniatures">'
        + miniature("fiche_recit.jpg", "Le récit", "la fiche récit de Louisa et June")
        + miniature("fiche_personnage_croquemou.jpg", "Une fiche personnage", "la fiche personnage de Croquemou")
        + miniature("fiche_situation_1.jpg", "Une fiche à embranchement", "la fiche situation n° 1, avec ses choix au dé")
        + '</div></div>'
        + '<span class="credits">Une histoire librement inspirée du récit de Louisa et de June.\nRéalisation du livre : '
        "Laboratoire d’Aix-périmentation et de Bidouille.</span>"
        + f'<div class="secondaires">{lien("Commencer le livre", "Prologue")}</div>\n</div>'
    )


def passage_arbre():
    # Page simple : le titre centré en haut, l'arbre dessous
    return (
        f'<div class="arbre"><span class="lien-retour">{lien("Couverture", "Page de garde")}</span>'
        f'<div class="arbre-tete"><h1>{TITRE}</h1>'
        f'<span class="arbre-sous-titre">Tous les chemins de l\'histoire imaginée par {AUTRICES}</span></div>'
        '<img src="images/arbre.svg" alt="L\'arbre de toutes les branches de l\'histoire"></div>'
    )


def construire():
    modele = SORTIE.read_text(encoding="utf-8")
    debut = modele[: modele.index("<tw-storydata")]
    moteur = modele[modele.index("</tw-storydata>"):]
    if NOINDEX not in debut:
        debut = debut.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + NOINDEX)
    # Icônes : on retire celles qui traînent (héritées d'un autre livre ou d'une construction précédente)
    # puis on remet le favicon du livre
    debut = re.sub(r"<link rel=\"(?:icon|apple-touch-icon)\"[^>]*>", "", debut)
    debut = debut.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + FAVICON)
    debut = re.sub(r"<title>[^<]*</title>", f"<title>{TITRE}</title>", debut)
    lire = re.compile(r"JavaScript (?:needs to be enabled to play|doit être activé pour lire) [^<.]*\.")
    debut = lire.sub(f"JavaScript doit être activé pour lire {TITRE}.", debut)
    moteur = lire.sub(f"JavaScript doit être activé pour lire {TITRE}.", moteur)

    passages = [
        ("Bouton couverture", "header",
         '(unless: (a: "Page de garde", "L\'arbre de l\'histoire", "Comment est née cette histoire") contains (passage:)\'s name)'
         '[<div class="retour">[[Couverture->Page de garde]]</div>]'),
        ("Page de garde", "", passage_garde()),
        ("Comment est née cette histoire", "", passage_contexte()),
        ("L'arbre de l'histoire", "", passage_arbre()),
    ]
    for ch in lire_chapitres():
        passages.append((ch["nom"], "", passage_chapitre(ch)))

    # Espaces insécables de la typographie française : un guillemet ou un deux-points ne se retrouve
    # jamais seul en début de ligne
    insecables = [("« ", "«\u00a0"), (" »", "\u00a0»"), (" :", "\u00a0:"), (" ?", "\u00a0?"),
                  (" !", "\u00a0!"), (" ;", "\u00a0;")]
    for i, (nom, tags, contenu) in enumerate(passages):
        if tags != "header":
            for avant, apres in insecables:
                contenu = contenu.replace(avant, apres)
            passages[i] = (nom, tags, contenu)

    noms = {p[0] for p in passages}
    for nom, _, contenu in passages:
        for cible in re.findall(r"->([^\]]+)\]\]", contenu):
            assert cible in noms, f"Lien cassé dans {nom} : {cible}"

    xml = [f'<tw-storydata name="{e(TITRE)}" startnode="2" creator="Twine" creator-version="2.12.1" '
           f'format="Harlowe" format-version="3.3.9" ifid="{str(uuid.uuid5(uuid.NAMESPACE_URL, TITRE)).upper()}" '
           'options="" tags="" zoom="1" hidden>',
           f'<style role="stylesheet" id="twine-user-stylesheet" type="text/twine-css">{CSS}</style>',
           '<script role="script" id="twine-user-script" type="text/twine-javascript">' + SCRIPT_DE + '</script>']
    for pid, (nom, tags, contenu) in enumerate(passages, start=1):
        xml.append(f'<tw-passagedata pid="{pid}" name="{e(nom)}" tags="{tags}" '
                   f'position="{pid * 150},0" size="100,100">{e(contenu)}</tw-passagedata>')
    SORTIE.write_text(debut + "".join(xml) + moteur, encoding="utf-8")
    print(f"{SORTIE} : {len(passages)} passages")


if __name__ == "__main__":
    construire()
