import re
import string
import csv
import urllib.request
import json
import nltk
import pandas as pd
from pathlib import Path
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.download("stopwords", quiet=True)
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

STOP_WORDS = set(stopwords.words("english"))
OUTPUT_PATH = Path("cleaned_dataset.csv")


def fetch_sample_corpus() -> list[dict]:
    url = "https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/webtext.zip"

    articles = [
        {
            "id": 1,
            "source": "tech_review",
            "text": "Apple's latest iPhone 15 Pro delivers exceptional performance. The A17 Pro chip handles demanding tasks effortlessly, while the titanium frame feels premium. Camera improvements are notable, especially in low-light conditions. Battery life has improved over previous models. The price point remains steep at $999, but power users will appreciate the upgrades.",
        },
        {
            "id": 2,
            "source": "tech_review",
            "text": "Samsung Galaxy S24 Ultra redefines Android flagships! The Snapdragon 8 Gen 3 processor blazes through applications. However, the S-Pen stylus integration remains unmatched for productivity. Display quality is simply stunning — 6.8 inches of pure brilliance. Battery consumption could be better optimized, though.",
        },
        {
            "id": 3,
            "source": "news",
            "text": "Scientists have discovered a new exoplanet within the habitable zone of its star, located 40 light-years away. The planet, designated Kepler-452c, shows signs of liquid water on its surface. Researchers at NASA confirmed these findings after years of telescope observations. This discovery raises new questions about the possibility of extraterrestrial life.",
        },
        {
            "id": 4,
            "source": "news",
            "text": "Global electric vehicle sales surpassed 10 million units in 2023, marking a significant milestone for the industry. China leads adoption rates, followed by Europe and North America. Major automakers are accelerating their transition away from combustion engines. Infrastructure challenges, particularly charging networks, remain a key concern.",
        },
        {
            "id": 5,
            "source": "product_review",
            "text": "Bought this coffee maker three months ago and it's been fantastic! Brews a full pot in under 8 minutes. The built-in grinder preserves freshness perfectly. Cleanup is straightforward — just rinse the removable parts. Honestly the best $120 I've spent. My mornings are so much better now.",
        },
        {
            "id": 6,
            "source": "product_review",
            "text": "Deeply disappointed with this laptop stand. It wobbles constantly, even on flat surfaces. The adjustment mechanism jammed after two weeks of use. Customer support was unhelpful and slow. For $45, I expected much better build quality. Returning it immediately.",
        },
        {
            "id": 7,
            "source": "news",
            "text": "The Federal Reserve announced a pause in interest rate hikes amid cooling inflation data. Consumer prices rose just 3.2% year-over-year, down from a peak of 9.1% in 2022. Economists are divided on whether rate cuts will begin in 2024. Financial markets responded positively, with major indices climbing throughout the session.",
        },
        {
            "id": 8,
            "source": "tech_review",
            "text": "OpenAI's GPT-4 continues to dominate the large language model landscape. Its reasoning capabilities outperform competitors on most benchmarks. Developers appreciate the robust API and thorough documentation. Token costs have decreased significantly over the past year. Context window expansion to 128k tokens opened entirely new use cases.",
        },
        {
            "id": 9,
            "source": "product_review",
            "text": "These running shoes exceeded all expectations!! The foam cushioning absorbs impact beautifully. Breathable mesh keeps feet cool during long runs. Sizing runs slightly large — order half a size down. After 200+ miles they still look and feel great. Worth every penny of the $150 price tag.",
        },
        {
            "id": 10,
            "source": "news",
            "text": "Wildfire season across the western United States has intensified due to prolonged drought conditions. Over 1.2 million acres have burned so far this year. Emergency services are stretched thin across multiple states. Climate scientists warn that hotter, drier summers will make future seasons increasingly severe without meaningful policy intervention.",
        },
    ]

    return articles


def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"\d+", "", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def remove_stopwords_and_tokenize(text: str) -> list[str]:
    tokens = word_tokenize(text)
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


def process_corpus(articles: list[dict]) -> pd.DataFrame:
    records = []

    for article in articles:
        raw_text = article["text"]
        cleaned = clean_text(raw_text)
        tokens = remove_stopwords_and_tokenize(cleaned)

        records.append(
            {
                "id": article["id"],
                "source": article["source"],
                "original_text": raw_text,
                "cleaned_text": cleaned,
                "tokens": tokens,
                "token_count": len(tokens),
            }
        )

    return pd.DataFrame(records)


def save_to_csv(df: pd.DataFrame, path: Path) -> None:
    df["tokens"] = df["tokens"].apply(lambda t: " ".join(t))
    df.to_csv(path, index=False, quoting=csv.QUOTE_ALL)
    print(f"Saved {len(df)} records → {path}")


def main():
    print("Fetching corpus...")
    articles = fetch_sample_corpus()

    print(f"Processing {len(articles)} documents...")
    df = process_corpus(articles)

    save_to_csv(df, OUTPUT_PATH)

    print("\nSample output:")
    print(df[["id", "source", "token_count"]].to_string(index=False))
    print(f"\nAverage tokens per document: {df['token_count'].mean():.1f}")


if __name__ == "__main__":
    main()