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
@font-face { font-family: "Eagle Lake"; font-display: swap; src: url("fonts/EagleLake.woff2") format("woff2"); }
@font-face { font-family: "Skranji"; font-weight: 700; font-display: swap; src: url("fonts/Skranji.woff2") format("woff2"); }
@font-face { font-family: "Alegreya"; font-style: normal; font-weight: 400 900; font-display: swap; src: url("fonts/Alegreya.woff2") format("woff2"); }
@font-face { font-family: "Alegreya"; font-style: italic; font-weight: 400 900; font-display: swap; src: url("fonts/Alegreya-i.woff2") format("woff2"); }
@font-face { font-family: "Literata"; font-style: normal; font-weight: 200 900; font-display: swap; src: url("fonts/Literata.woff2") format("woff2"); }
@font-face { font-family: "Literata"; font-style: italic; font-weight: 200 900; font-display: swap; src: url("fonts/Literata-i.woff2") format("woff2"); }

/* Livre jeunesse d'aventure : la page blanche partout, la nuit bleue de l'île pour le moment du tirage,
   le rouge de la tuque d'Anna, l'orange de Croquemou et le bleu de la glace pour les touches de couleur, l'or et la braise de Croquemou pour les étiquettes et les boutons.
   Titres en Eagle Lake (carte au trésor), étiquettes et boutons en Skranji (aventure), texte en
   Alegreya (livre de contes), encart du tirage en Literata. */
:root {
  --nuit: #24305a;
  --nuit-fonce: #18203d;
  --nuit-clair: #3b4f86;
  --or: #f2b25b;
  --or-clair: #ffe1a8;
  --or-fonce: #b9692a;
  --braise: #e0782f;
  --braise-fonce: #a9531f;
  --encre: #2a2c3d;
  --gris: #6a6e80;
  --papier: #ffffff;
  /* Couleurs prises aux planches et à Anna */
  --tuque: #c8322a;
  --tuque-fonce: #8f1f1c;
  --croquemou: #e8862a;
  --peche: #f6c992;
  --glace: #7fa3c8;
  --neige: #e3ecf6;
}
html, body, tw-story { background-color: var(--papier); color: var(--encre); }
tw-story {
  font-family: "Alegreya", Georgia, serif;
  font-size: 1.06em;
  line-height: 1.65;
  padding: 4em 1.25em 4em;
}
tw-passage { max-width: 1140px; margin: 0 auto; }

/* Pages de lecture : le texte à gauche, l'illustration à droite, qui suit le défilement */
.page {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
  gap: 3em;
  align-items: start;
}
.texte { max-width: 36em; }
.cote { position: sticky; top: 1.5em; margin-top: 1.5em; }
.illustration { display: flex; flex-direction: column; gap: 1.6em; }
.halo { display: block; }
/* Le cadre épouse la planche : l'image garde ses proportions et n'est jamais étirée dans une boîte plus large */
.illustration img {
  display: block;
  width: auto;
  height: auto;
  max-width: 100%;
  max-height: 86vh;
  margin: 0 auto;
  border-radius: 16px;
  box-shadow: 0 14px 30px -12px rgba(36, 48, 90, 0.45);
}
.page:not(:has(.cote)) { grid-template-columns: minmax(0, 38em); justify-content: center; }
@media (max-width: 800px) {
  .page { grid-template-columns: minmax(0, 1fr); gap: 1.6em; }
  .cote { position: static; order: -1; margin-top: 0; }
}
tw-sidebar { display: none; }
tw-story { overflow: clip; }

/* Titres de chapitre : le numéro dans une pastille rouge tuque, le titre en lettres de carte au trésor */
.chapitre { font-size: 1em; font-weight: 400; margin: 0 0 1em; line-height: 1.1; }
.chapitre .numero {
  display: inline-flex;
  align-items: center;
  gap: 0.5em;
  font-family: "Skranji", "Trebuchet MS", sans-serif;
  font-weight: 700;
  font-size: 0.95em;
  color: var(--gris);
  margin-bottom: 0.35em;
}
.chapitre .numero b {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.9em;
  height: 1.9em;
  border-radius: 50%;
  background: var(--tuque);
  color: #fff;
  font-weight: 700;
  font-size: 1.05em;
}
.chapitre .titre {
  display: block;
  font-family: "Eagle Lake", Georgia, serif;
  font-weight: 400;
  font-size: 1.85em;
  line-height: 1.15;
  color: var(--nuit);
}

