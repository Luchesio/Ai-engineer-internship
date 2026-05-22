# Text Dataset Cleaner

A Python script that fetches a sample text corpus (news articles and product reviews), cleans and preprocesses the text, and saves the results to a CSV file.

---

## What It Does

| Step             | Action                                                                               |
| ---------------- | ------------------------------------------------------------------------------------ |
| Fetch            | Loads a built-in sample corpus of 10 documents (tech reviews, news, product reviews) |
| Lowercase        | Converts all text to lowercase                                                       |
| Strip noise      | Removes URLs, numbers, and punctuation                                               |
| Tokenize         | Splits text into individual word tokens using NLTK                                   |
| Remove stopwords | Filters out common English stopwords (e.g. _the_, _is_, _at_)                        |
| Export           | Saves all results to `cleaned_dataset.csv`                                           |

---

## Requirements

- Python 3.10+
- pip packages: `nltk`, `pandas`

---

## Setup & Usage

**1. Clone or download the project files**

```bash
git clone <your-repo-url>
cd <project-folder>
```

**2. Install dependencies**

```bash
pip install nltk pandas
```

or

```bash
pip install -r requirements.txt
```

**3. Run the script**

```bash
python text_cleaner.py
```

The script will automatically download the required NLTK data (`stopwords`, `punkt`) on first run.

---

## Output

A file named `cleaned_dataset.csv` is created in the working directory with the following columns:

| Column          | Description                                        |
| --------------- | -------------------------------------------------- |
| `id`            | Document identifier                                |
| `source`        | Category (`tech_review`, `news`, `product_review`) |
| `original_text` | Raw input text                                     |
| `cleaned_text`  | Lowercased, punctuation-free text                  |
| `tokens`        | Space-separated list of meaningful tokens          |
| `token_count`   | Number of tokens after cleaning                    |

---

## Extending the Script

To use your own dataset, replace the `fetch_sample_corpus()` return value with a list of dicts following this shape:

```python
{"id": 1, "source": "my_source", "text": "Your raw text here..."}
```

You can also swap in data from a CSV, database, or API — the `process_corpus()` and `save_to_csv()` functions remain unchanged.
