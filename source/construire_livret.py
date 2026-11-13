#!/usr/bin/env python3
"""Construit le livret imprimable de « L'île aux dragons » à partir de source/texte.md.

Pages de 124 × 186 mm (format des livrets de l'atelier). Les planches de ce livre sont des pages entières
au format portrait : chaque chapitre s'ouvre sur sa planche en pleine page, puis le texte suit ; un
chapitre trop long continue sur la page suivante. Chaque renvoi indique la page du chapitre visé : le
livret est donc composé plusieurs fois, jusqu'à ce que les numéros de page se stabilisent.

Le style reprend celui du site, adapté à l'impression : titres en Eagle Lake, « Chapitre n » en Skranji
rouge tuque, texte en Alegreya, encart du tirage en Literata sur un bleu glace clair (le bleu nuit du site
coûterait trop d'encre), pastilles dorées Pair / Impair, séparateur à l'œuf de dragon.

Produit trois PDF dans le dossier Impression du livre :
- IleAuxDragons_Livret_lecture.pdf : les pages dans l'ordre de lecture, pour relire ;
- IleAuxDragons_Livret_A4_bord_court.pdf et _bord_long.pdf : les pages imposées deux par deux sur A4
  paysage, avec lignes de coupe et de pliure continues, très claires, pour une impression recto verso
  pliée en cahier (choisir le fichier selon le retournement de l'imprimante).

Nécessite Google Chrome, pdftotext (poppler) et le module Python pypdf.
Usage, depuis la racine du dépôt : python3 source/construire_livret.py
"""
import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter, Transformation

sys.path.insert(0, str(Path(__file__).resolve().parent))
from construire_site import AUTRICES, CONTEXTE, SYNOPSIS, TITRE, illustration, lire_chapitres  # noqa: E402

RACINE = Path(__file__).resolve().parent.parent
IMPRESSION = RACINE.parent / "Impression"
NOM = "IleAuxDragons"

MM = 72 / 25.4
LARGEUR_PAGE, HAUTEUR_PAGE = 124, 186          # mm
A4_L, A4_H = 297 * MM, 210 * MM                  # A4 paysage, en points

NUIT, TUQUE, GLACE, NEIGE, OR_OEUF, ENCRE, GRIS = "#24305a", "#c8322a", "#7fa3c8", "#e3ecf6", "#f7b04f", "#2a2c3d", "#6a6e80"
# Trait bleu glace effilé, celui du bouton Commencer et des séparateurs du site
TRAIT = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 14'%3E"
         "%3Cpath d='M118 7 C80 1.5 40 4.5 8 7 C40 9.5 80 12.5 118 7 Z' fill='%237fa3c8'/%3E"
         "%3Ccircle cx='5' cy='7' r='3' fill='%237fa3c8'/%3E%3C/svg%3E")

