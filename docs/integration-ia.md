# Intégration avec les agents IA

## Principe

La bibliothèque ne contacte aucune API IA. Un agent disposant du terminal du projet
appelle `manage.py dpm` pour lire ou mettre à jour les tâches. Les règles de clôture
sont identiques à celles de l’interface. Aucune clé de fournisseur n’est nécessaire.
L’utilisation de votre outil IA conserve ses propres conditions et coûts éventuels.

`--actor` doit désigner un compte Django actif disposant des permissions. Ce paramètre
sert au contrôle des droits et au journal, mais ne remplace pas une authentification :
l’accès au terminal et à la base est un accès de confiance. Prévoyez un compte de
contribution limité ; ne donnez pas automatiquement un compte superutilisateur aux agents.

## Générer les instructions

Dans le dossier contenant `manage.py`, après installation et migrations :

PowerShell :

```powershell
.\.venv\Scripts\python.exe manage.py dpm --actor votre_identifiant agents
```

Linux :

```bash
.venv/bin/python manage.py dpm --actor votre_identifiant agents
```

Le fichier contient les commandes et la procédure de vérification, aucun secret.
Si `AGENTS.md` existe déjà, la commande **refuse** de l’écraser. Générez plutôt
`agents --path DPM-AGENTS.md` puis fusionnez les sections utiles. Le remplacement
exige l’option explicite `--overwrite`, à utiliser uniquement après relecture et sauvegarde.

## Codex, OpenCode et Claude Code

