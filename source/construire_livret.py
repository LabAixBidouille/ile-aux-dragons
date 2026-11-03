#!/usr/bin/env python3
"""Construit le livret imprimable des « Trois sœurs » à partir de source/texte.md.

Pages de 124 × 186 mm (format des livrets de l'atelier), texte en 11 pt ; un chapitre
trop long continue sur la page suivante. Chaque renvoi indique la page du chapitre visé :
le livret est donc composé deux fois, la seconde avec les bons numéros de page.

Produit trois PDF dans le dossier Impression du livre :
- LesTroisSoeurs_Livret_lecture.pdf : les pages dans l'ordre de lecture, pour relire ;
- LesTroisSoeurs_Livret_A4_bord_court.pdf et _bord_long.pdf : les pages imposées deux par
  deux sur A4 paysage, avec lignes de coupe et de pliure continues, très claires, pour une impression recto verso pliée en cahier
  (choisir le fichier selon le retournement de l'imprimante).

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
NOM = "LesTroisSoeurs"

MM = 72 / 25.4
LARGEUR_PAGE, HAUTEUR_PAGE = 124, 186          # mm
A4_L, A4_H = 297 * MM, 210 * MM                  # A4 paysage, en points

CSS = f"""
@font-face {{ font-family: "IM Fell English"; src: url("{(RACINE / 'fonts/IMFellEnglish.woff2').as_uri()}"); }}
@font-face {{ font-family: "IM Fell English"; font-style: italic; src: url("{(RACINE / 'fonts/IMFellEnglish-italique.woff2').as_uri()}"); }}
@font-face {{ font-family: "EB Garamond"; font-weight: 400 800; src: url("{(RACINE / 'fonts/EBGaramond.woff2').as_uri()}"); }}
@font-face {{ font-family: "EB Garamond"; font-style: italic; font-weight: 400 800; src: url("{(RACINE / 'fonts/EBGaramond-italique.woff2').as_uri()}"); }}