CSS = f"""
@font-face {{ font-family: "Eagle Lake"; src: url("{(RACINE / 'fonts/EagleLake.woff2').as_uri()}"); }}
@font-face {{ font-family: "Skranji"; font-weight: 700; src: url("{(RACINE / 'fonts/Skranji.woff2').as_uri()}"); }}
@font-face {{ font-family: "Alegreya"; font-weight: 400 900; src: url("{(RACINE / 'fonts/Alegreya.woff2').as_uri()}"); }}
@font-face {{ font-family: "Alegreya"; font-style: italic; font-weight: 400 900; src: url("{(RACINE / 'fonts/Alegreya-i.woff2').as_uri()}"); }}
@font-face {{ font-family: "Literata"; font-weight: 200 900; src: url("{(RACINE / 'fonts/Literata.woff2').as_uri()}"); }}
@font-face {{ font-family: "Literata"; font-style: italic; font-weight: 200 900; src: url("{(RACINE / 'fonts/Literata-i.woff2').as_uri()}"); }}

@page {{
  size: {LARGEUR_PAGE}mm {HAUTEUR_PAGE}mm;
  margin: 13mm 12mm 15mm 12mm;
  @bottom-center {{ content: counter(page); font-family: "Alegreya"; font-size: 9.5pt; color: {GRIS}; }}
}}
@page sans-numero {{ @bottom-center {{ content: none; }} }}

* {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; box-sizing: border-box; }}
/* Alegreya a de petites lettres : 12 pt pour lire aussi bien qu'un 11 pt ordinaire */
html {{ font-family: "Alegreya", serif; font-size: 12pt; line-height: 1.4; color: {ENCRE}; }}
body {{ margin: 0; }}
p {{ margin: 0 0 0.55em; orphans: 2; widows: 2; }}
.page-seule {{ break-before: page; }}
.sans-numero {{ page: sans-numero; }}
.marque {{ font-size: 1pt; color: #ffffff; }}

/* Couverture intérieure : le bleu nuit du site, à fond perdu, comme la page d'accueil */
@page couverture {{ margin: 0; @bottom-center {{ content: none; }} }}
/* contenu centré dans toute la hauteur : même espace en haut et en bas */
.couverture {{ page: couverture; height: {HAUTEUR_PAGE}mm; overflow: hidden; padding: 2.3mm 12mm 0; text-align: center; color: #eef1fb;
  display: flex; flex-direction: column; justify-content: center;
  /* les 2.3 mm en haut compensent la place réservée aux jambages de la dernière ligne : le blanc est le même en haut et en bas */
  background: radial-gradient(ellipse at 70% 0%, #5065a0 0%, #33427a 45%, #252f58 100%); }}
.couverture .surtitre {{ font-family: "Skranji"; font-weight: 700; font-size: 10pt; color: #b9d0ea; }}
.couverture .titre-livre {{ font-family: "Eagle Lake"; font-size: 28pt; line-height: 1.05; color: #ffffff;
  text-shadow: 0.6mm 0.6mm 0 {GLACE}; margin: 1.5mm 0 1mm; }}
.couverture .titre-livre span {{ color: {OR_OEUF}; }}
.couverture .autrices {{ font-family: "Skranji"; font-weight: 700; font-size: 13pt; color: #ffffff; }}
.couverture img {{ display: block; width: 72mm; margin: 4mm auto 4mm; border-radius: 3mm; }}
.couverture .resume p {{ font-size: 10pt; line-height: 1.32; margin-bottom: 0.45em; color: #e2e7f6; }}

/* Planche du chapitre : une page entière */
.planche .cadre {{ display: flex; align-items: center; justify-content: center; height: 150mm; }}
.planche img {{ display: block; max-width: 100%; max-height: 150mm; border-radius: 3mm; }}
.planche .marque {{ display: block; line-height: 1; }}

/* Titres */
.numero {{ display: block; font-family: "Skranji"; font-weight: 700; font-size: 11pt; color: {TUQUE}; margin-bottom: 0.5mm; }}
h1 {{ font-family: "Eagle Lake"; font-weight: 400; font-size: 18pt; line-height: 1.1; color: {NUIT}; margin: 0 0 4mm; }}

/* Resserrements pour les fins de chapitre trop courtes */
.serre p {{ margin-bottom: 0.4em; }}
.serre .separateur {{ margin: 2mm 0 2mm; }}
.serre2 {{ font-size: 11.5pt; line-height: 1.33; }}

/* Séparateur : l'œuf de dragon entre deux traits bleu glace, aligné sur la gauche du texte */
.separateur {{ display: flex; align-items: center; justify-content: flex-start; gap: 1mm; margin: 4mm 0 3mm; break-after: avoid; }}
.separateur::before, .separateur::after {{ content: ""; width: 14mm; height: 3mm; background: url("{TRAIT}") no-repeat center / contain; }}
.separateur::after {{ transform: scaleX(-1); }}
.separateur img {{ width: 7mm; }}
.appel {{ font-family: "Eagle Lake"; font-size: 13pt; color: {NUIT}; margin: 0 0 3mm; }}
/* Les choix ne restent jamais seuls en haut d'une page : ils emmènent le dernier paragraphe avec eux */
.suite {{ break-inside: avoid; break-before: avoid; }}
/* Encart du tirage, en Literata sur bleu glace clair */
.tirage {{ font-family: "Literata"; font-size: 10.5pt; line-height: 1.45; background: {NEIGE}; border-radius: 3mm;
  padding: 3.5mm 4.5mm; margin-top: 4mm; }}
.consigne {{ font-style: italic; color: {NUIT}; margin: 0 0 2mm; }}
ul.choix {{ margin: 0; padding: 0; list-style: none; }}
ul.choix li {{ margin: 0 0 1.4mm; color: {NUIT}; font-weight: 700; }}
.pastille {{ display: inline-block; min-width: 6mm; padding: 0.3mm 2mm 0.1mm; margin-right: 1.8mm; border-radius: 3mm;
  background: {OR_OEUF}; color: {NUIT}; font-family: "Skranji"; font-weight: 700; font-size: 9.5pt; text-align: center; }}
/* Renvoi seul : le bouton bleu glace du site, flèche rouge */
.elan {{ margin-top: 3mm; }}
.elan span {{ display: inline-block; font-family: "Skranji"; font-weight: 700; font-size: 11pt; color: {NUIT};
  background: {NEIGE}; border-bottom: 0.8mm solid {GLACE}; border-radius: 2.5mm; padding: 1.4mm 4.5mm 1.2mm; }}
.elan span::after {{ content: " →"; font-family: "Alegreya"; color: {TUQUE}; }}
.fin {{ text-align: center; font-family: "Eagle Lake"; font-size: 26pt; color: {NUIT}; text-shadow: 0.6mm 0.6mm 0 {NEIGE}; margin-top: 4mm; }}

/* Pages de fin et de contexte */
.contexte h2 {{ font-family: "Eagle Lake"; font-weight: 400; font-size: 16pt; color: {NUIT}; margin: 0 0 4mm; }}
.contexte p {{ font-size: 9.9pt; line-height: 1.3; margin-bottom: 0.45em; }}
.contexte .credits {{ font-size: 9.5pt; color: {GRIS}; }}
.fiches {{ display: grid; grid-template-columns: 1fr 1fr; gap: 3mm; }}
.fiches img {{ width: 100%; display: block; }}
.fiches .pleine {{ grid-column: 1 / -1; }}
.dos {{ display: flex; flex-direction: column; justify-content: flex-end; height: 156mm; text-align: center;
  font-size: 9.5pt; color: {GRIS}; }}

/* L'arbre de l'histoire : une page à petites marges, le titre en haut, l'arbre aussi grand que possible */
@page arbre {{ margin: 8mm 6mm 9mm; @bottom-center {{ content: none; }} }}
.arbre {{ page: arbre; height: 168mm; display: flex; flex-direction: column; align-items: center; }}
.arbre h2 {{ margin-bottom: 2mm; }}
.arbre img {{ flex: 1; min-height: 0; width: 100%; object-fit: contain; }}
"""

