# L'île aux dragons

Une histoire dont le lecteur est le héros, librement inspirée du récit imaginé par Louisa et June pendant l'atelier « La quête du curry, une histoire dont tu es le héros » du L.A.B, à la bibliothèque Li Campaneto (bibliothèques Méjanes, Aix-en-Provence), en octobre 2026.

## Modifier le livre

Le texte se trouve dans `source/texte.md`, recopié de la page Notion de référence. Chaque chapitre commence par `## Chapitre n. Titre`, les choix s'écrivent `- texte du lien -> n` (une ligne sans `->`, comme « Un autre nombre : relance le dé. », reste une simple indication) et la fin se termine par `FIN`. La couverture, la page « Comment est née cette histoire » et la mise en forme sont dans `source/construire_site.py`. Les planches vont dans `images/chapitres/` (`prologue.jpg`, `chapitre-01.jpg`…) ; une page sans image s'affiche sur une seule colonne. L'arbre se redessine avec `python3 source/construire_arbre.py`.

```
python3 source/construire_site.py
```

Réalisation du livre : Laboratoire d'Aix-périmentation et de Bidouille.
