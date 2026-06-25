# Guide utilisateur — Fiches d'erreurs

> Fonctionnalité disponible pour les **étudiants uniquement**.

---

## À quoi ça sert ?

Quand tu discutes avec le tuteur IA sur un support de cours, il arrive que tu fasses
une erreur de compréhension sans forcément t'en rendre compte. Le tuteur la corrige,
mais cette correction disparaît quand tu fermes l'onglet.

Les **fiches d'erreurs** résolvent ce problème : chaque erreur détectée est
automatiquement transformée en une fiche pédagogique que tu peux consulter, relire
et télécharger en PDF pour réviser plus tard.

---

## Comment ça fonctionne ?

Tu n'as rien à faire. À chaque échange avec le tuteur IA :

1. Tu envoies un message, le tuteur répond.
2. En arrière-plan, une analyse détecte si ta question ou ta réponse révèle une
   incompréhension.
3. Si c'est le cas, une fiche est créée et apparaît dans le panneau **Mes fiches
   d'erreurs**, juste sous le chat.
4. Une notification discrète te prévient qu'une nouvelle fiche a été ajoutée.

Si ta question est correcte, aucune fiche n'est créée.

---

## Le panneau Fiches d'erreurs

Le panneau se trouve **sous la zone de chat** sur la page de chaque support
(`/student/support/:id`).

### Ouvrir / fermer le panneau

Clique sur l'en-tête **"Mes fiches d'erreurs"** pour déplier ou replier le panneau.
Le badge à côté du titre affiche le nombre de fiches enregistrées pour ce support,
même quand le panneau est replié.

![Panneau replié](screenshots/student-error-cards-header.png)
![Panneau ouvert](screenshots/mockup-panel-open.png)

### Lire une fiche

Chaque fiche contient :

| Champ | Contenu |
|-------|---------|
| **Concept** | Le sujet ou la notion concernée |
| **Erreur détectée** | Ce qui était incorrect dans ta compréhension |
| **Explication simple** | Une reformulation claire du concept |
| **Exemple correct** | Un exemple concret pour ancrer la notion |
| **Date** | Quand la fiche a été créée |

![Panneau avec fiches](screenshots/student-error-cards-panel.png)

### Notification

Quand une nouvelle fiche apparaît après un échange, un toast s'affiche
en bas à droite de l'écran.

### Supprimer une fiche

Clique sur l'icône corbeille à droite d'une fiche pour la supprimer définitivement.
Cette action est immédiate et irréversible.

### Exporter en PDF

Clique sur le bouton **↓ PDF** (en haut à droite du panneau, couleur ambre) pour
générer un PDF contenant toutes tes fiches du support actuel.

Le PDF s'ouvre dans la fenêtre d'impression du navigateur. Sélectionne
**"Enregistrer en PDF"** dans la liste des imprimantes pour sauvegarder le fichier.

![Aperçu du PDF](screenshots/student-error-cards-pdf.png)

> Le PDF inclut le nom du support et la date de l'export. L'URL du navigateur
> n'apparaît pas dans l'en-tête.

---

## Questions fréquentes

**Les fiches sont-elles partagées entre supports ?**
Non. Chaque support a sa propre liste de fiches indépendante.

**Les enseignants peuvent-ils voir mes fiches ?**
Non. Les fiches sont strictement personnelles et liées à ton compte.

**Une fiche peut-elle être modifiée ?**
Pas pour l'instant. Tu peux la supprimer et laisser le tuteur IA en générer
une nouvelle si tu rencontres à nouveau une difficulté similaire.

**Que se passe-t-il si aucune erreur n'est détectée ?**
Aucune fiche n'est créée. Le panneau reste inchangé. C'est le comportement
normal quand ta compréhension est correcte.

**L'analyse ralentit-elle le chat ?**
Non. L'analyse s'exécute en arrière-plan après que la réponse du tuteur t'a
été affichée. Tu ne constates aucun délai supplémentaire.