SEPARATEUR = f'<div class="separateur"><img src="{(RACINE / "images/oeuf.png").as_uri()}" alt=""></div>'


# Espaces insécables de la typographie française : un guillemet, un point d'interrogation ou un deux-points
# ne se retrouve jamais seul en début de ligne
INSECABLES = [("« ", "«\u00a0"), (" »", "\u00a0»"), (" :", "\u00a0:"), (" ?", "\u00a0?"), (" !", "\u00a0!"), (" ;", "\u00a0;")]


def e(texte):
    for avant, apres in INSECABLES:
        texte = texte.replace(avant, apres)
    return html.escape(texte, quote=False)


def italique(texte):
    return re.sub(r"//(.+?)//", r"<i>\1</i>", e(texte))


def avec_page(texte, pages):
    """Ajoute la page du dernier chapitre cité : « poursuis au chapitre 3. » → « … chapitre 3 (page 9). »"""
    m = list(re.finditer(r"chapitre (\d+)", texte))[-1]
    page = pages.get(int(m.group(1)), "00")
    return texte[: m.end()] + f" (page {page})" + texte[m.end():]


def choix_html(texte, pages):
    """« Un nombre pair : poursuis… » devient la pastille dorée Pair suivie de « poursuis… »"""
    texte = avec_page(texte, pages)
    m = re.match(r"(\d|Un nombre pair|Un nombre impair) : (.*)", texte)
    if not m:
        return e(texte)
    pastille = {"Un nombre pair": "Pair", "Un nombre impair": "Impair"}.get(m[1], m[1])
    return f'<span class="pastille">{pastille}</span>{e(m[2])}'