/* Page de garde : la seule page sur fond de nuit, un bleu un peu plus clair que celui de l'encart */
html:has(.garde), html:has(.garde) body, tw-story:has(.garde) {
  background: radial-gradient(ellipse at 70% 0%, #5065a0 0%, #33427a 45%, #252f58 100%) fixed;
  color: #eef1fb;
}
tw-story:has(.garde) { padding-top: 1em; padding-bottom: 1em; }
.garde {
  min-height: calc(100vh - 2.2em);
  display: flex;
  align-items: center;
}
.garde-corps {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(22em, 1fr);
  gap: 3.4em;
  align-items: center;
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  padding: 1.5em 0;
}
.garde-image img {
  display: block;
  width: auto;
  height: auto;
  max-width: 100%;
  max-height: 84vh;
  margin: 0 auto;
  border-radius: 18px;
  box-shadow: 0 14px 34px -8px rgba(0, 0, 0, 0.5);
}
.garde-texte { display: flex; flex-direction: column; align-items: center; gap: clamp(0.9em, 2.6vh, 1.4em); text-align: center; }
.garde-entete { display: flex; flex-direction: column; align-items: center; }
@media (max-width: 800px) {
  .garde { min-height: 0; }
  .garde-corps { grid-template-columns: minmax(0, 1fr); gap: 2em; }
}
.garde .surtitre { font-family: "Skranji", "Trebuchet MS", sans-serif; font-weight: 700; font-size: 1em; color: #b9d0ea; }
.garde .grand-titre {
  font-family: "Eagle Lake", Georgia, serif;
  font-weight: 400;
  font-size: clamp(2.3em, 7vh, 3.3em);
  line-height: 1.05;
  color: #fff;
  margin: 0.15em 0 0.1em;
}
.garde .grand-titre span { color: var(--croquemou); }
.garde .nom-auteur { font-family: "Skranji", "Trebuchet MS", sans-serif; font-weight: 700; font-size: 1.3em; color: #fff; }
.garde .synopsis { margin: 0 auto; max-width: 32em; font-size: 0.98em; line-height: 1.65; color: #e2e7f6; }
/* Commencer : le mot entre deux traits bleu glace, précédé de l'œuf de dragon qui tremble au survol */
.garde .commencer { display: flex; align-items: center; justify-content: center; gap: 0.7em; }
.garde .commencer .trait { flex: none; width: 4.5em; height: 0.9em; background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 14'%3E%3Cpath d='M118 7 C80 1.5 40 4.5 8 7 C40 9.5 80 12.5 118 7 Z' fill='%23b9d0ea'/%3E%3Ccircle cx='5' cy='7' r='3' fill='%23b9d0ea'/%3E%3C/svg%3E") no-repeat center / contain; }
.garde .commencer .trait.droite { transform: scaleX(-1); }
.garde .commencer tw-link, .garde .commencer .enchantment-link {
  display: inline-flex;
  align-items: center;
  gap: 0.35em;
  white-space: nowrap;
  font-family: "Skranji", "Trebuchet MS", sans-serif;
  font-weight: 700;
  font-size: 1.45em;
  color: #fff;
  transition: color 0.2s ease;
}
.garde .commencer tw-link::before, .garde .commencer .enchantment-link::before {
  content: "";
  flex: none;
  width: 2.2em;
  height: 2.2em;
  background: url("images/oeuf.png") no-repeat center / contain;
}
.garde .commencer tw-link:hover, .garde .commencer .enchantment-link:hover { color: var(--peche); }
.garde .commencer tw-link:hover::before, .garde .commencer .enchantment-link:hover::before { animation: tremble 0.12s linear 4; }
@media (max-width: 600px) {
  .garde .commencer .trait { width: 2.4em; }
  .garde .commencer tw-link, .garde .commencer .enchantment-link { font-size: 1.25em; }
}
.garde .secondaires { display: flex; flex-wrap: wrap; justify-content: center; gap: 0.6em 1.2em; }
.garde .secondaires tw-link, .garde .secondaires .enchantment-link {
  font-family: "Skranji", "Trebuchet MS", sans-serif;
  font-weight: 700;
  font-size: 0.95em;
  color: #fff;
  background: transparent;
  border: none;
  border-bottom: 2px solid rgba(246, 201, 146, 0.7);
  border-radius: 0;
  padding: 0;
}
.garde .secondaires tw-link:hover, .garde .secondaires .enchantment-link:hover { color: var(--peche); }

/* Petits boutons secondaires */
.secondaires tw-link, .secondaires .enchantment-link {
  display: inline-block;
  font-family: "Skranji", "Trebuchet MS", sans-serif;
  font-weight: 700;
  font-size: 0.95em;
  color: var(--nuit);
  border: 2px solid var(--or);
  border-radius: 12px;
  padding: 0.2em 1em 0.15em;
  background: var(--papier);
}
.secondaires tw-link:hover, .secondaires .enchantment-link:hover { color: var(--nuit); background: var(--or-clair); }

/* Lien Couverture */
.retour { margin: 0 auto 1.2em; text-align: left; }
.retour tw-link, .retour .enchantment-link,
.lien-retour tw-link, .lien-retour .enchantment-link {
  font-family: "Skranji", "Trebuchet MS", sans-serif;
  font-weight: 700;
  font-size: 0.9em;
  color: var(--gris);
}
.retour tw-link::before, .lien-retour tw-link::before { content: "← "; }
.retour tw-link:hover, .lien-retour tw-link:hover { color: var(--braise); }

/* Le moment du tirage : un encart de nuit sur la page blanche, en Literata, avec l'œuf à droite */
.de {
  display: flex;
  align-items: center;
  gap: 1.2em;
  margin-top: 0.4em;
  padding: 1.15em 1.4em;
  border-radius: 16px;
  background: radial-gradient(ellipse at 80% 0%, var(--nuit-clair), var(--nuit) 55%, var(--nuit-fonce));
  color: #eef1fb;
  font-family: "Literata", Georgia, serif;
  font-size: 0.9em;
  line-height: 1.55;
}
.de-texte { flex: 1; min-width: 0; }
.de .consigne { display: block; font-style: italic; color: var(--or-clair); margin-bottom: 0.6em; }
.choix { display: flex; flex-direction: column; align-items: flex-start; gap: 0.5em; }
.choix tw-link, .choix .enchantment-link { color: var(--nuit); font-weight: 700; }
.choix tw-link:hover, .choix .enchantment-link:hover { color: var(--braise); }
.de .choix tw-link, .de .choix .enchantment-link { color: #fff; }
.de .choix tw-link:hover, .de .choix .enchantment-link:hover { color: var(--or); }
/* Le nombre à obtenir, dans une pastille dorée devant le choix */
.tirage { display: inline-flex; align-items: center; gap: 0.55em; }
.tirage b {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.8em;
  height: 1.8em;
  padding: 0 0.5em;
  border-radius: 999px;
  background: var(--or);
  color: var(--nuit-fonce);
  font-family: "Skranji", "Trebuchet MS", sans-serif;
  font-weight: 700;
  font-size: 0.95em;
}
.choix .relance { font-style: italic; color: var(--gris); }
.de .choix .relance { color: #b9c4e6; font-size: 0.95em; }
.suite { margin-top: 0.8em; }

/* Séparateur : une étincelle dorée entre deux traits qui s'effacent */
.separateur { display: flex; align-items: center; justify-content: center; gap: 0.7em; margin: 1.5em 0 1.1em; }
.separateur::before, .separateur::after { content: ""; width: 5.5em; height: 1.5px; background: linear-gradient(to right, transparent, var(--or)); }
.separateur::after { background: linear-gradient(to left, transparent, var(--or)); }
.separateur .embleme {
  width: 1em;
  height: 1em;
  background: radial-gradient(circle, #fff3d0 0 20%, var(--or) 45%, transparent 70%);
  filter: drop-shadow(0 0 6px rgba(242, 178, 91, 0.9));
}

/* Renvoi seul : un bouton bleu glace, une flèche rouge tuque qui avance au survol */
.elan { align-items: flex-start; margin-top: 1.6em; }
.choix.elan tw-link, .choix.elan .enchantment-link {
  display: inline-flex;
  align-items: center;
  gap: 0.55em;
  font-family: "Skranji", "Trebuchet MS", sans-serif;
  font-weight: 700;
  font-size: 1.02em;
  color: var(--nuit);
  background: var(--neige);
  padding: 0.4em 1.3em 0.35em;
  border-radius: 12px;
  border-bottom: 3px solid var(--glace);
  transition: background 0.18s ease;
}
.choix.elan tw-link::after, .choix.elan .enchantment-link::after {
  content: "→";
  font-family: "Alegreya", Georgia, serif;
  font-weight: 700;
  color: var(--tuque);
  transition: transform 0.18s ease;
}
.choix.elan tw-link:hover, .choix.elan .enchantment-link:hover { color: var(--nuit); background: #d3e1f0; }
.choix.elan tw-link:hover::after, .choix.elan .enchantment-link:hover::after { transform: translateX(4px); }

/* L'œuf de dragon de Manon : il tremble, éclot et laisse voir le nombre tiré. L'image est carrée et
   l'œuf est en son centre : il est centré dans sa colonne et dans la hauteur de l'encart. Le résultat
   écrit n'est lu que par les lecteurs d'écran. */
.lancer { flex: none; width: 6.4em; align-self: stretch; display: flex; align-items: center; justify-content: center; }
.oeuf {
  position: relative;
  width: 6.4em;
  height: 6.4em;
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
  font-family: "Skranji", "Trebuchet MS", sans-serif;
  font-weight: 700;
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
  .de { gap: 0.6em; padding: 1em 1em; }
  .lancer { width: 5em; }
  .oeuf { width: 5em; height: 5em; margin: -0.5em 0; }
  .oeuf .dedans { font-size: 2.2em; }
}

/* Fin */
.fin { margin-top: 0.6em; text-align: center; }
.fin .mot-fin {
  display: block;
  font-family: "Eagle Lake", Georgia, serif;
  font-size: 2.8em;
  color: #fff;
  text-shadow: 3px 3px 0 var(--braise), 6px 6px 0 var(--nuit);
  margin-bottom: 0.5em;
}
.appel { display: block; text-align: center; font-family: "Eagle Lake", Georgia, serif; font-size: 1.3em; color: var(--nuit); }

/* Page « Comment est née cette histoire » : texte centré, citation, fiches de l'atelier */
.contexte { text-align: center; }
.contexte .lien-retour { display: block; text-align: left; margin-bottom: 1em; }
.contexte h1, .arbre h1 {
  font-family: "Eagle Lake", Georgia, serif;
  font-weight: 400;
  font-size: 2.2em;
  line-height: 1.15;
  color: var(--nuit);
  margin: 0.2em 0 0.1em;
}
.contexte-texte { max-width: 36em; margin: 0 auto; }
.citation {
  max-width: 30em;
  margin: 2em auto;
  font-style: italic;
  font-size: 1.3em;
  line-height: 1.45;
  color: var(--nuit);
}
.citation .source {
  display: block;
  margin-top: 0.5em;
  font-family: "Skranji", "Trebuchet MS", sans-serif;
  font-style: normal;
  font-weight: 700;
  font-size: 0.6em;
  color: var(--braise);
}
.table-fiches {
  margin: 2.6em auto 0;
  max-width: 62em;
  padding: 1.8em 1.5em 2.2em;
  border-radius: 16px;
  background: radial-gradient(ellipse at 80% 0%, var(--nuit-clair), var(--nuit) 55%, var(--nuit-fonce));
  color: #eef1fb;
}
.table-fiches .titre-table {
  display: block;
  font-family: "Skranji", "Trebuchet MS", sans-serif;
  font-weight: 700;
  font-size: 1.2em;
  color: var(--or);
  margin-bottom: 1.3em;
}
.miniatures { display: flex; justify-content: center; align-items: flex-start; flex-wrap: wrap; gap: 2em; }
.miniatures figure { margin: 0; }
.miniatures figcaption { margin-top: 0.9em; font-family: "Skranji", "Trebuchet MS", sans-serif; font-weight: 700; color: var(--or-clair); }
.miniature { display: block; padding: 0; border: none; background: none; cursor: zoom-in; }
.miniature img { display: block; height: 15em; width: auto; border: 6px solid #fff; border-radius: 4px; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.35); transition: transform 0.2s ease; }
.miniatures figure:nth-child(1) img { transform: rotate(-3deg); }
.miniatures figure:nth-child(2) img { transform: rotate(1.5deg); }
.miniatures figure:nth-child(3) img { transform: rotate(-1deg); }
.miniatures .miniature:hover img { transform: rotate(0) scale(1.04); }
.contexte .credits { display: block; margin-top: 1.6em; font-size: 0.92em; color: var(--gris); }
.contexte .secondaires { display: flex; justify-content: center; margin-top: 1.4em; }
.agrandi { position: fixed; inset: 0; z-index: 100; display: flex; align-items: center; justify-content: center; padding: 2vh 2vw; background: rgba(24, 32, 61, 0.88); cursor: zoom-out; }
.agrandi img { max-width: 100%; max-height: 96vh; border-radius: 4px; }
@media (max-width: 600px) { .miniature img { height: 11em; } }

/* Page de l'arbre */
.arbre .lien-retour { display: block; font-size: 0.9em; }
.arbre-tete { text-align: center; margin-bottom: 1.5em; }
.arbre h1 { margin: 0; }
.arbre .arbre-sous-titre { display: block; font-style: italic; font-size: 1.1em; color: var(--gris); margin: 0.4em 0 1em; }
.arbre img { display: block; width: 100%; max-width: 760px; height: auto; margin: 0 auto; }

tw-link, .enchantment-link { color: var(--nuit); font-weight: 700; text-decoration: none; }
tw-link:hover, .enchantment-link:hover { color: var(--braise); }

@media (max-width: 600px) {
  tw-story { font-size: 1em; }
  .garde .grand-titre { font-size: 2.4em; }
  .chapitre .titre { font-size: 1.6em; }
}
@media (max-height: 620px) and (min-width: 801px) {
  tw-story:has(.garde) { padding-top: 0.6em; padding-bottom: 0.6em; }
  .garde { min-height: calc(100vh - 1.4em); }
  .garde .synopsis { font-size: 0.92em; line-height: 1.5; }
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
                texte = texte.rstrip(".")
                tirage_vise = re.match(r"(\d|Un nombre pair|Un nombre impair) : (.*)", texte)
                if tirage_vise:
                    # Le nombre à obtenir dans une pastille dorée, devant le lien
                    pastille = {"Un nombre pair": "Pair", "Un nombre impair": "Impair"}.get(tirage_vise[1], tirage_vise[1])
                    choix.append(f'<span class="tirage"><b>{pastille}</b>{lien(tirage_vise[2], f"Chapitre {cible}")}</span>')
                else:
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
             f'<h1 class="chapitre"><span class="numero">{numero_chapitre(ch["numero"])}</span>'
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


def numero_chapitre(numero):
    """« Chapitre 2 » devient la pastille rouge 2 suivie du mot Chapitre ; le Prologue reste un mot seul"""
    if numero.startswith("Chapitre "):
        return f'<b>{numero.split()[-1]}</b> Chapitre'
    return numero


def illustration(nom):
    """Nom du fichier d'illustration : prologue, chapitre-01, chapitre-02…"""
    return "prologue" if nom == "Prologue" else f"chapitre-{int(nom.split()[-1]):02d}"


def passage_garde():
    # La couverture à gauche comme une photo collée, le titre et le résumé à droite
    titre = TITRE.replace("dragons", "<span>dragons</span>")
    return (
        '<div class="garde"><div class="garde-corps"><div class="garde-image"><img src="images/couverture.jpg" '
        'alt="Anna, tuque rouge et crosse de hockey, debout près de Croquemou face au château noir"></div>'
        '<div class="garde-texte"><div class="garde-entete">'
        '<span class="surtitre">Une histoire dont le lecteur est le héros</span>'
        f'<div class="grand-titre">{titre}</div>'
        f'<span class="nom-auteur">{AUTRICES}</span></div>'
        f'<div class="synopsis">{SYNOPSIS}</div>'
        '<div class="commencer"><span class="trait"></span>'
        f'{lien("Commencer l\'histoire", "Prologue")}<span class="trait droite"></span></div>'
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
