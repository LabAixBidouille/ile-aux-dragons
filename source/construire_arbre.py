#!/usr/bin/env python3
"""Dessine images/arbre.svg, l'arbre de toutes les branches de l'histoire.

La position des cases et le tracé des flèches sont fixés à la main ci-dessous. Les titres
viennent de source/texte.md, et le script vérifie que les flèches dessinées correspondent
exactement aux renvois du texte : si le texte change, il s'arrête au lieu de dessiner un
arbre faux.

Usage, depuis la racine du dépôt : python3 source/construire_arbre.py
"""
import base64
import html
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
TEXTE = RACINE / "source" / "texte.md"
SORTIE = RACINE / "images" / "arbre.svg"
POLICES = {"Alegreya": RACINE / "fonts" / "Alegreya.woff2", "Skranji": RACINE / "fonts" / "Skranji.woff2",
           "Eagle Lake": RACINE / "fonts" / "EagleLake.woff2"}
OEUF = RACINE / "images" / "oeuf-arbre.png"

# Couleurs du site : bleu nuit pour le texte, rouge de la tuque d'Anna pour les numéros, bleu glace pour
# les cadres et les flèches, or de l'œuf pour les pastilles du tirage
NUIT, TUQUE, GLACE, GLACE_FONCE, OR_OEUF, ENCRE = "#24305a", "#c8322a", "#7fa3c8", "#5f84ad", "#f7b04f", "#2a2c3d"
GAUCHE, LARGEUR, HAUTEUR = 110, 900, 1580
L_CASE, H_CASE = 230, 66

CASES = {
    "P": (560, 60), 1: (560, 190), 2: (560, 320),
    3: (300, 490), 4: (820, 490), 5: (560, 650),
    6: (300, 820), 7: (820, 820), 8: (560, 980),
    9: (300, 1150), 10: (820, 1150), 11: (560, 1310), 12: (560, 1440),
}
FINS = {12}
ICONES = {2: "de", 5: "de", 8: "de"}

FLECHES = [
    ("P", 1, [(560, 126), (560, 190)], []),
    (1, 2, [(560, 256), (560, 320)], []),
    (2, 3, [(560, 430), (300, 430), (300, 490)], [("pair", 430, 430)]),
    (2, 4, [(560, 430), (820, 430), (820, 490)], [("impair", 690, 430)]),
    (3, 5, [(300, 556), (300, 620), (560, 620), (560, 650)], []),
    (4, 5, [(820, 556), (820, 620), (560, 620), (560, 650)], []),
    (5, 6, [(560, 760), (300, 760), (300, 820)], [("pair", 430, 760)]),
    (5, 7, [(560, 760), (820, 760), (820, 820)], [("impair", 690, 760)]),
    (6, 8, [(300, 886), (300, 950), (560, 950), (560, 980)], []),
    (7, 8, [(820, 886), (820, 950), (560, 950), (560, 980)], []),
    (8, 9, [(560, 1090), (300, 1090), (300, 1150)], [("pair", 430, 1090)]),
    (8, 10, [(560, 1090), (820, 1090), (820, 1150)], [("impair", 690, 1090)]),
    (9, 11, [(300, 1216), (300, 1280), (560, 1280), (560, 1310)], []),
    (10, 11, [(820, 1216), (820, 1280), (560, 1280), (560, 1310)], []),
    (11, 12, [(560, 1376), (560, 1440)], []),
]


def lire_texte():
    titres, renvois = {}, set()
    actuel = None
    for ligne in TEXTE.read_text(encoding="utf-8").split("\n"):
        m = re.match(r"## (Prologue|Chapitre (\d+))\. (.+)", ligne)
        if m:
            actuel = "P" if m.group(1) == "Prologue" else int(m.group(2))
            titres[actuel] = m.group(3)
        m = re.match(r"- .+ -> (\d+)$", ligne)
        if m:
            renvois.add((actuel, int(m.group(1))))
    return titres, renvois


def couper(texte, largeur=27):
    lignes, ligne = [], ""
    for mot in texte.split():
        if ligne and len(ligne) + 1 + len(mot) > largeur:
            lignes.append(ligne)
            ligne = mot
        else:
            ligne = f"{ligne} {mot}".strip()
    return lignes + [ligne]