def chapitre(ch, pages):
    cle = 0 if ch["nom"] == "Prologue" else int(ch["nom"].split()[-1])
    morceaux = [f'<section class="page-seule planche"><span class="marque">@@CH{cle}@@</span>']
    image = RACINE / "images" / "chapitres" / f"{illustration(ch['nom'])}.jpg"
    if image.exists():
        morceaux.append(f'<div class="cadre"><img src="{image.as_uri()}" alt=""></div>')
    morceaux.append("</section>")
    classe = "page-seule" + (" serre" if cle in SERRES else "") + (" serre2" if cle in SERRES2 else "")
    morceaux.append(f'<section class="{classe}">')
    morceaux.append(f'<span class="numero">{e(ch["numero"])}</span><h1>{e(ch["titre"])}</h1>')
    corps, consigne, choix, fin, appel = [], None, [], False, False
    cibles = []
    for p in ch["paragraphes"]:
        if p.startswith("- "):
            for ligne in p.split("\n"):
                texte, cible = ligne[2:].rsplit(" -> ", 1)
                choix.append(texte)
                cibles.append(int(cible))
        elif p == "FIN":
            fin = True
        elif p.startswith("**") and p.endswith("**"):
            interieur = p[2:-2]
            if interieur.startswith("Lance le dé") or interieur.startswith("Te souviens-tu"):
                consigne = interieur
            else:
                corps.append(f'{SEPARATEUR}<p class="appel">{e(interieur)}</p>')
                appel = True
        else:
            corps.append(f"<p>{e(p)}</p>")
    morceaux += corps

    # Dans un livre, inutile d'écrire « Poursuis au chapitre suivant » : on tourne simplement la page.
    # Le renvoi reste quand il saute des chapitres (3 → 5, par exemple)
    if not consigne and len(choix) == 1 and cibles[0] == cle + 1:
        choix = []
    # Pas de séparateur au-dessus de l'encart du tirage, comme sur le site
    suite = [] if (appel or consigne) else [SEPARATEUR]
    if consigne:
        suite.append(f'<div class="tirage"><p class="consigne">{e(consigne)}</p><ul class="choix">'
                     + "".join(f"<li>{choix_html(c, pages)}</li>" for c in choix) + "</ul></div>")
    elif len(choix) > 1:
        suite.append('<ul class="choix">' + "".join(f"<li>{choix_html(c, pages)}</li>" for c in choix) + "</ul>")
    elif choix:
        # Le point final disparaît devant la flèche du bouton
        suite.append(f'<div class="elan"><span>{e(avec_page(choix[0].rstrip("."), pages))}</span></div>')
    if fin:
        suite.append('<div class="fin">FIN</div>')
    if consigne or choix or fin or suite:
        morceaux.append(f'<div class="suite">{"".join(suite)}</div>')
    morceaux.append("</section>")
    return "".join(morceaux)


