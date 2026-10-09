# Utiliser le tableau de bord

## Une première tâche

Connectez-vous sur `/project/`, puis choisissez « Nouvelle tâche ». Donnez un titre
concret, une description, une catégorie et une priorité. L’échéance et les références
Git sont facultatives. Les critères d’acceptation décrivent ce que vous vérifierez,
par exemple « Un utilisateur sans permission reçoit une réponse 403 ».

Le titre est limité à 200 caractères. Les descriptions, critères, notes et commits
sont du texte brut : le HTML reste affiché comme du texte pour éviter les injections.

## Suivre le travail

Les colonnes sont « À faire », « En cours », « En attente » et « Terminé ». Déplacez
une carte à la souris ou choisissez son statut et cliquez sur « Déplacer ». Ce
sélecteur fonctionne au clavier, sur mobile et sans JavaScript. Ouvrez le titre
d’une carte pour voir sa fiche, ajouter des étapes ou modifier le contenu.

La recherche porte sur le titre et la description. Combinez-la avec les filtres
de priorité et de catégorie, puis cliquez sur « Filtrer ». Les compteurs de
progression portent sur toutes les tâches actives (ou archivées dans la vue archives),
alors que les compteurs des colonnes portent sur les cartes filtrées.

Le bouton « Thème » bascule entre clair et sombre et retient votre préférence dans
ce navigateur. La vue « Suivi des bugs » applique le filtre catégorie Bug.

## Terminer après vérification

1. Découpez la tâche en sous-tâches et cochez chaque étape réellement réalisée.
2. Vérifiez les critères d’acceptation, puis consignez les résultats observés dans
   « Consigner une vérification » et validez les critères.
3. Exécutez les tests pertinents dans votre terminal, ou faites le contrôle manuel
   approprié. Dans « Enregistrer un résultat », indiquez la commande ou le contrôle,
   son résultat et les détails observés.
4. Si aucun test n’est applicable, choisissez « Non applicable » et justifiez-le.
5. Passez le statut à « Terminé ».

Un message explique toute condition manquante. Enregistrer un contrôle ne lance
aucune commande : vous êtes responsable de la fidélité du résultat déclaré.
Une modification du contenu ou des sous-tâches invalide la vérification et rouvre
une tâche terminée ; recommencez la vérification et le contrôle après le changement.
Un échec de test rouvre aussi la tâche. Les tests anciens ne valident pas une nouvelle révision.

## Archives et suppression

« Archiver » retire une tâche du tableau actif et conserve son contenu. Le lien
« Consulter les archives » permet de la retrouver. Depuis sa fiche, choisissez
« Restaurer » pour la remettre dans le tableau actif.

« Supprimer… » ouvre une page de confirmation. La suppression retire aussi les
sous-tâches et tests ; le journal garde les actions et le titre de la tâche.
Si vous hésitez, archivez. La suppression exige une permission distincte.

## Comprendre les autres sections

- **Journal** : actions datées et auteur, avec détails des changements.
- **Tests & vérifications** : liste des contrôles enregistrés sur les tâches.
- **Sessions IA** : ouvrez une session avec l’agent et l’objectif, puis clôturez-la
  avec le bilan et la prochaine étape. Il s’agit d’un journal manuel, pas d’une
  capture automatique des conversations de vos outils IA.
- **Notes & décisions** : conservez le choix, ses raisons et les alternatives utiles.
- **Statistiques** : progression, tâches par statut/catégorie et échéances dépassées.

Les notes sont des entrées de journal ajoutées une fois. Pour rectifier une décision,
ajoutez une note qui cite la précédente. L’édition des notes et la gestion avancée
des sessions font partie de la feuille de route. Votre administrateur attribue les
permissions ; certains liens et boutons peuvent donc être absents pour votre compte.
