# Validation du MVP

Contrôles locaux effectués le 9 octobre 2026, sur Windows avec Python 3.12.14.

| Contrôle | Résultat |
|---|---|
| Django 5.2.18 / SQLite | 32 tests réussis |
| Django 6.0.9 / SQLite | 32 tests réussis |
| Django 6.1.2 / SQLite | 32 tests réussis |
| `manage.py check` | Aucun problème détecté |
| `makemigrations --check --dry-run` | Aucun changement de schéma manquant |
| Ruff | Contrôle du code réussi |
| Construction wheel et archive source | Réussie |
| Installation du wheel dans un deuxième environnement | Réussie, import depuis site-packages |
| Projet hôte indépendant | Migrations, templates, ressources, commande JSON, connexion et tableau fonctionnels |
| Compilation Tailwind | Réussie ; CSS compilé inclus |
| `npm audit` avec package-lock final | Aucune vulnérabilité signalée |
| Script PowerShell de démarrage | Syntaxe analysée sans erreur ; interaction de création de compte laissée à l’utilisateur |

## Tests de comportement

Les tests contrôlent l’authentification, les permissions de lecture/écriture,
le CSRF, les actions POST, l’échappement des titres dans HTML et HTMX, les filtres,
les archives et la conservation du journal après suppression. Ils couvrent aussi
la création et l’édition des tâches, les notes et sessions, ainsi que la protection
contre le changement d’une sous-tâche via une autre tâche.

Le workflow de clôture est vérifié : critères, preuves, sous-tâches, test récent,
justification des tests non applicables, invalidation après changement et réouverture
après échec. La répétition d’une clôture déjà enregistrée est sans effet supplémentaire.
Les changements de priorité d’une tâche terminée restent possibles. Le français
de la connexion ne change pas la langue du projet hôte.

Le protocole est testé par un parcours agent complet, la création/listage/consultation,
un import de plan atomique, les sous-tâches, les refus de permission et de champs inconnus,
les erreurs JSON, les fichiers UTF-8 avec BOM et la protection d’AGENTS.md existant.

## Vérification dans Chromium

Parcours réel avec JavaScript et HTMX : connexion, modes clair/sombre, déplacement
d’une carte par drag-and-drop, refus d’une clôture sans preuves, recherche avec
mise à jour partielle, ouverture de fiche et accès aux cinq sections complémentaires.
Aucune erreur JavaScript détectée pendant ce parcours.

Vérification à 1512 px et 390 px de largeur ; absence de débordement horizontal
sur mobile. Captures dans [screenshots/](screenshots/) :

- [Tableau clair](screenshots/tableau-clair.png)
- [Tableau sombre](screenshots/tableau-sombre.png)
- [Tableau mobile](screenshots/tableau-mobile.png)

## Limites de la validation

La CI fournie teste aussi PostgreSQL 16 et d’autres versions Python, mais elle n’a
pas été exécutée sur GitHub : aucun dépôt distant n’a été créé. PostgreSQL n’a pas
été testé localement, car le service Docker de cette machine est arrêté. La
compatibilité repose ici sur l’ORM et les migrations portables, complétés par le
job PostgreSQL prêt à être lancé lors de la publication du dépôt.

Un audit complet RGAA/WCAG, un test avec lecteur d’écran, les essais de charge et
une revue de déploiement du projet hôte restent à effectuer selon votre contexte.
Les résultats de tests saisis dans le tableau sont déclaratifs et ne remplacent
pas les preuves produites par votre CI ou vos propres commandes.
