# Installation pas à pas

## 1. Comprendre les prérequis

Python exécute l’application. Django est le framework web du projet. pip installe
les bibliothèques. Un environnement virtuel isole ces installations. Le terminal
est l’endroit où copier les commandes. Un dossier contenant `manage.py` est la
racine du projet Django ; ouvrez le terminal dans ce dossier.

Utilisez Python **3.12 ou 3.13** pour couvrir toutes les branches Django prises en
charge. Python 3.10 et 3.11 peuvent utiliser Django 5.2. Il faut un navigateur
récent. Node.js est facultatif : les fichiers CSS compilés sont déjà inclus.

## 2. Installer Python et préparer l’environnement

Windows : téléchargez Python sur [python.org](https://www.python.org/downloads/windows/).
Dans l’installateur, activez l’ajout de Python au PATH si cette option est proposée.
Fermez et rouvrez PowerShell, puis vérifiez :

```powershell
py --version
```

Linux Debian/Ubuntu :

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
python3 --version
```

Si votre distribution fournit une version trop ancienne, installez une version
compatible via son gestionnaire ou suivez [la documentation Python](https://docs.python.org/3/using/unix.html).

## 3. Tester la démonstration fournie

Décompressez le dépôt téléchargé puis ouvrez son dossier `django-project-manager`.
Sur votre ordinateur Windows, le script `DEMARRER.ps1` détecte aussi le Python
fourni avec Codex si le lanceur `py` ne trouve pas d’installation. Depuis ce dossier :

```powershell
powershell -ExecutionPolicy Bypass -File .\DEMARRER.ps1
```

À la première utilisation, répondez `o` pour créer votre propre compte. Les
commandes manuelles ci-dessous conviennent aussi à une installation Python standard.

Dans PowerShell, remplacez le chemin par celui de votre dossier :

```powershell
Set-Location 'C:\chemin\django-project-manager'
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py dpm_demo --actor votre_identifiant
.\.venv\Scripts\python.exe manage.py runserver
```

Linux :

```bash
cd /chemin/django-project-manager
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py dpm_demo --actor votre_identifiant
.venv/bin/python manage.py runserver
```

`createsuperuser` vous demande de choisir un identifiant et un mot de passe ; le
mot de passe n’apparaît pas pendant sa saisie. Remplacez `votre_identifiant` par
l’identifiant choisi. La commande de données fictives est facultative et refuse
de remplir une base qui contient déjà des tâches. Visitez
[le tableau local](http://127.0.0.1:8000/project/). Arrêtez le serveur avec Ctrl+C.
Ne publiez pas la base SQLite ni le fichier `.demo-secret` créés localement.

## 4. Installer dans votre projet existant

Sauvegardez votre projet et sa base. Utilisez son environnement Python habituel.
Les exemples ci-dessous supposent qu’il s’appelle `.venv` et que le dépôt de cette
bibliothèque se trouve dans un autre dossier.

PowerShell :

```powershell
Set-Location 'C:\chemin\mon-projet'
.\.venv\Scripts\python.exe -m pip install 'C:\chemin\django-project-manager'
```

Linux :

```bash
cd /chemin/mon-projet
.venv/bin/python -m pip install /chemin/django-project-manager
```

Vous pouvez aussi installer le wheel `django_project_manager-0.1.0-py3-none-any.whl`
avec `python -m pip install chemin_du_fichier.whl`. Le paquet n’est pas encore
publié sur PyPI. N’utilisez le nom seul qu’après une publication confirmée du dépôt.

## 5. Modifier settings.py

Dans le fichier de paramètres de votre projet, ajoutez seulement l’application :

```python
INSTALLED_APPS = [
    # Conservez toutes les applications déjà présentes.
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_project_manager",
]
```

Les applications `django.contrib.*` ci-dessus doivent être présentes une fois chacune.
Conservez vos réglages actuels. Vérifiez aussi :

- Un moteur `DjangoTemplates` avec `APP_DIRS=True`, ou le chargeur de templates des applications.
- Les context processors `django.template.context_processors.request`,
  `django.contrib.auth.context_processors.auth` et `django.contrib.messages.context_processors.messages`.
- Les middlewares `SessionMiddleware`, `CsrfViewMiddleware`,
  `AuthenticationMiddleware` et `MessageMiddleware` dans l’ordre standard Django.
- `STATIC_URL` défini et les migrations d’authentification/sessions exécutées.

Un projet créé avec `django-admin startproject` contient déjà ces éléments.
La bibliothèque utilise votre `AUTH_USER_MODEL` et votre `DATABASES`. Ne copiez
pas `demo/settings.py` dans un projet existant. Avec `USE_I18N = True`, elle applique
le français uniquement pendant ses propres vues, y compris les formulaires Django,
sans changer la langue du reste du projet.

## 6. Modifier urls.py

Dans le fichier principal d’URL :

```python
from django.urls import include, path

urlpatterns = [
    # Conservez vos routes actuelles.
    path("project/", include("django_project_manager.urls")),
]
```

Vérifiez qu’aucune route existante n’utilise déjà `project/`. Un autre préfixe est
possible, mais adaptez alors les liens indiqués aux agents. Les routes de connexion
sont internes à l’application : aucune modification de `LOGIN_URL` n’est requise.

## 7. Migrations, compte et permissions

PowerShell :

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Linux :

```bash
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver
```

Si vous disposez déjà d’un superutilisateur, ne le recréez pas. Pour les autres
comptes, créez un groupe dans l’administration Django et attribuez les permissions
de « Gestion du projet ». Un lecteur reçoit `view_task`. Un contributeur reçoit
aussi `add_task`, `change_task`, `add_subtask`, `change_subtask`, `add_testrun` et les
permissions de notes/sessions voulues. `delete_task` doit être attribué séparément.
Le [tableau complet](architecture.md#permissions) détaille les opérations.

## 8. Production et PostgreSQL

L’application utilise la base configurée par le projet. Pour PostgreSQL, installez
`python -m pip install 'django-project-manager[postgres]'` **après publication**,
ou `python -m pip install '.[postgres]'` depuis le dépôt, puis configurez
`django.db.backends.postgresql` dans vos paramètres habituels. Le projet de démo
lit aussi `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` et
`POSTGRES_PORT` dans l’environnement. Aucun secret n’est généré dans AGENTS.md.

En production, utilisez votre serveur Django habituel, HTTPS, `DEBUG=False`,
des hôtes autorisés explicites et des cookies sécurisés. Exécutez :

```text
python manage.py collectstatic --noinput
python manage.py check --deploy
```

Servez `STATIC_ROOT` comme pour les autres applications. Configurez la limitation
des tentatives de connexion dans le projet hôte. `runserver` n’est pas un serveur
de production. Les ressources front-end sont locales et ne nécessitent aucun CDN.

## 9. Mettre à jour

Sauvegardez la base et lisez CHANGELOG.md. Installez la nouvelle version depuis
son dossier ou wheel, puis lancez `migrate` et, en production, `collectstatic`.

PowerShell :

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade 'C:\chemin\nouvelle-version'
.\.venv\Scripts\python.exe manage.py migrate
```

Linux :

```bash
.venv/bin/python -m pip install --upgrade /chemin/nouvelle-version
.venv/bin/python manage.py migrate
```

## 10. Désinstaller

Pour désactiver sans perdre les données, retirez la route `project/` puis
`django_project_manager` d’INSTALLED_APPS, et désinstallez le paquet avec
`python -m pip uninstall django-project-manager`. Les tables restent dans la base.

Pour supprimer aussi toutes les données, **avant** de retirer l’application,
sauvegardez-les avec `python manage.py dumpdata django_project_manager --output dpm-backup.json`,
puis exécutez `python manage.py migrate django_project_manager zero`. Cette dernière
commande supprime définitivement les tables de l’application. Retirez ensuite la
route, l’application et le paquet. Fusionnez ou supprimez vous-même le bloc généré
d’AGENTS.md ; la désinstallation ne modifie pas vos fichiers d’instructions.

## 11. Erreurs courantes

| Message | Solution |
|---|---|
| `py` / `python3` introuvable | Installer Python puis rouvrir le terminal ; vérifier le PATH. |
| PowerShell bloque Activate.ps1 | Utiliser les chemins `.venv\Scripts\python.exe` du guide, sans activation. |
| `No module named django_project_manager` | Installer avec le Python du même environnement que `manage.py`. |
| `no such table` / `relation does not exist` | Exécuter `manage.py migrate` avec les paramètres et la base du projet. |
| Réponse 403 | Attribuer `view_task` et les droits nécessaires ; vérifier le compte actif. |
| CSRF verification failed | Activer cookies, middleware CSRF et HTTPS cohérent ; vérifier les origines du projet. |
| Template introuvable | Vérifier INSTALLED_APPS et APP_DIRS / le chargeur des applications. |
| Interface sans style | Vérifier staticfiles ; en production exécuter collectstatic et servir STATIC_ROOT. |
| Tâche impossible à terminer | Cocher les sous-tâches, vérifier les critères puis enregistrer un nouveau contrôle. |
| `database is locked` | Éviter les écritures simultanées sur SQLite ou passer à PostgreSQL. |
| AGENTS.md existe déjà | Fusionner manuellement le fichier généré ailleurs ; ne remplacer qu’en connaissance de cause. |
| Port 8000 occupé | Utiliser `manage.py runserver 8001`, puis ouvrir le port 8001. |

## Vérifier l’installation

Dans le dépôt de démonstration, exécutez `python manage.py test tests`. Dans un
projet hôte, exécutez `python manage.py check`, connectez-vous, créez une tâche et
vérifiez qu’un compte lecteur ne peut pas la modifier. Les tests du dépôt ne sont
pas installés avec le wheel : ils appartiennent à l’environnement de développement.
