# Architecture du MVP

## Choix

Le paquet `django_project_manager` est une application Django autonome. Son nom de
module est distinct du nom de distribution pip `django-project-manager`. Toutes les
tables et tous les fichiers statiques sont préfixés par l’application. Les URL sont
dans l’espace de noms `django_project_manager`. Aucune modification automatique des
réglages du projet, aucun signal global, aucun remplacement du modèle utilisateur.

Le projet `demo` est un exemple local, exclu du paquet installé. Ses migrations et
sa commande de démonstration utilisent les modèles de la véritable bibliothèque.
Le wheel contient modèles, vues, migrations, commandes, templates, schémas et ressources.

## Organisation

```text
django_project_manager/
  models.py           tâches, sous-tâches, contrôles, journal, sessions, notes
  services.py         validations, transactions et journal des mutations
  views.py, forms.py  interface protégée
  urls.py             routes préfixées par le projet hôte
  admin.py            inspection en lecture seule
  management/commands/dpm.py      protocole agents
  management/commands/dpm_demo.py exemples fictifs facultatifs
  migrations/         schéma initial versionné
  templates/          interface française Django Templates + HTMX
  static/             CSS Tailwind compilé, JS et HTMX local
  schemas/            protocole JSON v1
demo/                 projet de démonstration
tests/                tests comportementaux et sécurité
assets/               source CSS, compilation facultative avec Node
docs/                 documentation en français
```

## Flux d’écriture et clôture

L’interface et la commande `dpm` invoquent les mêmes services transactionnels.
Les mutations d’une tâche prennent un verrou `select_for_update` sur PostgreSQL.
SQLite convient à un usage local avec peu d’écritures concurrentes ; ses verrous
globaux peuvent produire « database is locked » si plusieurs agents écrivent ensemble.

Le service refuse « done » si les critères sont vides, non vérifiés, sans preuve,
si une sous-tâche reste ouverte, ou si le dernier contrôle est absent, échoué ou
antérieur à la dernière modification. Un contrôle « skipped » exige une justification.
Les changements du titre, de la description, des critères, des références Git ou
des sous-tâches invalident la validation ; une tâche terminée est alors rouverte.
Un test échoué rouvre aussi la tâche. Il faut enregistrer la vérification **avant**
le contrôle final, car la vérification met à jour la date de modification.

Le journal garde l’identité Django, les valeurs avant/après et le titre historique.
La suppression d’une tâche conserve ses événements et supprime ses sous-tâches et
tests. L’administration de ces modèles est en lecture seule pour éviter une clôture
qui contournerait le service. Un accès direct à l’ORM/SQL reste un accès de confiance.

## Permissions

L’accès exige un utilisateur connecté et actif. Les vues exigent `view_task`, puis
la permission correspondant à l’opération. Les permissions sont celles générées
par Django dans `/admin/auth/group/` (ou l’administration de votre modèle utilisateur).

| Fonction | Permissions de l’application |
|---|---|
| Tableau, fiche et statistiques | `view_task` |
| Créer une tâche / importer un plan | `view_task`, `add_task` |
| Éditer, vérifier, déplacer, archiver, restaurer | `view_task`, `change_task` |
| Ajouter une sous-tâche | précédentes + `add_subtask` |
| Cocher une sous-tâche | précédentes + `change_subtask` |
| Ajouter un contrôle | précédentes + `add_testrun` |
| Supprimer une tâche | `view_task`, `delete_task` |
| Journal global | `view_task`, `view_activity` |
| Liste des tests | `view_task`, `view_testrun` |
| Notes | `view_task`, `view_note` (+ `add_note` pour écrire) |
| Sessions | `view_task`, `view_aisession` (+ `add_aisession` / `change_aisession`) |

Le préfixe complet est `django_project_manager.`. Le droit `view_task` donne accès
à la fiche complète, y compris ses sous-tâches, contrôles et historique. Les droits
`view_activity` et `view_testrun` contrôlent les vues globales correspondantes.
Un superutilisateur actif possède tous ces droits. Les agents ne reçoivent aucun
accès HTTP anonyme. `--actor` vérifie les droits et fournit une identité de journal,
mais un utilisateur disposant d’un terminal et de la base peut choisir cette identité :
ce n’est pas une frontière d’authentification. Limitez cet accès système.

## Front-end et accessibilité

HTML échappé par Django, formulaires CSRF, mutations en POST. HTMX n’évalue ni code
ni scripts reçus ; seules les requêtes du même site sont autorisées. Les références
Git et commandes sont du texte affiché, jamais exécuté. Le CSS et HTMX sont locaux.
Le thème n’enregistre qu’une préférence dans localStorage, aucune donnée sensible.

Titres hiérarchisés, repères de navigation, libellés de champs, lien d’évitement,
focus visible, annonces d’état et sélecteur de statut au clavier complètent le drag.
Le Kanban s’adapte de quatre à deux puis une colonne. Aucune certification RGAA/WCAG
n’est revendiquée ; un audit humain complet reste à prévoir avant une telle déclaration.

Pour une CSP stricte, autorisez `script-src 'self'` et `style-src 'self'`. Configurez
les en-têtes dans le projet hôte : l’application ne remplace pas sa politique.

## Extension future

Un adaptateur MCP pourra appeler ces services ou le protocole v1 sans coupler le
MVP à un fournisseur IA. Les permissions par espace et la révision optimiste pour
les éditions simultanées font partie de la feuille de route.
