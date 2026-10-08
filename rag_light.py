"""RAG خفيف للسحابة: TF-IDF على حروف الكلمات (من غير torch ولا Embeddings تقيلة)"""
import glob, os
from langchain_community.retrievers import TFIDFRetriever
 
def get_light_retriever(k: int = 3):
    base = os.path.dirname(os.path.abspath(__file__))
    texts = []
    for f in glob.glob(os.path.join(base, "data", "**", "*.txt"), recursive=True):
        raw = open(f, encoding="utf-8").read()
        texts += [t.strip() for t in raw.split("\n\n") if t.strip()]   # كل نوع نصب = chunk
    if not texts:
        raise FileNotFoundError(
            "مفيش ملفات في فولدر data. لازم يبقى فيه data/scam_patterns.txt (وفيه محتوى) على GitHub.")
    return TFIDFRetriever.from_texts(texts, tfidf_params={"analyzer": "char_wb", "ngram_range": (2, 4)}, k=k)
 
