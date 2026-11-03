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
# Favicon : la tête de Croquemou
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
@font-face { font-family: "Uncial Antiqua"; font-display: swap; src: url("fonts/UncialAntiqua.woff2") format("woff2"); }
@font-face { font-family: "Bangers"; font-display: swap; src: url("fonts/Bangers.woff2") format("woff2"); }
@font-face { font-family: "Patrick Hand"; font-display: swap; src: url("fonts/PatrickHand.woff2") format("woff2"); }
@font-face { font-family: "Nunito"; font-style: normal; font-weight: 400 800; font-display: swap; src: url("fonts/Nunito.woff2") format("woff2"); }
@font-face { font-family: "Nunito"; font-style: italic; font-weight: 400 800; font-display: swap; src: url("fonts/Nunito-italique.woff2") format("woff2"); }

/* Esprit BD fantastique, couleurs des planches : encre noire des cases, rouge de la tuque d'Anna,
   orange et jaune de Croquemou, bleu de la neige et du ciel d'hiver */
:root {
  --encre: #1c1b24;
  --rouge: #c23a2b;
  --rouge-fonce: #8f2419;
  --orange: #e8862a;
  --jaune: #f6cf4e;
  --bleu: #4f6aa8;
  --ciel: #e3e9f6;
  --gris: #5b5f6e;
  --papier: #ffffff;
}
html, body, tw-story { background-color: var(--papier); color: var(--encre); }
tw-story {
  font-family: "Nunito", "Trebuchet MS", sans-serif;
  font-size: 1.04em;
  line-height: 1.7;
  padding: 4em 1.25em 4em;
}
tw-passage { max-width: 1180px; margin: 0 auto; }

/* Pages de lecture : le texte à gauche, la planche à droite, qui suit le défilement */
.page {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
  gap: 2.8em;
  align-items: start;
}
.cote { position: sticky; top: 1.5em; margin-top: 2.5em; }
.illustration { display: flex; flex-direction: column; gap: 1.2em; }
.halo { display: block; }
/* Une case de BD : épais trait d'encre et ombre portée franche */
.illustration img {
  display: block;
  width: 100%;
  max-height: 88vh;
  object-fit: contain;
  border: 3px solid var(--encre);
  box-shadow: 6px 6px 0 var(--encre);
  background: var(--papier);
}
.page:not(:has(.cote)) { grid-template-columns: minmax(0, 40em); justify-content: center; }
@media (max-width: 800px) {
  .page { grid-template-columns: minmax(0, 1fr); gap: 1.4em; }
  .cote { position: static; order: -1; margin-top: 0; }
}
tw-sidebar { display: none; }
tw-story { overflow: clip; }

/* Titres de chapitre : le numéro dans un cartouche jaune, le titre en lettres de légende */
.chapitre { font-size: 1em; font-weight: 400; margin: 0 0 1.1em; line-height: 1.1; }
.chapitre .numero {
  display: inline-block;
  font-family: "Bangers", "Impact", sans-serif;
  font-size: 1.25em;
  letter-spacing: 0.06em;
  color: var(--encre);
  background: var(--jaune);
  border: 2.5px solid var(--encre);
  box-shadow: 3px 3px 0 var(--encre);
  padding: 0.1em 0.6em 0;
  transform: rotate(-2deg);
  margin-bottom: 0.7em;
}
.chapitre .titre {
  display: block;
  font-family: "Uncial Antiqua", Georgia, serif;
  font-weight: 400;
  font-size: 2.1em;
  color: var(--rouge);
  text-shadow: 2px 2px 0 var(--jaune);
}

