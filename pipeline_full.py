"""
Mini Document AI Pipeline - Demo (for interview prep)
Pipeline: raw scan -> preprocessing -> OCR -> classification -> NER -> structured JSON -> RAG

NOTE: Classification/NER here are simple rule-based stubs. In production,
replace with fine-tuned AraBERT/MARBERT (classification) and a fine-tuned
NER model or LayoutLM (field extraction). RAG uses TF-IDF as a lightweight
stand-in for multilingual neural embeddings (multilingual-e5, LaBSE).
"""
import cv2
import numpy as np
import pytesseract
from PIL import Image
import re
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ---------- STEP 1: PREPROCESSING ----------
def preprocess_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=15)
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    coords = np.column_stack(np.where(binary == 0))
    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90 + angle) if angle < -45 else -angle

    h, w = binary.shape
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    deskewed = cv2.warpAffine(binary, M, (w, h), flags=cv2.INTER_CUBIC, borderValue=255)
    return deskewed, angle


# ---------- STEP 2: OCR ----------
def run_ocr(preprocessed_img):
    return pytesseract.image_to_string(Image.fromarray(preprocessed_img))


# ---------- STEP 3: CLASSIFICATION (stub - replace with fine-tuned AraBERT/MARBERT) ----------
def classify_document(text):
    text_lower = text.lower()
    if 'invoice' in text_lower:
        return 'invoice', 0.94
    elif 'contract' in text_lower:
        return 'contract', 0.88
    return 'unknown', 0.40


# ---------- STEP 4: NER / FIELD EXTRACTION (stub - replace with fine-tuned NER/LayoutLM) ----------
def extract_fields(text):
    fields = {}
    inv_match = re.search(r'Number\s+([A-Z]{2,3}[-\s]?\d{4}[-\s]?\d+)', text)
    fields['invoice_number'] = {'value': inv_match.group(1) if inv_match else None,
                                 'confidence': 0.65 if inv_match else 0.0}
    date_match = re.search(r'Date\s+(\d{4}-\d{2}-\d{2})', text)
    fields['date'] = {'value': date_match.group(1) if date_match else None,
                       'confidence': 0.98 if date_match else 0.0}
    amount_match = re.search(r'Amount\s+([\d.]+\s*\w+)', text)
    fields['amount'] = {'value': amount_match.group(1) if amount_match else None,
                         'confidence': 0.95 if amount_match else 0.0}
    return fields


# ---------- STEP 5: RAG (stub - replace TF-IDF with multilingual-e5/LaBSE + FAISS/Qdrant) ----------
def rag_search(query, chunks, top_k=2):
    texts = [c['text'] for c in chunks]
    vectorizer = TfidfVectorizer()
    chunk_vectors = vectorizer.fit_transform(texts)
    query_vector = vectorizer.transform([query])
    similarities = cosine_similarity(query_vector, chunk_vectors)[0]
    top_idx = np.argsort(similarities)[::-1][:top_k]
    return [(chunks[i], similarities[i]) for i in top_idx]


if __name__ == "__main__":
    # Full pipeline run
    preprocessed, skew_angle = preprocess_image("raw_scan_messy.png")
    print(f"Deskew angle corrected: {skew_angle:.2f} degrees")

    raw_text = run_ocr(preprocessed)
    print(f"\nOCR output:\n{raw_text}")

    doc_type, class_conf = classify_document(raw_text)
    fields = extract_fields(raw_text)

    result = {
        'document_type': doc_type,
        'classification_confidence': class_conf,
        'fields': fields,
        'needs_human_review': any(f['confidence'] < 0.80 for f in fields.values())
    }
    print(f"\nStructured output:\n{json.dumps(result, indent=2)}")

    # RAG demo
    chunks = [
        {"text": "Invoice INV-2026-0472 issued to Ahmed Ben Salah for 1250.00 TND, paid status.",
         "doc": "invoice_0472.pdf", "page": 1},
        {"text": "Contract renewal terms for client Ahmed Ben Salah effective January 2026.",
         "doc": "contract_2026.pdf", "page": 3},
    ]
    results = rag_search("What is the payment status for Ahmed Ben Salah's invoice?", chunks)
    print("\nRAG retrieval results:")
    for chunk, score in results:
        print(f"  [{score:.3f}] {chunk['doc']} p.{chunk['page']}: {chunk['text']}")