def case(cle, titre):
    cx, haut = CASES[cle]
    x = cx - L_CASE / 2
    contour = OR_OEUF if cle in FINS else GLACE
    svg = [f'<rect x="{x}" y="{haut}" width="{L_CASE}" height="{H_CASE}" rx="14" fill="#fff" stroke="{contour}" '
           f'stroke-width="2.5" filter="url(#ombre)"/>']
    lignes = couper(titre)
    if len(lignes) > 2:
        lignes = couper(titre, 31)
    taille, interligne = (19, 20) if len(lignes) < 3 else (16, 17)
    y0 = haut + H_CASE / 2 - (len(lignes) - 1) * interligne / 2 + 6
    for i, l in enumerate(lignes):
        svg.append(f'<text x="{cx}" y="{y0 + i * interligne}" font-family="Alegreya" font-weight="600" font-size="{taille}" '
                   f'text-anchor="middle" fill="{NUIT}">{html.escape(l)}</text>')
    # Le numéro au-dessus de la case, en rouge tuque, comme « Chapitre 2 » sur les pages du livre
    etiquette = "Prologue" if cle == "P" else f"Chapitre {cle}"
    svg.append(f'<text x="{x + 6}" y="{haut - 7}" font-family="Skranji" font-weight="700" font-size="14.5" '
               f'fill="{TUQUE}">{etiquette}</text>')
    if cle in FINS:
        svg.append(f'<text x="{cx}" y="{haut + H_CASE + 44}" font-family="Eagle Lake" font-size="30" text-anchor="middle" '
                   f'fill="{NUIT}" style="paint-order:stroke" stroke="{GLACE}" stroke-width="0">FIN</text>')
    return "\n".join(svg)


def icone(cle, oeuf):
    """L'œuf de dragon sous les cases où l'on tire au sort"""
    cx, haut = CASES[cle]
    taille = 40
    y = haut + H_CASE + 2
    return (f'<line x1="{cx}" y1="{haut + H_CASE}" x2="{cx}" y2="{y + taille}" stroke="{GLACE_FONCE}" stroke-width="2"/>'
            f'<image href="data:image/png;base64,{oeuf}" x="{cx - taille / 2}" y="{y}" width="{taille}" height="{taille}"/>')


def fleche(points, etiquettes):
    trace = " ".join(f"{x},{y}" for x, y in points)
    # Halo blanc sous chaque flèche : là où deux flèches se croisent, la dernière tracée passe dessus
    svg = [f'<polyline points="{trace}" fill="none" stroke="#fff" stroke-width="8"/>',
           f'<polyline points="{trace}" fill="none" stroke="{GLACE_FONCE}" stroke-width="2" stroke-linejoin="round" '
           'marker-end="url(#pointe)"/>']
    for texte, x, y in etiquettes:
        # Pair / Impair dans une pastille dorée, comme dans l'encart du tirage
        mot = texte.capitalize()
        largeur = 8.6 * len(mot) + 22
        svg.append(f'<rect x="{x - largeur / 2}" y="{y - 12}" width="{largeur}" height="24" rx="12" fill="{OR_OEUF}"/>')
        svg.append(f'<text x="{x}" y="{y + 5}" font-family="Skranji" font-weight="700" font-size="14.5" text-anchor="middle" '
                   f'fill="{NUIT}">{html.escape(mot)}</text>')
    return "\n".join(svg)


def construire():
    titres, renvois = lire_texte()
    dessinees = {(a, b) for a, b, _, _ in FLECHES}
    assert set(titres) == set(CASES), f"Chapitres du texte et cases de l'arbre différents : {set(titres) ^ set(CASES)}"
    assert renvois == dessinees, f"Renvois du texte et flèches de l'arbre différents : {renvois ^ dessinees}"

    polices = "".join(
        f'@font-face{{font-family:"{nom}";src:url(data:font/woff2;base64,{base64.b64encode(f.read_bytes()).decode()}) format("woff2");}}'
        for nom, f in POLICES.items())
    oeuf = base64.b64encode(OEUF.read_bytes()).decode()
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{GAUCHE} 0 {LARGEUR} {HAUTEUR}" width="{LARGEUR}" height="{HAUTEUR}" font-family="Alegreya, serif">',
           f'<defs><style>{polices}</style>',
           f'<filter id="ombre" x="-10%" y="-20%" width="120%" height="160%"><feDropShadow dx="0" dy="6" stdDeviation="6" flood-color="{NUIT}" flood-opacity="0.18"/></filter>',
           f'<marker id="pointe" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{GLACE_FONCE}"/></marker></defs>']
    svg += [fleche(t, e) for _, _, t, e in FLECHES]
    svg += [icone(c, oeuf) for c in ICONES]
    svg += [case(c, titres[c]) for c in CASES]
    svg.append("</svg>")
    SORTIE.parent.mkdir(exist_ok=True)
    SORTIE.write_text("\n".join(svg), encoding="utf-8")
    print(f"{SORTIE} : {len(CASES)} cases, {len(FLECHES)} flèches")


if __name__ == "__main__":
    construire()