def document(pages, blanches=0):
    titre = e(TITRE).replace("dragons", "<span>dragons</span>")
    # Couverture pleine page dans le style du livre, le résumé seul sur la page suivante
    couverture = (
        '<style>.cv { page: couverture; position: relative; height: 185.5mm; overflow: hidden; }.cv .cv-entete { position: absolute; left: 0; right: 0; text-align: center; padding: 0 8mm; z-index: 2; }.cv .cv-image { position: absolute; left: 0; right: 0; bottom: 0; overflow: hidden; }.cv .cv-image img { display: block; height: 100%; width: auto; position: absolute; top: 0; margin: 0; border: 0; border-radius: 0; }.cv-resume { display: flex; flex-direction: column; justify-content: center; height: 156mm; text-align: center; }.cv { background: #252f58; } .cv > img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: 30% center; margin: 0; border-radius: 0; }.cv .voile { position: absolute; left: 0; right: 0; top: 0; height: 80mm; background: linear-gradient(to bottom, rgba(24,32,61,0.92) 0%, rgba(24,32,61,0.75) 40%, rgba(24,32,61,0) 100%); }.cv .cv-entete { top: 14mm; } .cv .surtitre { font-family: "Skranji"; font-weight: 700; font-size: 10pt; color: #b9d0ea; text-shadow: 0 0 2mm rgba(0,0,0,0.6); }.cv .titre { font-family: "Eagle Lake"; font-size: 34pt; line-height: 1.05; color: #fff; margin: 2mm 0; text-shadow: 0.8mm 0.8mm 0 #24305a, 0 0 4mm rgba(0,0,0,0.7); }.cv .titre span { color: #f7b04f; } .cv .auteur { font-family: "Skranji"; font-weight: 700; font-size: 15pt; color: #fff; text-shadow: 0 0 3mm rgba(0,0,0,0.7); }.cv-resume p { font-size: 12pt; line-height: 1.5; }</style>'
        '<section class="cv sans-numero"><div class="cv-entete"><div class="surtitre">Une histoire dont le lecteur est le héros</div><div class="titre">L’île aux <span>dragons</span></div><div class="auteur">' + e(AUTRICES) + '</div></div>'
        f'<img src="{(RACINE / "images/couverture.jpg").as_uri()}" alt=""><div class="voile"></div>'
        '</section><section class="page-seule sans-numero"><div class="cv-resume">'
        + "".join(f"<p>{e(p)}</p>" for p in SYNOPSIS.split("\n\n")) + '' + "</div></section>"
    )
    fiches = RACINE / "images" / "fiches"
    # Texte de Manon, commun aux livres de l'atelier ; seule la phrase finale est en gras
    paragraphes = [q for p in CONTEXTE for q in p.split("\n\n")]
    contexte = (
        '<section class="page-seule contexte"><h2>Comment est née cette histoire</h2>'
        + "".join(f"<p>{italique(p).replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')}</p>" for p in paragraphes)
        + '<p class="credits">Une histoire librement inspirée du récit de Louisa et de June.<br>Réalisation du livre : '
          "Laboratoire d’Aix-périmentation et de Bidouille.</p></section>"
        '<section class="page-seule contexte"><h2>Les fiches de l’atelier</h2><div class="fiches">'
        f'<img src="{(fiches / "fiche_recit.jpg").as_uri()}" alt="">'
        f'<img src="{(fiches / "fiche_personnage_croquemou.jpg").as_uri()}" alt="">'
        f'<img class="pleine" src="{(fiches / "fiche_situation_1.jpg").as_uri()}" alt="">'
        "</div></section>"
    )
    chapitres = "".join(chapitre(ch, pages) for ch in lire_chapitres())
    arbre = ('<section class="page-seule contexte arbre sans-numero"><h2>L’arbre de l’histoire</h2>'
             f'<img src="{(RACINE / "images/arbre.svg").as_uri()}" alt=""></section>')
    vides = '<section class="page-seule sans-numero">&nbsp;</section>' * blanches
    dos = ('<section class="page-seule sans-numero"><div class="dos">'
           f"<p><b>{e(TITRE)}</b>, une histoire librement inspirée du récit imaginé par {e(AUTRICES)} pendant l’atelier "
           "« La quête du curry, une histoire dont tu es le héros », à la bibliothèque Li Campaneto "
           "(bibliothèques Méjanes, Aix-en-Provence), en octobre 2026.</p><p>Réalisation du livre : Laboratoire d’Aix-périmentation et de Bidouille.</p>"
           "</div></section>")
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>{CSS}</style></head>'
            f"<body>{couverture}{chapitres}{arbre}{contexte}{vides}{dos}</body></html>")


