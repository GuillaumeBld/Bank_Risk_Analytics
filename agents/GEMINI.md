# Agent Operating Manual

## Lisez ceci au début de chaque session
Toujours commencer par ouvrir /agents/comms.md, lire le <goal>, puis la dernière ligne du journal pour vérifier si c'est votre tour. Si oui, déterminer la plus petite étape utile qui fait progresser le projet et peut être terminée en moins de cinq minutes. Avant toute édition, créer le verrou `/diagnostic/lock_<agent>.lock`. Écrire aussitôt dans la section **Agent Action Log** une ligne unique ne dépassant pas 200 caractères et suivant strictement le format :
[YYYY-MM-DD HH:MM UTC][Agent n] Action: <étape en cours>. Next: <étape suivante>.
Ensuite exécuter l'étape, ne modifier que des fichiers dans **/diagnostic**, mettre à jour le journal avec le résultat et la tâche suivante, supprimer le fichier de verrou, relire le journal pour cohérence, puis recommencer le cycle. S'arrêter uniquement si la ligne `[FIN]` apparaît dans comms.md ou si l'utilisateur déclare la tâche achevée.

---

## Cycle d'exploitation détaillé
1. **Verrouillage :** créer `/diagnostic/lock_<agent>.lock` avant d'ouvrir comms.md, le supprimer après sauvegarde.
2. **Lecture :** consulter /agents/GEMINI.md et /agents/comms.md (objectif + dernier log).
3. **Planification :** choisir une action de < 5 min. Si l'action est plus longue, la découper.
4. **Journalisation :** écrire la ligne Action/Next avec horodatage UTC, respecter 200 caractères max.
5. **Exécution :** réaliser l'étape dans /diagnostic uniquement, exécuter `npm run lint` ou commande équivalente s'il existe un script de vérification, corriger avant de journaliser.
6. **Revue croisée :** relire la dernière entrée d'un autre agent pour détecter incohérences.
7. **Blocage :** si un obstacle empêche l'étape, journaliser sous le format :
[YYYY-MM-DD HH:MM UTC][Agent n] Blocage: <problème>. Next: diagnostiquer <étape>.
8. **Résumé quotidien :** avant 23:55 UTC, l'agent actif crée `/diagnostic/daily/diag_YYYYMMDD_daily.md` à partir du modèle fourni, puis journalise :
[YYYY-MM-DD HH:MM UTC][Agent n] Action: résumé quotidien créé. Next: <étape suivante>.
9. **Convention de nommage :** tout nouveau fichier dans /diagnostic commence par `diag_YYYYMMDD_`.
10. **Exemple complet :**
[2025-07-18 14:32 UTC][Agent 2] Action: calcul σ actions 12 mois. Next: recalculer DD avec σ 24 mois.
---

## Logging Protocol (rappel rapide)
* Préfixe horodaté UTC.
* Limite de 200 caractères.
* Structure Action/Next ou Blocage/Next.
* Une tâche à la fois.
* Communication exclusive via comms.md.
* Respecter le verrou pour éviter les collisions d'écriture.
