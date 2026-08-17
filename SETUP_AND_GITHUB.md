# Setup local (Anaconda) + Push vers GitHub

## 1. Setup de l'environnement (Anaconda)

Ouvre ton terminal Anaconda (Anaconda Prompt sur Windows, ou terminal normal sur Mac/Linux) :

```bash
# Aller dans le dossier du projet
cd chemin/vers/mini_document_ai_project

# Créer l'environnement conda à partir du fichier fourni
conda env create -f environment.yml

# Activer l'environnement
conda activate arabic-document-ai
```

## 2. Installer Tesseract OCR (moteur externe, pas juste un package Python)

**Windows :**
- Télécharge l'installeur ici : https://github.com/UB-Mannheim/tesseract/wiki
- Pendant l'installation, coche la langue **Arabic** dans les options
- Ajoute le chemin d'installation (ex: `C:\Program Files\Tesseract-OCR`) à ta variable PATH

**Mac :**
```bash
brew install tesseract
brew install tesseract-lang   # installe tous les packs de langue, dont l'arabe
```

**Linux (Ubuntu/Debian) :**
```bash
sudo apt install tesseract-ocr
sudo apt install tesseract-ocr-ara   # pack langue arabe
```

Vérifie que l'arabe est bien installé :
```bash
tesseract --list-langs
# tu dois voir "ara" dans la liste
```

## 3. Lancer le pipeline

```bash
python pipeline_full.py
```

Tu dois voir l'angle de skew détecté, le texte OCR, le JSON structuré, et les résultats RAG s'afficher dans le terminal.

### Pour l'adapter à un vrai texte arabe :
Dans `pipeline_full.py`, à la fonction `run_ocr`, change simplement :
```python
pytesseract.image_to_string(Image.fromarray(preprocessed_img))
```
en :
```python
pytesseract.image_to_string(Image.fromarray(preprocessed_img), lang='ara')
```

## 4. Initialiser Git et pousser vers GitHub

### a) Créer le repo sur GitHub d'abord
Va sur https://github.com/new, choisis un nom (ex: `arabic-document-ai-demo`), **ne coche PAS** "Initialize with README" (on a déjà nos fichiers), clique "Create repository".

### b) Dans ton terminal, depuis le dossier du projet :

```bash
# Initialiser git
git init

# Ajouter tous les fichiers (le .gitignore fourni exclut déjà les fichiers inutiles)
git add .

# Premier commit
git commit -m "Initial commit: Arabic Document AI mini pipeline demo"

# Lier ton repo local au repo GitHub (remplace par TON URL, visible sur la page GitHub après création)
git remote add origin https://github.com/TON-USERNAME/arabic-document-ai-demo.git

# Renommer la branche en 'main' si besoin
git branch -M main

# Pousser vers GitHub
git push -u origin main
```

### c) Vérifier
Rafraîchis la page de ton repo sur GitHub — tous les fichiers doivent apparaître.

## 5. Bonus — bien présenter le repo pour l'entretien
- Renomme `README_mini_project.md` en `README.md` (GitHub l'affiche automatiquement sur la page d'accueil du repo)
- Ajoute une capture d'écran du `structured_output.json` ou d'une des images d'étape dans le README pour que ça soit visuel
- Dans ta description GitHub du repo, mets une phrase courte : *"Demo pipeline reproducing an Arabic-first Document AI workflow: preprocessing, OCR, classification, NER, confidence scoring, and RAG retrieval with citations."*

C'est un bon point à mentionner en entretien : *"I put together a small demo repo reproducing the pipeline architecture to make sure I could explain and defend every step concretely."*