def imprimer(source_html, pdf):
    subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=8000", f"--print-to-pdf={pdf}", source_html.as_uri()],
                   check=True, capture_output=True)


def reperer_pages(pdf):
    """Numéro de page où commence chaque chapitre (0 pour le prologue), d'après les marques invisibles."""
    pages = {}
    total = len(PdfReader(str(pdf)).pages)
    for n in range(1, total + 1):
        texte = subprocess.run(["pdftotext", "-f", str(n), "-l", str(n), str(pdf), "-"],
                               capture_output=True, text=True, check=True).stdout
        for cle in re.findall(r"@@CH(\d+)@@", texte):
            pages[int(cle)] = n
    return pages, total


# Une page de fin de chapitre qui ne porte que quelques lignes paraît coupée bizarrement : ces chapitres
# sont resserrés (image moins haute, séparateur plus proche) pour tenir sur une page de moins
SEUIL_QUEUE = 8
SERRES = set()        # premier resserrement
SERRES2 = set()       # second, si le premier ne suffit pas


def queues_courtes(pdf, pages):
    """Chapitres sur plusieurs pages dont la dernière page ne porte que quelques lignes."""
    debuts = sorted((page, cle) for cle, page in pages.items())
    courtes = set()
    for (debut, cle), (suivant, _) in zip(debuts, debuts[1:]):
        fin = suivant - 1
        if fin <= debut:
            continue
        texte = subprocess.run(["pdftotext", "-f", str(fin), "-l", str(fin), str(pdf), "-"],
                               capture_output=True, text=True, check=True).stdout
        lignes = [l for l in texte.splitlines() if l.strip() and not l.strip().isdigit()]
        if len(lignes) <= SEUIL_QUEUE:
            courtes.add(cle)
    return courtes


def composer(dossier):
    source = Path(dossier) / "livret.html"
    pdf = Path(dossier) / "livret.pdf"
    pages = {}
    for _ in range(6):
        for _ in range(4):
            source.write_text(document(pages), encoding="utf-8")
            imprimer(source, pdf)
            nouvelles, total = reperer_pages(pdf)
            if nouvelles == pages:
                break
            pages = nouvelles
        else:
            raise SystemExit("Les numéros de page ne se stabilisent pas.")
        courtes = queues_courtes(pdf, pages)
        nouvelles = (courtes - SERRES) | {c for c in courtes & SERRES if c not in SERRES2}
        if not nouvelles:
            break
        SERRES2.update(courtes & SERRES)
        SERRES.update(courtes)
        pages = {}
    # Là où même le second resserrement ne suffit pas, la fin du chapitre est longue par nature
    # (dernier paragraphe et choix) : on rend à l'image sa taille normale plutôt que de la réduire pour rien
    inutiles = queues_courtes(pdf, pages) & SERRES2
    if inutiles:
        SERRES.difference_update(inutiles)
        SERRES2.difference_update(inutiles)
        pages = {}
        for _ in range(5):
            source.write_text(document(pages), encoding="utf-8")
            imprimer(source, pdf)
            nouvelles, total = reperer_pages(pdf)
            if nouvelles == pages:
                break
            pages = nouvelles
    # Pages blanches avant le dos pour arriver à un multiple de 4 (cahier plié)
    blanches = (-total) % 4
    if blanches:
        source.write_text(document(pages, blanches), encoding="utf-8")
        imprimer(source, pdf)
        assert reperer_pages(pdf)[0] == pages
    return pdf, pages


