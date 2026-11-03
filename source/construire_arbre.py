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
POLICE = RACINE / "fonts" / "Nunito.woff2"

# Couleurs du livre : rouge de la tuque, jaune de Croquemou, encre noire, bleu de la neige
ORANGE, JAUNE_CLAIR, VIOLET, MENTHE, ENCRE = "#c23a2b", "#fdf0c4", "#1c1b24", "#4f6aa8", "#1c1b24"
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
    (2, 3, [(560, 430), (300, 430), (300, 490)], [("4", 430, 430)]),
    (2, 4, [(560, 430), (820, 430), (820, 490)], [("2", 690, 430)]),
    (3, 5, [(300, 556), (300, 620), (530, 620), (530, 650)], []),
    (4, 5, [(820, 556), (820, 620), (590, 620), (590, 650)], []),
    (5, 6, [(560, 760), (300, 760), (300, 820)], [("6", 430, 760)]),
    (5, 7, [(560, 760), (820, 760), (820, 820)], [("1", 690, 760)]),
    (6, 8, [(300, 886), (300, 950), (530, 950), (530, 980)], []),
    (7, 8, [(820, 886), (820, 950), (590, 950), (590, 980)], []),
    (8, 9, [(560, 1090), (300, 1090), (300, 1150)], [("pair", 430, 1090)]),
    (8, 10, [(560, 1090), (820, 1090), (820, 1150)], [("impair", 690, 1090)]),
    (9, 11, [(300, 1216), (300, 1280), (530, 1280), (530, 1310)], []),
    (10, 11, [(820, 1216), (820, 1280), (590, 1280), (590, 1310)], []),
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


def couper(texte, largeur=23):
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
    contour = MENTHE if cle in FINS else VIOLET
    svg = [f'<rect x="{x}" y="{haut}" width="{L_CASE}" height="{H_CASE}" rx="12" fill="#fff" stroke="{contour}" stroke-width="2.5"/>']
    lignes = couper(titre)
    if len(lignes) > 2:
        lignes = couper(titre, 27)
    taille, interligne = (17, 18) if len(lignes) < 3 else (14.5, 15.5)
    y0 = haut + H_CASE / 2 - (len(lignes) - 1) * interligne / 2 + 6
    for i, l in enumerate(lignes):
        svg.append(f'<text x="{cx}" y="{y0 + i * interligne}" font-size="{taille}" text-anchor="middle" fill="{ENCRE}">{html.escape(l)}</text>')
    etiquette = "Prologue" if cle == "P" else str(cle)
    lb = 76 if cle == "P" else (30 if cle < 10 else 36)
    svg.append(f'<rect x="{x + 8}" y="{haut - 11}" width="{lb}" height="22" rx="11" fill="{ORANGE}"/>')
    svg.append(f'<text x="{x + 8 + lb / 2}" y="{haut + 5}" font-size="14" font-weight="800" text-anchor="middle" fill="#fff">{etiquette}</text>')
    if cle in FINS:
        svg.append(f'<text x="{cx}" y="{haut + H_CASE + 34}" font-size="24" font-weight="800" text-anchor="middle" fill="{MENTHE}">FIN</text>')
    return "\n".join(svg)


def icone(cle):
    cx, haut = CASES[cle]
    y = haut + H_CASE + 8
    svg = [f'<line x1="{cx}" y1="{haut + H_CASE}" x2="{cx}" y2="{y}" stroke="{VIOLET}" stroke-width="2"/>',
           f'<rect x="{cx - 13}" y="{y}" width="26" height="26" rx="6" fill="{JAUNE_CLAIR}" stroke="{ORANGE}" stroke-width="2"/>']
    if ICONES[cle] == "de":
        for dx, dy in ((-6, -6), (0, 0), (6, 6)):
            svg.append(f'<circle cx="{cx + dx}" cy="{y + 13 + dy}" r="2.6" fill="{ORANGE}"/>')
    else:
        svg.append(f'<text x="{cx}" y="{y + 19}" font-size="17" font-weight="800" text-anchor="middle" fill="{ORANGE}">?</text>')
    svg.append(f'<line x1="{cx}" y1="{y + 26}" x2="{cx}" y2="{y + 36}" stroke="{VIOLET}" stroke-width="2"/>')
    return "\n".join(svg)


def fleche(points, etiquettes):
    trace = " ".join(f"{x},{y}" for x, y in points)
    # Halo blanc sous chaque flèche : là où deux flèches se croisent, la dernière tracée passe dessus
    svg = [f'<polyline points="{trace}" fill="none" stroke="#fff" stroke-width="8"/>',
           f'<polyline points="{trace}" fill="none" stroke="{VIOLET}" stroke-width="2" marker-end="url(#pointe)"/>']
    for texte, x, y in etiquettes:
        largeur = 8.2 * len(texte) + 18
        svg.append(f'<rect x="{x - largeur / 2}" y="{y - 11}" width="{largeur}" height="22" rx="11" fill="#fff" stroke="{VIOLET}" stroke-width="1.5"/>')
        svg.append(f'<text x="{x}" y="{y + 5}" font-size="15" text-anchor="middle" fill="{VIOLET}">{html.escape(texte)}</text>')
    return "\n".join(svg)


def construire():
    titres, renvois = lire_texte()
    dessinees = {(a, b) for a, b, _, _ in FLECHES}
    assert set(titres) == set(CASES), f"Chapitres du texte et cases de l'arbre différents : {set(titres) ^ set(CASES)}"
    assert renvois == dessinees, f"Renvois du texte et flèches de l'arbre différents : {renvois ^ dessinees}"

    police = base64.b64encode(POLICE.read_bytes()).decode()
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{GAUCHE} 0 {LARGEUR} {HAUTEUR}" width="{LARGEUR}" height="{HAUTEUR}" font-family="Nunito, sans-serif">',
           f'<defs><style>@font-face{{font-family:"Nunito";font-weight:400 800;src:url(data:font/woff2;base64,{police}) format("woff2");}}</style>',
           f'<marker id="pointe" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{VIOLET}"/></marker></defs>']
    svg += [fleche(t, e) for _, _, t, e in FLECHES]
    svg += [icone(c) for c in ICONES]
    svg += [case(c, titres[c]) for c in CASES]
    svg.append("</svg>")
    SORTIE.parent.mkdir(exist_ok=True)
    SORTIE.write_text("\n".join(svg), encoding="utf-8")
    print(f"{SORTIE} : {len(CASES)} cases, {len(FLECHES)} flèches")


if __name__ == "__main__":
    construire()
