# ProfilPro RH — application Django + front-end Figma

- `frontend/` : application React/Vite exportée de Figma (page « Segmentation RH » branchée sur l'API)
- `segmentation/` : app Django qui charge `models/modele_profilpro.pkl` (préprocesseur → ACP → K-Means)
- `config/` : projet Django (sert l'API sous `/api/` et le front construit à la racine)

## Installation
    python -m venv .venv && source .venv/bin/activate     # Windows : .venv\Scripts\activate
    pip install -r requirements.txt                        # scikit-learn 1.6.1 obligatoire (version du .pkl)
    cd frontend && pnpm install && pnpm build && cd ..     # ou npm install && npm run build
    python manage.py runserver                             # http://127.0.0.1:8000

## Mode développement (rechargement à chaud du front)
    python manage.py runserver          # terminal 1 (port 8000)
    cd frontend && pnpm dev             # terminal 2 (port 8443, proxy /api -> 8000)

## API
- `GET  /api/health/`                   état + `model_consistent`
- `GET  /api/segmentation/profiles/`    noms des profils
- `POST /api/segmentation/predict/`     {"age":44,"education_num":13,"marital_status":"Married-civ-spouse","relationship":"Husband","sex":"Male"}

## ⚠️ Modèle incohérent
Le `.pkl` fourni échoue au test de cohérence (centres K-Means incompatibles avec l'ACP sauvegardée) :
les clusters renvoyés ne correspondent pas à `noms_profils`. `/api/health/` renvoie `model_consistent: false`
et le front affiche un avertissement. Ré-exportez un `.pkl` où préprocesseur, ACP et K-Means sont ajustés
dans la même exécution, puis remplacez `models/modele_profilpro.pkl`.

## Limites
- Seule la page « Segmentation RH » (formulaire en haut) appelle le modèle ; le reste du front reste en données simulées.
- L'endpoint POST est `csrf_exempt` : à sécuriser avant toute mise en production (`DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY`).

## Données réelles (MySQL XAMPP)
1. XAMPP : démarrer **Apache** et **MySQL**, ouvrir http://localhost/phpmyadmin, créer la base `profilpro` (utf8mb4_general_ci).
2. `pip install -r requirements.txt`
3. `python manage.py makemigrations segmentation && python manage.py migrate`
4. `python manage.py import_adult chemin\adult.test chemin\adult.data --reset`   (adult.data facultatif)
5. `cd frontend && npm install && npm run build`, puis `python manage.py runserver`
Variables optionnelles : DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT (défaut : profilpro / root / vide / 127.0.0.1 / 3306).
Nouvelles routes : `GET /api/stats/` (KPI, répartitions) et `GET /api/people/?page=1&q=Sales` (profils paginés).

## Analyse des profils → Segmentation des profils familiaux (clustering du notebook)
Parcours : **Analyse des profils** → import du CV → « Analyser le CV » → compléter les 5 variables familiales
(âge, années d'études, statut marital, rôle familial, sexe) → valider → cocher **Segmentation des profils familiaux**
→ **Lancer l'analyse**. La page de résultats affiche, en langage RH : le profil du candidat, sa comparaison avec son groupe, les cartes des profils, la composition du groupe et la carte de clustering (seul graphique conservé) ; les indicateurs techniques sont dans « Détails techniques ».

- `POST /api/segmentation/analyze/` (mêmes champs que `/predict/`) : renvoie `candidate`, `clusters`, `model` et `graphs` (PNG base64).
- `segmentation/clustering.py` reproduit le notebook (nettoyage → StandardScaler + One-Hot → ACP → K-Means, k par silhouette entre 3 et 8)
  et ajuste préprocesseur, ACP et K-Means dans la même exécution : il **n'utilise pas le .pkl** et n'a donc pas le problème d'incohérence.
- Données : table MySQL `adult_person` si elle contient des lignes, sinon `data/adult.data` + `data/adult.test`. Pour retrouver exactement
  les résultats du notebook (jeu complet UCI), importez aussi `adult.data` : `python manage.py import_adult adult.test adult.data --reset`.
- `PROFILPRO_K=5` (variable d'environnement) impose le nombre de clusters. Le 1er appel après un démarrage prend quelques secondes (ajustement du modèle), les suivants ~2 s.
- Dépendances ajoutées : `matplotlib`, `seaborn` (`pip install -r requirements.txt`).

## ▶ Démarrage rapide (ami / nouvelle machine)
Prérequis : **Python 3.10+** uniquement (le front est déjà compilé dans `frontend/dist`, pas besoin de Node).
- **Windows** : double-cliquer sur `demarrer.bat` — **macOS/Linux** : `./demarrer.sh`
- Le script crée l'environnement, installe les dépendances, prépare la base, importe `data/adult.test` (une seule fois) et lance le serveur → http://127.0.0.1:8000
- **Base de données automatique** : si MySQL/MariaDB (XAMPP) est joignable, il est utilisé (la base `profilpro` est créée au besoin) ; sinon l'application bascule seule sur **SQLite**. Forcer : `DB_ENGINE=mysql` ou `DB_ENGINE=sqlite`.
- **Import sans doublon** : `python manage.py import_adult data\adult.test` *remplace* les lignes de la même source au lieu de les ajouter. Pour nettoyer une base déjà doublée : relancer cette commande une fois.
- Django est figé en **5.0** car XAMPP fournit MariaDB 10.4 (Django 5.1+ exige MariaDB ≥ 10.5).

## 🤖 Analyse du CV par IA gratuite (Google Gemini)
`POST /api/cv/analyze/` (multipart, champ `file`, PDF ≤ 10 Mo) renvoie formation, catégorie d'éducation (+ education-num), métier, expérience, compétences et âge si présent.
1. Créer une clé **gratuite, sans carte bancaire** sur https://aistudio.google.com/apikey (compte Google).
2. Copier `.env.example` en `.env` et renseigner `GEMINI_API_KEY=...` (ne jamais partager ce fichier ; chacun met sa propre clé).
3. Relancer le serveur. Un bandeau vert « extraits par IA (Gemini) » apparaît à l'étape de vérification.
- Le modèle « flash » disponible est choisi automatiquement (les noms changent souvent) ; forçable avec `GEMINI_MODEL`.
- **Quota gratuit limité** (quelques dizaines à centaines de requêtes par jour selon le modèle, voir https://aistudio.google.com/rate-limit). Quota atteint, clé refusée ou pas de réseau : l'application bascule sur une **extraction locale simplifiée** (règles + pypdf) et l'indique par un bandeau orange. Sans clé, c'est le même mode.
- **Confidentialité** : le palier gratuit de Google peut utiliser les données envoyées pour améliorer ses produits. Par défaut, on n'envoie donc que le **texte** du CV, **sans e-mail, téléphone ni liens** (le nom reste présent) ; le PDF brut n'est envoyé que s'il est scanné ou avec `GEMINI_SEND_PDF=1`. Pour de vrais candidats : les informer (RGPD) ou passer à un fournisseur payant / un modèle local.
- Le sexe, la situation matrimoniale et le rôle familial **ne sont jamais déduits** du CV (risque de discrimination) : ils restent à saisir par le RH, sauf s'ils sont écrits explicitement.
- Option payante : `ANTHROPIC_API_KEY` + `pip install anthropic` (Gemini reste prioritaire si les deux clés sont présentes).

## 💰 Classification des revenus (CatBoost)
Parcours : **Analyse des profils** → import du CV → « Analyser le CV » → compléter les variables (âge, études, sexe, rôle familial + bloc
« Classification des revenus » : métier, heures/semaine, gains/pertes en capital — facultatifs) → cocher **Classification des revenus** → **Lancer l'analyse**.
La page de résultats affiche : la classe prédite et sa probabilité, les facteurs qui l'expliquent (SHAP), la comparaison avec des profils réels
(même métier / études / âge / horaires), des leviers théoriques, les taux de revenu élevé par caractéristique et les avertissements.

- `POST /api/income/analyze/` : `{age, education_num, relationship, sex, hours_per_week?, capital_gain?, capital_loss?, occupation?, occupation_text?}`
- Modèle : `models/catboost_adult.pkl` (nécessite `pip install -r requirements.txt` → paquet `catboost`). Vérification : `python manage.py test_income`.
- Prétraitement identique à l'entraînement : log1p (gains/pertes), écrêtage âge/heures sur `bornes`, métier manquant → « Inconnu ».
- Le métier du CV (texte libre) est converti en catégorie Adult par des règles (`segmentation/income.py`) ; le RH peut le corriger dans la liste.
- ⚠️ Données du recensement US de 1994 (seuil 50 000 $) : résultat indicatif. Le sexe et le rôle familial sont des variables sensibles du modèle,
  signalées à l'écran : ne jamais les utiliser pour une décision d'embauche ou de rémunération.
- **Après modification du front : `cd frontend && npm run build`** (le dossier `dist` doit être reconstruit pour voir la nouvelle page).

## Recommandation salariale et rapport PDF (USD)
- `POST /api/salary/recommend/` : `{role?, occupation_text?, years?, level? (junior|confirme|senior), expected_monthly?}` : fourchette mensuelle, salaire conseillé, estimation annuelle, justification et comparaison avec un salaire saisi.
- `POST /api/income/report/` : mêmes champs que l'analyse + `candidate_name` : rapport PDF téléchargeable.
- Référentiel : `data/salary_reference.json` (BLS, Occupational Outlook Handbook, mai 2025 : médiane, 10e et 90e percentiles). Seuls les métiers présents dans ce fichier reçoivent une recommandation ; sinon l'application indique que les données sont indisponibles.
- Le score du modèle de revenu n'entre pas dans le calcul salarial. Les montants sont des références américaines nationales, à valider avant toute offre.
- Tests : `python manage.py test segmentation`.

### Lancer le projet
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cd frontend && npm install && npm run build && cd ..
    python manage.py test segmentation
    python manage.py runserver

## 🧩 Segmentation professionnelle (K-Means : `kmeans_profils_socio_economiques.pkl`)
Parcours : **Analyse des profils** → import du CV → vérification (âge, niveau d'études, heures/semaine, et « Revenu > 50 000 $ ? » facultatif)
→ cocher **Segmentation professionnelle** → **Lancer l'analyse**. La page de résultats affiche : le cluster du candidat et le nom du profil, la fiabilité de
l'affectation, les moyennes du profil (âge, tranche d'âge, études, heures, % de revenus > 50K $, métiers dominants), la comparaison candidat / profil / ensemble,
les 4 profils, et **une seule carte** : la carte des individus (ACP 2D) avec le candidat en étoile. La page **Segmentation RH** affiche les mêmes profils sur les données réelles de l'application.

- `POST /api/professional/analyze/` : `{age, education_num, hours_per_week, income_sup50k? (0|1)}` → candidat, profils, moyennes, carte (PNG base64).
- `GET  /api/professional/clusters/` : les 4 profils avec leurs moyennes + la carte des individus.
- Code : `segmentation/professional.py` (modèle + calculs), `segmentation/views_professional.py` (API), tests : `python manage.py test segmentation.tests_professional`.
- Le `.pkl` est utilisé tel quel (scaler + K-Means, jamais ré-entraîné). Si le revenu n'est pas saisi, il est estimé (régression logistique sur âge, études, heures) et l'écran l'indique.
- Les noms des profils (0 à 3) sont dans `PROFILES` (`professional.py`). Ils ne sont utilisés que si les centres du `.pkl` correspondent ; sinon des noms génériques sont générés.
- Les moyennes dépendent des données chargées : avec `adult.data` + `adult.test` (voir `import_adult`), les chiffres se rapprochent de ceux du notebook.
- Front : `frontend/src/App.tsx` (`ProfessionalClusteringModule`, `ProfessionalOverview`). Après modification : `cd frontend && npm run build`.
- Page **Segmentation RH** : le formulaire du haut utilise désormais votre modèle (âge, études, heures, revenu). L'ancien panneau « profils familiaux » (modèle `modele_profilpro.pkl`, signalé incohérent) n'y est plus affiché ; son code reste dans `App.tsx` (`FamilySegmentationPanel`), et la segmentation familiale reste disponible dans *Analyse des profils*.

## 🎓 Prédiction du niveau d'éducation (XGBoost : `xgboost_education.pkl`)
Page **Prédiction du niveau d'éducation** (menu de gauche). Formulaire en 4 blocs → probabilités par niveau, interprétation, résumé du profil, détails repliables.

- `GET /api/education/options/` : listes déroulantes (catégories du modèle). `POST /api/education/predict/` :
  `{age, sex, race, native_country, marital_status, relationship, workclass, occupation, hours_per_week, income}` (valeurs du dataset Adult, ex. `"Private"`, `">50K"`).
- Code : `segmentation/education.py` (validation, encodage identique à l'entraînement, inférence), `segmentation/views_education.py` (API), tests : `python manage.py test segmentation.tests_education`.
- Le modèle attend **79 colonnes** : âge, sexe (0/1), heures, `income_>50K`, puis des indicateurs one-hot (`get_dummies(drop_first=True)` : catégories de référence Federal-gov, Divorced, Adm-clerical, Husband, Amer-Indian-Eskimo, Cambodia = tous les indicateurs à 0). Pas de mise à l'échelle.
  La variable **`income_>50K`** fait partie des entrées du modèle : le formulaire la demande donc (« Tranche de revenu annuel »).
- Classes : 3 (`Below_HS`, `HS_Graduate`, `Higher_Education`). ⚠️ Le dictionnaire `classes` stocké dans le .pkl (1 = Higher_Education, 2 = HS_Graduate) est **inversé** par rapport au comportement réel du modèle ;
  `CLASS_ORDER` dans `education.py` utilise l'ordre vérifié sur `adult.test` (0 = Below_HS, 1 = HS_Graduate, 2 = Higher_Education). À mettre à jour si vous ré-exportez le .pkl.
- Encodage du sexe supposé : Female = 0, Male = 1 (`SEX_CODE`) ; le .pkl ne le précise pas.
- Dépendance ajoutée : `xgboost>=3.4.1` (`pip install -r requirements.txt`). Le .pkl est chargé une seule fois (`lru_cache`) ; c'est un fichier du dépôt, jamais un fichier envoyé par l'utilisateur.
- Aucune donnée saisie n'est enregistrée. **Après modification du front : `cd frontend && npm install && npm run build`** (le `dist/` fourni ne contient pas encore cette page).

## ⏱️ Régression des heures de travail (XGBoost)
Parcours : **Analyse des profils** → import du CV → « Analyser le CV » → compléter âge, études, statut marital, rôle familial, sexe
(+ métier et revenu, facultatifs) → cocher **Régression des heures de travail** → **Lancer l'analyse**.
La page de résultats affiche : les **heures par semaine prédites** et une fourchette indicative (80 % des cas), l'écart avec la moyenne,
les points clés (effet de chaque caractéristique en heures), la comparaison avec des profils réels (même métier / études / âge / profil proche),
la répartition des horaires, les heures moyennes par métier / études / âge, des simulations « et si le profil changeait ? » et la qualité du modèle (MAE, R²).

- `POST /api/hours/analyze/` : `{age, education_num, marital_status, relationship, sex, occupation?, occupation_text?, income_sup50k?}`
- `segmentation/hours.py` : XGBRegressor du notebook (`learning_rate=0.05, max_depth=7, n_estimators=100, subsample=0.8`), cible `hours-per-week`.
  Il n'utilise que les variables collectées par l'application ; le métier et le revenu inconnus sont gérés (revenu masqué dans 25 % des lignes à l'entraînement).
- Modèle : `models/xgboost_hours.pkl`. S'il est absent ou illisible (autre version de xgboost), il est **entraîné automatiquement au premier appel**
  (quelques secondes) sur les données de l'application (table `adult_person` ou `data/adult.test`) puis sauvegardé.
  Forcer le ré-entraînement : `python manage.py train_hours`. Tests : `python manage.py test segmentation.tests_hours`.
- ⚠️ `frontend/dist/` a été retiré de cette version : `demarrer.bat` / `demarrer.sh` reconstruisent le front (Node requis) et créent `models/xgboost_hours.pkl` automatiquement.
  À la main : `cd frontend && npm install && npm run build`, puis `python manage.py train_hours`.
- Limites : le modèle explique peu de variations (R² ≈ 0,25-0,3 ; erreur moyenne ≈ 7 h) → utiliser la fourchette ; sexe, statut marital et rôle familial
  sont des variables sensibles à ne jamais utiliser pour décider.