def traits_de_coupe(dossier):
    """Page A4 paysage avec des lignes continues très claires : lignes de coupe sur tout le tour des deux
    pages côte à côte, prolongées jusqu'aux bords de la feuille pour poser la règle, et ligne de pliure
    au milieu, d'une autre teinte."""
    x0, y0 = (297 - 2 * LARGEUR_PAGE) / 2, (210 - HAUTEUR_PAGE) / 2
    gauche, droite, haut, bas = x0, x0 + 2 * LARGEUR_PAGE, y0, y0 + HAUTEUR_PAGE
    coupe = [f'<line x1="0" y1="{y}" x2="297" y2="{y}"/>' for y in (haut, bas)]
    coupe += [f'<line x1="{x}" y1="0" x2="{x}" y2="210"/>' for x in (gauche, droite)]
    pli = x0 + LARGEUR_PAGE
    source = Path(dossier) / "traits.html"
    source.write_text(
        '<!doctype html><html><head><style>@page { size: 297mm 210mm; margin: 0; } body { margin: 0; }</style></head>'
        '<body><svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">'
        f'<g stroke="#c9c9c9" stroke-width="0.2">{"".join(coupe)}</g>'
        f'<line x1="{pli}" y1="0" x2="{pli}" y2="210" stroke="#b7cbe6" stroke-width="0.2"/>'
        '</svg></body></html>', encoding="utf-8")
    pdf = Path(dossier) / "traits.pdf"
    imprimer(source, pdf)
    return PdfReader(str(pdf)).pages[0]


def imposer(lecture, traits, sortie, bord_long):
    pages = PdfReader(str(lecture)).pages
    n = len(pages)
    assert n % 4 == 0
    x0 = (A4_L - 2 * LARGEUR_PAGE * MM) / 2
    y0 = (A4_H - HAUTEUR_PAGE * MM) / 2
    ecrivain = PdfWriter()

    def face(gauche, droite, retournee):
        feuille = PageObject.create_blank_page(width=A4_L, height=A4_H)
        feuille.merge_page(traits)
        for indice, x in ((gauche, x0), (droite, x0 + LARGEUR_PAGE * MM)):
            feuille.merge_transformed_page(pages[indice - 1], Transformation().translate(x, y0))
        if retournee:
            feuille.rotate(180)
        ecrivain.add_page(feuille)

    for i in range(n // 4):
        face(n - 2 * i, 1 + 2 * i, False)          # recto : dernière page à gauche, première à droite
        face(2 + 2 * i, n - 1 - 2 * i, bord_long)  # verso
    with open(sortie, "wb") as f:
        ecrivain.write(f)


def construire():
    IMPRESSION.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as dossier:
        pdf, pages = composer(dossier)
        lecture = IMPRESSION / f"{NOM}_Livret_lecture.pdf"
        lecture.write_bytes(pdf.read_bytes())
        traits = traits_de_coupe(dossier)
        imposer(lecture, traits, IMPRESSION / f"{NOM}_Livret_A4_bord_court.pdf", bord_long=False)
        imposer(lecture, traits, IMPRESSION / f"{NOM}_Livret_A4_bord_long.pdf", bord_long=True)
    total = len(PdfReader(str(lecture)).pages)
    print(f"{lecture} : {total} pages, soit {total // 4} feuilles A4 recto verso")
    print("Chapitres resserrés :", ", ".join(("P" if c == 0 else str(c)) + ("+" if c in SERRES2 else "") for c in sorted(SERRES)) or "aucun")
    restantes = queues_courtes(lecture, pages)
    print("Fins de chapitre encore courtes :", ", ".join("P" if c == 0 else str(c) for c in sorted(restantes)) or "aucune")
    print("Pages des chapitres :", ", ".join(f"{'P' if k == 0 else k}→{v}" for k, v in sorted(pages.items())))


if __name__ == "__main__":
    construire()