@page {{
  size: {LARGEUR_PAGE}mm {HAUTEUR_PAGE}mm;
  margin: 13mm 12mm 15mm 12mm;
  @bottom-center {{ content: counter(page); font-family: "EB Garamond"; font-size: 9.5pt; color: #5d6475; }}
}}
@page sans-numero {{ @bottom-center {{ content: none; }} }}

* {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; box-sizing: border-box; }}
/* EB Garamond a de petites lettres : 12 pt pour lire aussi bien qu'un 11 pt ordinaire */
html {{ font-family: "EB Garamond", serif; font-size: 12pt; line-height: 1.38; color: #22263a; }}
body {{ margin: 0; }}
p {{ margin: 0 0 0.55em; orphans: 2; widows: 2; }}
.page-seule {{ break-before: page; }}
.sans-numero {{ page: sans-numero; }}
.marque {{ font-size: 1pt; color: #ffffff; }}

/* Couverture */
.couverture {{ text-align: center; }}
.couverture .surtitre {{ font-family: "IM Fell English"; font-style: italic; font-size: 10.5pt; color: #5d6475; }}
.couverture .titre-livre {{ font-family: "IM Fell English"; font-size: 31pt; line-height: 0.95; letter-spacing: -0.3pt; color: #1d2b4f; margin: 1.5mm 0 1mm; }}
.couverture .autrices {{ font-family: "IM Fell English"; font-style: italic; font-size: 15pt; color: #a8740f; }}
.couverture img {{ display: block; width: 100%; margin: 5mm 0 4mm; }}
.couverture .resume p {{ font-size: 10.2pt; line-height: 1.3; margin-bottom: 0.45em; }}

/* Titres */
.numero {{ display: block; font-family: "IM Fell English"; font-style: italic; font-size: 12pt; color: #a8740f; margin-bottom: 0.5mm; }}
h1 {{ font-family: "IM Fell English"; font-weight: 400; font-size: 19pt; line-height: 1.05; color: #1d2b4f; margin: 0 0 4mm; }}
/* L'image remplit tout son cadre doré (recadrée au besoin), sans bande vide */
.illus img {{ display: block; width: 100%; height: 62mm; object-fit: cover; margin: 0 auto 4mm;
  border: 0.8mm solid #d99a2b; border-radius: 3.5mm; }}

.serre2 .illus img {{ height: 30mm; }}
.serre .illus img {{ height: 40mm; }}
.serre .separateur {{ margin: 2mm 0 2mm; }}
.serre .elan {{ margin-top: 1.5mm; }}

/* Séparateur, choix, fin */
.separateur {{ display: flex; align-items: center; justify-content: center; gap: 3mm; margin: 4mm 0 3mm; break-after: avoid; }}
.separateur::before, .separateur::after {{ content: ""; width: 20mm; height: 0.3mm; background: linear-gradient(to right, transparent, #d99a2b); }}
.separateur::after {{ background: linear-gradient(to left, transparent, #d99a2b); }}
.separateur img {{ width: 8mm; }}
.appel {{ font-family: "IM Fell English"; font-style: italic; font-size: 14pt; color: #a8740f; margin: 0 0 3mm; }}
/* Les choix ne restent jamais seuls en haut d'une page : ils emmènent le dernier paragraphe avec eux */
.suite {{ break-inside: avoid; break-before: avoid; }}
.consigne {{ font-family: "IM Fell English"; font-style: italic; font-size: 13pt; line-height: 1.25; color: #1d2b4f; margin: 0 0 2mm; }}
ul.choix {{ margin: 0; padding: 0; list-style: none; }}
ul.choix li {{ margin: 0 0 1.6mm; padding-left: 4.5mm; text-indent: -4.5mm; color: #1d2b4f; font-weight: 700; }}
ul.choix li::before {{ content: "✦"; color: #d99a2b; display: inline-block; width: 4.5mm; text-indent: 0; font-weight: 400; }}
.elan {{ text-align: center; margin-top: 3mm; }}
.elan span {{ display: inline-block; font-family: "IM Fell English"; font-size: 12pt; color: #1d2b4f;
  border: 0.3mm solid #d99a2b; outline: 0.3mm solid #d99a2b; outline-offset: 0.9mm; padding: 1.4mm 5mm 1.6mm; }}
.elan span::before, .elan span::after {{ content: " ✦ "; color: #d99a2b; font-size: 8pt; }}
.fin {{ text-align: center; font-family: "IM Fell English"; font-size: 24pt; letter-spacing: 2pt; color: #1d2b4f; margin-top: 2mm; }}

/* Pages de fin et de contexte */
.contexte h2 {{ font-family: "IM Fell English"; font-weight: 400; font-size: 17pt; color: #1d2b4f; margin: 0 0 4mm; }}
.contexte p {{ font-size: 10.3pt; line-height: 1.32; }}
.contexte .credits {{ font-size: 9.5pt; color: #5d6475; }}
.fiches {{ display: grid; grid-template-columns: 1fr 1fr; gap: 3mm; }}
.fiches img {{ width: 100%; display: block; }}
.fiches .pleine {{ grid-column: 1 / -1; }}
.dos {{ display: flex; flex-direction: column; justify-content: flex-end; height: 156mm; text-align: center;
  font-size: 9.5pt; color: #5d6475; }}
"""

def _separateur():
    """Séparateur : la patte de loup étoilée de Manon entre deux traits dorés."""
    return f'<div class="separateur"><img src="{(RACINE / "images/embleme.png").as_uri()}" alt=""></div>'


SEPARATEUR = _separateur()


def e(texte):
    return html.escape(texte, quote=False)


def italique(texte):
    return re.sub(r"//(.+?)//", r"<i>\1</i>", e(texte))


def avec_page(texte, pages):
    """Ajoute la page du dernier chapitre cité : « poursuis au chapitre 3. » → « … chapitre 3 (page 9). »"""
    m = list(re.finditer(r"chapitre (\d+)", texte))[-1]
    page = pages.get(int(m.group(1)), "00")
    return texte[: m.end()] + f" (page {page})" + texte[m.end():]



def chapitre(ch, pages):
    cle = 0 if ch["nom"] == "Prologue" else int(ch["nom"].split()[-1])
    classe = "page-seule" + (" serre" if cle in SERRES else "") + (" serre2" if cle in SERRES2 else "")
    morceaux = [f'<section class="{classe}"><span class="marque">@@CH{cle}@@</span>']
    image = RACINE / "images" / "chapitres" / f"{illustration(ch['nom'])}.jpg"
    if image.exists():
        morceaux.append(f'<div class="illus"><img src="{image.as_uri()}" alt=""></div>')
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

    # Le bouton du prologue n'existe que sur le site : dans le livret, on tourne simplement la page
    # Dans un livre, inutile d'écrire « Poursuis au chapitre suivant » : on tourne simplement la page.
    # Le renvoi reste quand il saute des chapitres (6 → 8, par exemple)
    if not consigne and len(choix) == 1 and cibles[0] == cle + 1:
        choix = []
    suite = [] if appel else [SEPARATEUR]
    if consigne:
        suite.append(f'<p class="consigne">{e(consigne)}</p><ul class="choix">'
                     + "".join(f"<li>{e(avec_page(c, pages))}</li>" for c in choix) + "</ul>")
    elif len(choix) > 1:
        suite.append('<ul class="choix">' + "".join(f"<li>{e(avec_page(c, pages))}</li>" for c in choix) + "</ul>")
    elif choix:
        suite.append(f'<div class="elan"><span>{e(avec_page(choix[0], pages))}</span></div>')
    if fin:
        suite.append('<div class="fin">FIN</div>')
    if consigne or choix or fin:
        morceaux.append(f'<div class="suite">{"".join(suite)}</div>')
    morceaux.append("</section>")
    return "".join(morceaux)


def document(pages, blanches=0):
    couverture = (
        '<section class="couverture sans-numero">'
        '<div class="surtitre">Une histoire dont le lecteur est le héros</div>'
        f'<div class="titre-livre">{e(TITRE)}</div>'
        f'<img src="{(RACINE / "images/couverture.jpg").as_uri()}" alt="">'
        '<div class="resume">' + "".join(f"<p>{e(p)}</p>" for p in SYNOPSIS.split("\n\n")) + "</div></section>"
    )
    fiches = RACINE / "images" / "fiches"
    # Texte de Manon, commun aux livres de l'atelier ; seule la phrase finale est en gras
    paragraphes = [q for p in CONTEXTE for q in p.split("\n\n")]
    contexte = (
        '<section class="page-seule contexte"><h2>Comment est née cette histoire</h2>'
        + "".join(f"<p>{italique(p).replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')}</p>" for p in paragraphes)
        + '<p class="credits">Une histoire librement inspirée du récit de deux jeunes autrices.<br>Réalisation du livre : '
          "Laboratoire d’Aix-périmentation et de Bidouille.</p></section>"
        '<section class="page-seule contexte"><h2>Les fiches de l’atelier</h2><div class="fiches">'
        f'<img src="{(fiches / "fiche_recit.jpg").as_uri()}" alt="">'
        f'<img src="{(fiches / "fiche_personnage_rose.jpg").as_uri()}" alt="">'
        f'<img class="pleine" src="{(fiches / "fiche_situation_1.jpg").as_uri()}" alt="">'
        "</div></section>"
    )
    chapitres = "".join(chapitre(ch, pages) for ch in lire_chapitres())
    vides = '<section class="page-seule sans-numero">&nbsp;</section>' * blanches
    dos = ('<section class="page-seule sans-numero"><div class="dos">'
           f"<p><b>{e(TITRE)}</b>, une histoire librement inspirée du récit imaginé par deux jeunes autrices pendant l’atelier "
           "« La quête du curry, une histoire dont tu es le héros », dans les bibliothèques Méjanes "
           "d’Aix-en-Provence, en octobre 2026.</p><p>Réalisation du livre : Laboratoire d’Aix-périmentation et de Bidouille.</p>"
           "</div></section>")
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>{CSS}</style></head>'
            f"<body>{couverture}{contexte}{chapitres}{vides}{dos}</body></html>")


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