/* Page de garde */
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
  border: 3px solid var(--encre);
  box-shadow: 7px 7px 0 var(--encre);
  transform: rotate(-1deg);
}
.garde-texte { display: flex; flex-direction: column; gap: clamp(1.1em, 3.4vh, 1.9em); text-align: center; }
@media (max-width: 800px) {
  .garde { min-height: 0; }
  .garde-corps { grid-template-columns: minmax(0, 1fr); gap: 1.6em; }
}
.garde .surtitre { font-family: "Patrick Hand", cursive; font-size: 1.2em; color: var(--gris); }
.garde .grand-titre {
  font-family: "Uncial Antiqua", Georgia, serif;
  font-size: clamp(2.4em, 8vh, 4.6em);
  line-height: 1;
  color: var(--rouge);
  -webkit-text-stroke: 1.5px var(--encre);
  text-shadow: 4px 4px 0 var(--jaune), 6px 6px 0 var(--encre);
  margin: 0.1em 0 0.2em;
}
.garde .nom-auteur {
  font-family: "Bangers", "Impact", sans-serif;
  font-size: clamp(1.3em, 3.6vh, 1.8em);
  letter-spacing: 0.08em;
  color: var(--bleu);
}
.garde .synopsis { margin: 0 auto; max-width: 38em; font-size: 1.05em; line-height: 1.65; }
/* Commencer : une grande case rouge à l'encre noire, légèrement penchée, qui se redresse au survol */
.garde .commencer tw-link, .garde .commencer .enchantment-link {
  display: inline-block;
  font-family: "Bangers", "Impact", sans-serif;
  font-size: 1.7em;
  letter-spacing: 0.06em;
  color: #ffffff;
  background: var(--rouge);
  border: 3px solid var(--encre);
  box-shadow: 5px 5px 0 var(--encre);
  padding: 0.25em 1.1em 0.15em;
  transform: rotate(-2deg);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.garde .commencer tw-link:hover, .garde .commencer .enchantment-link:hover {
  color: #ffffff;
  transform: rotate(0deg) translate(2px, 2px);
  box-shadow: 3px 3px 0 var(--encre);
}
.garde .secondaires { display: flex; flex-wrap: wrap; justify-content: center; gap: 0.8em 1.4em; }

/* Petits boutons secondaires : bulle à l'encre */
.secondaires tw-link, .secondaires .enchantment-link {
  display: inline-block;
  font-family: "Patrick Hand", cursive;
  font-size: 1.05em;
  color: var(--encre);
  border: 2px solid var(--encre);
  border-radius: 999px;
  padding: 0.15em 1em;
  background: var(--papier);
}
.secondaires tw-link:hover, .secondaires .enchantment-link:hover { background: var(--jaune); color: var(--encre); }

/* Lien Couverture */
.retour { margin: 0 auto 1.2em; text-align: left; }
.retour tw-link, .retour .enchantment-link,
.lien-retour tw-link, .lien-retour .enchantment-link { font-size: 0.9em; font-weight: 700; color: var(--gris); }
.retour tw-link::before, .lien-retour tw-link::before { content: "← "; }
.retour tw-link:hover, .lien-retour tw-link:hover { color: var(--rouge); }

/* Consigne du dé : une bulle de BD, avec sa pointe */
.de .consigne {
  position: relative;
  display: block;
  font-family: "Patrick Hand", cursive;
  font-size: 1.35em;
  line-height: 1.25;
  color: var(--encre);
  background: var(--papier);
  border: 2.5px solid var(--encre);
  border-radius: 1.2em;
  padding: 0.5em 0.9em;
  margin-bottom: 1.1em;
}
.de .consigne::after {
  content: "";
  position: absolute;
  right: 2.2em;
  bottom: -14px;
  width: 22px;
  height: 14px;
  background: var(--papier);
  border-right: 2.5px solid var(--encre);
  border-bottom: 2.5px solid var(--encre);
  transform: skewX(-35deg);
}
.choix { display: flex; flex-direction: column; align-items: flex-start; gap: 0.45em; }
.choix > *::before { content: "▸"; color: var(--rouge); margin-right: 0.5em; }
.choix tw-link, .choix .enchantment-link {
  color: var(--encre);
  font-weight: 800;
  border-bottom: 2px solid var(--orange);
}
.choix tw-link:hover, .choix .enchantment-link:hover { color: var(--rouge); }
.choix .relance { color: var(--gris); font-style: italic; }
.elan > *::before { content: none; }
.suite { margin-top: 0.8em; }

/* Séparateur : une petite flamme de Croquemou entre deux traits d'encre */
.separateur { display: flex; align-items: center; justify-content: center; gap: 0.7em; margin: 1.6em 0 1.1em; }
.separateur::before, .separateur::after { content: ""; width: 6em; height: 2.5px; background: var(--encre); border-radius: 2px; }
.separateur .embleme {
  width: 1.4em;
  height: 1.8em;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 28 36'%3E%3Cpath d='M14 2 C18 10 25 13 25 22 C25 30 20 34 14 34 C8 34 3 30 3 22 C3 16 7 13 9 8 C10 13 12 15 14 15 C15 11 13 7 14 2 Z' fill='%23e8862a' stroke='%231c1b24' stroke-width='2.2' stroke-linejoin='round'/%3E%3Cpath d='M14 18 C17 22 19 24 19 27 C19 31 16 32 14 32 C11 32 9 30 9 27 C9 24 12 23 14 18 Z' fill='%23f6cf4e'/%3E%3C/svg%3E") no-repeat center / contain;
}
.garde .separateur { margin: 0; }

/* Renvoi seul : un cartouche jaune de BD */
.elan { align-items: center; margin-top: 2.2em; }
.choix.elan tw-link, .choix.elan .enchantment-link {
  display: inline-block;
  font-family: "Bangers", "Impact", sans-serif;
  font-weight: 400;
  font-size: 1.25em;
  letter-spacing: 0.05em;
  color: var(--encre);
  background: var(--jaune);
  border: 2.5px solid var(--encre);
  box-shadow: 4px 4px 0 var(--encre);
  padding: 0.2em 0.9em 0.1em;
  transform: rotate(-1.5deg);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.choix.elan tw-link:hover, .choix.elan .enchantment-link:hover {
  color: var(--encre);
  transform: rotate(0deg) translate(2px, 2px);
  box-shadow: 2px 2px 0 var(--encre);
}

/* Dé à lancer : un dé dessiné à l'encre, comme dans une case ; il montre la face sans choisir */
.de { display: flex; align-items: center; gap: 1.6em; }
.de-texte { flex: 1; min-width: 0; }
.fleche-de { flex: none; width: 3.4em; height: auto; margin-right: -0.6em; transform: translateY(-0.2em); }
.lancer { flex: none; position: relative; display: flex; }
.de-virtuel {
  position: relative;
  font-size: inherit;
  width: 4.6em;
  height: 4.6em;
  padding: 0.5em;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(3, 1fr);
  background: var(--papier);
  border: 3px solid var(--encre);
  border-radius: 0.7em;
  box-shadow: 5px 5px 0 var(--encre);
  cursor: pointer;
  transform: rotate(-6deg);
  transition: transform 0.15s ease;
}
.de-virtuel:hover { transform: rotate(4deg); }
.de-virtuel.roule { animation: roule 0.3s linear infinite; }
@keyframes roule {
  0% { transform: rotate(0deg) translateY(0); }
  50% { transform: rotate(180deg) translateY(-4px); }
  100% { transform: rotate(360deg) translateY(0); }
}
.de-virtuel i { width: 0.8em; height: 0.8em; border-radius: 50%; background: var(--rouge); border: 2px solid var(--encre); place-self: center; visibility: hidden; }
.de-virtuel[data-face="0"]::after {
  content: "?";
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: "Bangers", "Impact", sans-serif;
  font-size: 2.8em;
  color: var(--rouge);
  -webkit-text-stroke: 1px var(--encre);
}
.de-virtuel[data-face="1"] i:nth-child(5),
.de-virtuel[data-face="2"] i:is(:nth-child(1), :nth-child(9)),
.de-virtuel[data-face="3"] i:is(:nth-child(1), :nth-child(5), :nth-child(9)),
.de-virtuel[data-face="4"] i:is(:nth-child(1), :nth-child(3), :nth-child(7), :nth-child(9)),
.de-virtuel[data-face="5"] i:is(:nth-child(1), :nth-child(3), :nth-child(5), :nth-child(7), :nth-child(9)),
.de-virtuel[data-face="6"] i:is(:nth-child(1), :nth-child(3), :nth-child(4), :nth-child(6), :nth-child(7), :nth-child(9)) { visibility: visible; }
.resultat {
  position: absolute;
  top: calc(100% + 0.8em);
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
  font-family: "Patrick Hand", cursive;
  font-size: 1.15em;
  color: var(--encre);
}
@media (max-width: 600px) {
  .de { gap: 0.6em; }
  .fleche-de { width: 2.4em; }
  .de-virtuel { width: 3.6em; height: 3.6em; padding: 0.4em; }
  .de-virtuel i { width: 0.6em; height: 0.6em; }
  .de-virtuel[data-face="0"]::after { font-size: 2.1em; }
}

/* Fin */
.fin { margin-top: 0.6em; text-align: center; }
.fin .mot-fin {
  display: block;
  font-family: "Bangers", "Impact", sans-serif;
  font-size: 3em;
  letter-spacing: 0.1em;
  color: var(--orange);
  -webkit-text-stroke: 1.5px var(--encre);
  text-shadow: 4px 4px 0 var(--encre);
  transform: rotate(-3deg);
  margin-bottom: 0.4em;
}
.appel { font-family: "Patrick Hand", cursive; font-size: 1.4em; color: var(--rouge); }

/* Page « Comment est née cette histoire » : texte centré, citation, fiches sur une table */
.contexte { font-size: 0.92em; text-align: center; }
.contexte .lien-retour { display: block; text-align: left; margin-bottom: 1em; }
.contexte h1 {
  font-family: "Uncial Antiqua", Georgia, serif;
  font-weight: 400;
  font-size: 2.4em;
  line-height: 1.1;
  color: var(--rouge);
  text-shadow: 2px 2px 0 var(--jaune);
  margin: 0.2em 0 0.1em;
}
.contexte-texte { max-width: 38em; margin: 0 auto; }
.citation {
  position: relative;
  max-width: 30em;
  margin: 2em auto;
  padding: 0.8em 1.2em;
  font-family: "Patrick Hand", cursive;
  font-size: 1.45em;
  line-height: 1.35;
  background: var(--papier);
  border: 2.5px solid var(--encre);
  border-radius: 1.3em;
  box-shadow: 4px 4px 0 var(--encre);
}
.citation .source { display: block; margin-top: 0.4em; font-family: "Nunito", sans-serif; font-size: 0.55em; color: var(--gris); }
.table-fiches { margin: 2.6em auto 0; max-width: 62em; padding: 1.8em 1.5em; background: var(--ciel); border: 2.5px solid var(--encre); }
.table-fiches .titre-table { display: block; font-family: "Bangers", "Impact", sans-serif; font-size: 1.5em; letter-spacing: 0.05em; color: var(--encre); margin-bottom: 1.1em; }
.miniatures { display: flex; justify-content: center; align-items: flex-start; flex-wrap: wrap; gap: 2em; }
.miniatures figure { margin: 0; }
.miniatures figcaption { margin-top: 0.8em; font-family: "Patrick Hand", cursive; font-size: 1.15em; color: var(--encre); }
.miniature { display: block; padding: 0; border: none; background: none; cursor: zoom-in; }
.miniature img { display: block; height: 15em; width: auto; border: 2px solid var(--encre); box-shadow: 4px 4px 0 var(--encre); transition: transform 0.2s ease; }
.miniatures figure:nth-child(1) img { transform: rotate(-3deg); }
.miniatures figure:nth-child(2) img { transform: rotate(1.5deg); }
.miniatures figure:nth-child(3) img { transform: rotate(-1deg); }
.miniatures .miniature:hover img { transform: rotate(0) scale(1.05); }
.contexte .credits { display: block; margin-top: 1.6em; font-size: 0.92em; color: var(--gris); }
.contexte .secondaires { display: flex; justify-content: center; margin-top: 1.4em; }
.agrandi { position: fixed; inset: 0; z-index: 100; display: flex; align-items: center; justify-content: center; padding: 2vh 2vw; background: rgba(28, 27, 36, 0.86); cursor: zoom-out; }
.agrandi img { max-width: 100%; max-height: 96vh; border: 3px solid var(--encre); }
@media (max-width: 600px) { .miniature img { height: 11em; } }

/* Page de l'arbre */
.arbre .lien-retour { display: block; font-size: 0.9em; }
.arbre-tete { text-align: center; margin-bottom: 1.5em; }
.arbre h1 {
  font-family: "Uncial Antiqua", Georgia, serif;
  font-weight: 400;
  font-size: 2.5em;
  line-height: 1.1;
  color: var(--rouge);
  text-shadow: 2px 2px 0 var(--jaune);
  margin: 0;
}
.arbre .arbre-sous-titre { display: block; font-family: "Patrick Hand", cursive; font-size: 1.3em; color: var(--gris); margin: 0.3em 0 1em; }
.arbre img { display: block; width: 100%; max-width: 760px; height: auto; margin: 0 auto; }

tw-link, .enchantment-link { color: var(--encre); font-weight: 700; text-decoration: none; }
tw-link:hover, .enchantment-link:hover { color: var(--rouge); }

@media (max-width: 600px) {
  tw-story { font-size: 0.98em; }
  .garde .grand-titre { font-size: 2.8em; }
  .chapitre .titre { font-size: 1.7em; }
}
@media (max-height: 620px) and (min-width: 801px) {
  tw-story:has(.garde) { padding-top: 0.6em; padding-bottom: 0.6em; }
  .garde { min-height: calc(100vh - 1.4em); gap: 0.6em; }
  .garde .synopsis { font-size: 0.95em; line-height: 1.45; }
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
    # Une flèche tracée à l'encre, comme un trait de mouvement de BD
    '<svg class="fleche-de" viewBox="0 0 60 40" aria-hidden="true"><g fill="none" stroke="#1c1b24" '
    'stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M4 30 C16 34 34 30 48 16"/><path d="M38 14 L49 15 L47 26"/></g></svg>'
    '<div class="lancer"><button class="de-virtuel" type="button" data-face="0" '
    'aria-label="Lancer le dé">' + "<i></i>" * 9 + '</button>'
    '<span class="resultat" aria-live="polite"></span></div>'
)

# Script commun à toutes les pages : fait rouler le dé puis affiche la face tirée, sans choisir
SCRIPT_DE = """
// Le dé roule puis affiche la face tirée ; il ne choisit jamais à la place du lecteur
document.addEventListener('click', function (evenement) {
  var de = evenement.target.closest('.de-virtuel');
  if (!de || de.classList.contains('roule')) return;
  var resultat = de.parentNode.querySelector('.resultat');
  var face = 1 + Math.floor(Math.random() * 6);
  var etapes = 0;
  de.classList.add('roule');
  resultat.textContent = '';
  var minuterie = setInterval(function () {
    de.setAttribute('data-face', 1 + Math.floor(Math.random() * 6));
    etapes += 1;
    if (etapes >= 8) {
      clearInterval(minuterie);
      de.setAttribute('data-face', face);
      de.classList.remove('roule');
      resultat.textContent = 'Le dé affiche ' + face + '.';
    }
  }, 75);
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
                    choix.append(f'<span class="relance">{ligne[2:]}</span>')
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
        # Sur les vrais tirages, un dé à lancer à droite du bloc consigne et choix ; il montre la face sans choisir
        lancer = DE_VIRTUEL if tirage else ""
        if tirage:
            # Sur le site, on lance le dé en cliquant dessus : la consigne le dit, une flèche le montre
            consigne = consigne.replace("Lance le dé", "Clique sur le dé", 1)
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