**Codex** : ouvrez le dossier de votre projet et placez le fichier `AGENTS.md` à sa
racine. Codex consulte les instructions de ce fichier ; vérifiez leur prise en
compte en lui demandant de résumer le protocole avant sa première modification.
Les instructions d’un sous-dossier peuvent compléter celles de la racine.
Référence : [documentation officielle AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

**OpenCode** : ouvrez le même dossier dans votre environnement de travail et demandez
explicitement à l’agent de lire `AGENTS.md` puis d’utiliser les commandes `dpm`.
Cette procédure reste utilisable même si votre version ne charge pas automatiquement ce fichier.

**Claude Code** : demandez aussi de lire `AGENTS.md` au début de session. Si vous
utilisez un fichier `CLAUDE.md`, ajoutez-y une consigne qui renvoie vers `AGENTS.md`,
sans écraser ses instructions existantes. Aucun plugin spécifique n’est requis.

Consigne de départ suggérée :

```text
Lis AGENTS.md. Utilise le Python de l’environnement du projet et le compte Django
CONTRIBUTEUR pour les commandes dpm. Liste les tâches restantes, propose un plan,
puis avance une tâche à la fois. Ne marque rien comme terminé sans vérifier les
critères et exécuter les tests applicables. Consigne seulement les résultats observés.
```

## JSON stable, version 1

Chaque commande réussie produit **un objet JSON sur stdout** :

```json
{"schema_version":1,"ok":true,"data":{"tasks":[]},"errors":[]}
```

Un refus produit `ok:false`, `data:null`, une liste `errors` et un code de sortie
non nul. Le message Django sur stderr ne fait pas partie du JSON. Une erreur de
syntaxe des arguments est traitée par argparse et ne produit pas d’enveloppe JSON.
Le protocole suppose une installation fonctionnelle ; une panne de base peut
également sortir de cette enveloppe. Les schémas sont livrés dans `schemas/` du paquet.
Le consommateur doit vérifier `schema_version` et `ok` avant de lire `data`.

Valeurs stables :

| Champ | Valeurs |
|---|---|
| status | `todo`, `doing`, `waiting`, `done` |
| priority | `low`, `normal`, `high`, `critical` |
| category | `feature`, `bug`, `optimization`, `security`, `docs`, `test` |
| result d’un contrôle | `passed`, `failed`, `skipped` |

Les IDs sont des entiers, les dates des chaînes ISO 8601. `due_date` vaut `YYYY-MM-DD`
ou `null`. Les champs `archived`, `acceptance_verified`, les IDs et les horodatages
ne peuvent pas être modifiés dans `create`/`update`. Utilisez les actions dédiées.
La taille des imports est limitée à 1 Mo ; un plan contient 1 à 200 tâches avec
100 sous-tâches maximum chacune. L’import entier est annulé si une tâche est invalide.
Un import n’est pas idempotent : une seconde exécution crée un nouveau plan.

## Commandes à copier

Les exemples utilisent le raccourci `python` une fois l’environnement activé.
Sans activation, remplacez-le par `.\.venv\Scripts\python.exe` sur PowerShell
ou `.venv/bin/python` sur Linux, comme dans le guide d’installation.
Remplacez `contributeur` et les IDs par les valeurs de votre projet.

```text
python manage.py dpm --actor contributeur list --remaining
python manage.py dpm --actor contributeur list --archived
python manage.py dpm --actor contributeur show 1
python manage.py dpm --actor contributeur subtask 1 --title "Vérifier les permissions"
python manage.py dpm --actor contributeur toggle 1 --subtask-id 2
python manage.py dpm --actor contributeur verify 1 --notes "Les critères ont été vérifiés : lecteur bloqué en écriture."
python manage.py dpm --actor contributeur test 1 --command "python manage.py test" --result passed --notes "Résultat réel des tests."
python manage.py dpm --actor contributeur archive 1
python manage.py dpm --actor contributeur restore 1
python manage.py dpm --actor contributeur delete 1 --confirm
```

### Créer un plan et mettre à jour

Préférez les fichiers JSON à `--data` pour éviter les différences d’échappement
entre les terminaux. Les fichiers UTF-8 avec BOM de PowerShell sont pris en charge.

PowerShell :

```powershell
@'
{"tasks":[{"title":"Protéger le tableau","category":"security","priority":"high","acceptance_criteria":"Un lecteur ne peut pas modifier une tâche.","subtasks":["Ajouter les permissions","Tester le refus"]}]}
'@ | Set-Content -Encoding utf8 plan.json
.\.venv\Scripts\python.exe manage.py dpm --actor contributeur plan --file plan.json
'{"status":"doing"}' | Set-Content -Encoding utf8 update.json
.\.venv\Scripts\python.exe manage.py dpm --actor contributeur update 1 --file update.json
```

Linux :

```bash
cat > plan.json <<'JSON'
{"tasks":[{"title":"Protéger le tableau","category":"security","priority":"high","acceptance_criteria":"Un lecteur ne peut pas modifier une tâche.","subtasks":["Ajouter les permissions","Tester le refus"]}]}
JSON
.venv/bin/python manage.py dpm --actor contributeur plan --file plan.json
printf '%s\n' '{"status":"doing"}' > update.json
.venv/bin/python manage.py dpm --actor contributeur update 1 --file update.json
```

`create --file task.json` accepte les mêmes champs qu’une tâche du plan, mais sans
le champ `subtasks` : ajoutez les sous-tâches avec la commande dédiée. `update` accepte
un sous-ensemble des champs modifiables. Consignez une référence Git avec `commits`
et les changements dans `description`, **avant** les vérifications finales.

### Clôture et prochaine session

Cochez les sous-tâches effectivement réalisées, consignez la vérification, exécutez
les tests puis enregistrez le contrôle. Ensuite seulement, préparez un fichier
`done.json` contenant `{"status":"done"}` et appelez :

```text
python manage.py dpm --actor contributeur update 1 --file done.json
python manage.py dpm --actor contributeur list --remaining
```

Le simple fait d’avoir écrit du code n’est jamais une raison suffisante pour utiliser
`passed` ou `done`. Si des tests ne sont pas applicables, utilisez `skipped` avec une
justification précise. Le bilan de session se consigne dans « Sessions IA » de
l’interface ; aucune conversation IA n’est automatiquement capturée.

## Future intégration MCP

Le service Python et le protocole versionné constituent les points d’adaptation.
Le MVP ne fournit pas de serveur MCP, de jeton d’API ni d’accès distant pour agents.
Un futur adaptateur devra authentifier le compte réellement appelant, appliquer les
permissions, limiter les requêtes et préserver les règles de vérification.
