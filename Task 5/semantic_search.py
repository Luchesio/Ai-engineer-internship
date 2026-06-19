import json
import sys
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 3

INDEX_DIR = Path(__file__).parent / "index"
DOCS_PATH = INDEX_DIR / "documents.json"
EMBEDDINGS_PATH = INDEX_DIR / "embeddings.npy"

DOCUMENTS = [
    "Regularly updating your software patches security holes before attackers can exploit them.",
    "To extend a lithium-ion battery's lifespan, avoid full discharges and keep the charge between 20 and 80 percent.",
    "A password manager lets you use strong, unique passwords for every account without memorizing them.",
    "Electric cars produce no tailpipe emissions, though their footprint depends on how the electricity is generated.",
    "Drinking enough water through the day supports concentration, mood, and steady energy levels.",
    "A diet rich in vegetables, whole grains, and lean protein lowers the risk of chronic disease.",
    "Regular exercise strengthens the heart, improves sleep, and helps the body manage stress.",
    "Reading before bed and dimming bright screens signals the body to wind down and improves sleep quality.",
    "Compound interest grows your savings faster because you earn returns on returns you already earned.",
    "Spreading investments across different asset classes softens the blow of any single market downturn.",
    "Searing meat at high heat before slow cooking builds deeper flavor through the Maillard reaction.",
    "Letting bread dough rise slowly in the fridge overnight improves both its flavor and its texture.",
    "Honeybees pollinate a large share of the crops we eat, making them vital to the global food supply.",
    "Composting kitchen scraps keeps waste out of landfills and produces nutrient-rich soil for the garden.",
]

DEMO_QUERIES = [
    "How can I make my phone battery last longer?",
    "Ways to keep my computer safe from hackers",
    "Tips for cooking a tastier steak",
    "What helps me sleep better at night?",
    "How do I grow my money over time?",
    "Why do bees matter so much?",
]

_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed(texts: list[str]) -> np.ndarray:
    vectors = get_model().encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return vectors.astype("float32")


class VectorStore:
    def __init__(self, documents=None, embeddings=None):
        self.documents = documents or []
        self.embeddings = embeddings if embeddings is not None else np.empty((0, 0), dtype="float32")

    def add(self, documents: list[str], embeddings: np.ndarray) -> None:
        self.documents = list(documents)
        self.embeddings = embeddings

    def search(self, query_vector: np.ndarray, k: int = TOP_K) -> list[tuple[str, float]]:
        scores = self.embeddings @ query_vector
        top = np.argsort(scores)[::-1][:k]
        return [(self.documents[i], float(scores[i])) for i in top]

    def save(self, docs_path: Path = DOCS_PATH, embeddings_path: Path = EMBEDDINGS_PATH) -> None:
        docs_path.parent.mkdir(parents=True, exist_ok=True)
        docs_path.write_text(json.dumps(self.documents, indent=2), encoding="utf-8")
        np.save(embeddings_path, self.embeddings)

    @classmethod
    def load(cls, docs_path: Path = DOCS_PATH, embeddings_path: Path = EMBEDDINGS_PATH) -> "VectorStore":
        documents = json.loads(docs_path.read_text(encoding="utf-8"))
        embeddings = np.load(embeddings_path)
        return cls(documents, embeddings)


def build_index(documents: list[str] = DOCUMENTS) -> VectorStore:
    store = VectorStore()
    store.add(documents, embed(documents))
    store.save()
    return store


def load_or_build_index() -> VectorStore:
    if DOCS_PATH.exists() and EMBEDDINGS_PATH.exists():
        return VectorStore.load()
    return build_index()


def search(store: VectorStore, query: str, k: int = TOP_K) -> list[tuple[str, float]]:
    return store.search(embed([query])[0], k)


def main() -> None:
    store = load_or_build_index()
    print(f"Indexed {len(store.documents)} documents with '{MODEL_NAME}'.\n")

    queries = sys.argv[1:] or DEMO_QUERIES
    for query in queries:
        print(f"Query: {query}")
        for rank, (doc, score) in enumerate(search(store, query, TOP_K), start=1):
            print(f"  {rank}. [{score:.3f}] {doc}")
        print()


if __name__ == "__main__":
    main()
