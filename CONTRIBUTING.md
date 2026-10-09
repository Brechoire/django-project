# Contribuer et publier

Créez un environnement Python, puis installez `python -m pip install -e '.[dev]'`.
Lancez `python manage.py test tests`, `python manage.py check` et
`python manage.py makemigrations --check --dry-run` après un changement métier.
Les mutations doivent passer par services.py et préserver les contrôles de clôture.
Ajoutez des tests de comportement pour les nouvelles règles et vérifiez les permissions.

Pour modifier le style, Node.js 20+ est nécessaire uniquement en développement :

```text
npm ci
npm run build:css
npm audit
```

Versionnez le CSS compilé et le verrou package-lock.json. HTMX 2.0.8 est copié de
`node_modules/htmx.org/dist/htmx.min.js` ; sa licence est dans le dossier vendor.
Tailwind et les dépendances Python conservent leurs licences respectives.
N’ajoutez pas de CDN, de secret, de base de démonstration ou de compte prédéfini.

Construction Python :

```text
python -m build
```

Le dossier dist contient un wheel installable et une archive source. Avant une
publication, installez le wheel dans un environnement neuf et lancez un projet hôte.
La CI effectue également cette vérification. Vérifiez la disponibilité du nom sur
PyPI, choisissez le dépôt GitHub, relisez les licences et la version, puis publiez
avec vos outils habituels. Aucun dépôt distant ni compte PyPI n’est créé automatiquement.

Pour créer votre dépôt local après téléchargement :

```text
git init
git add .
git commit -m "Première version de Django Project Manager"
```

Créez ensuite un dépôt vide dans votre compte GitHub, et suivez les commandes
d’association du dépôt proposées par GitHub. Ne versionnez pas `db.sqlite3`,
`.demo-secret`, `.env`, `.venv` ou `node_modules` : ils sont ignorés.
