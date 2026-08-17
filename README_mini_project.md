# Mini Document AI Pipeline — Demo Project

Ce projet démontre, étape par étape, le pipeline Document AI décrit dans le CV :
scan brut → preprocessing → OCR → classification → NER → structured JSON → RAG search.

## ⚠️ Limitations de cette démo (à connaître avant l'entretien)
- Exécutée SANS accès internet → pas de modèle Arabic OCR (`ara.traineddata`) ni de
  vrais modèles Transformer (AraBERT/MARBERT). Le texte de démo est en anglais,
  mais **la structure du pipeline est identique**.
- Classification & NER sont ici des règles simples (regex/mots-clés) — en
  production ce sont des modèles fine-tunés (AraBERT/MARBERT pour classification,
  NER Transformer pour l'extraction de champs).
- RAG utilise TF-IDF (léger, local) au lieu d'embeddings neuronaux
  (multilingual-e5, LaBSE) — le principe de retrieval + citation reste le même.

## Pour adapter à un vrai cas Arabic (ce qu'il faudrait faire en environnement réel)
1. `sudo apt install tesseract-ocr-ara` (ou utiliser un moteur HTR comme TrOCR
   fine-tuné pour l'arabe pour le manuscrit)
2. Remplacer le classifieur par un `AraBERT`/`MARBERT` fine-tuné (Hugging Face
   Transformers) sur des classes de documents réelles
3. Remplacer le NER regex par un modèle NER fine-tuné (ou layout-aware comme
   LayoutLM) pour gérer les templates variables
4. Remplacer TF-IDF par des embeddings multilingues (multilingual-e5, LaBSE) +
   une vraie base vectorielle (FAISS/Qdrant pour déploiement on-premise)

## Fichiers du pipeline
| Fichier | Étape |
|---|---|
| `raw_scan.png` | Document synthétique "propre" |
| `raw_scan_messy.png` | Simulation d'un scan réel (bruit + rotation 2.5°) |
| `step1_grayscale.png` → `step4_deskewed.png` | Étapes de preprocessing |
| `raw_text.txt` | Sortie OCR brute (avec erreurs réelles) |
| `structured_output.json` | Résultat final structuré avec confidence scoring |

## Scripts
Voir `pipeline_full.py` pour le code complet, commenté étape par étape.
