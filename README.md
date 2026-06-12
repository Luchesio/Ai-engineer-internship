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

# Task 3 — Simple Chatbot (LangChain + OpenAI + FastAPI)

A minimal chatbot that accepts user questions and returns answers using a LangChain chain (LCEL), served over FastAPI with Uvicorn. It uses the `gpt-4o-mini` model and keeps short per-session conversation memory.

## How It Works

| Piece              | Role                                                                                    |
| ------------------ | --------------------------------------------------------------------------------------- |
| `chatbot.py`       | Builds the LangChain chain (`prompt \| model \| parser`) and tracks per-session history |
| `main.py`          | FastAPI app exposing `/chat`, `/reset`, and a health check at `/`                       |
| `requirements.txt` | Dependencies                                                                            |
| `.env.example`     | Template for required environment variables                                             |

The chain is composed with LangChain Expression Language (LCEL). A `ChatPromptTemplate` feeds a `ChatOpenAI` model, and `StrOutputParser` turns the model output into plain text. Past turns are stored in memory per `session_id` and replayed into the prompt on each call.

## Setup

**1. Install dependencies**

```bash
cd "Task 3"
pip install -r requirements.txt
```

**2. Configure your API key**

Copy the example env file and add your real OpenAI key:

```bash
cp .env.example .env
```

Then edit `.env`:

```
OPENAI_API_KEY=sk-...your actual key...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.3
```

Get a key from the OpenAI dashboard at https://platform.openai.com/api-keys.

| Variable             | Required | Default       | Purpose                                      |
| -------------------- | -------- | ------------- | -------------------------------------------- |
| `OPENAI_API_KEY`     | Yes      | —             | Your OpenAI secret key                       |
| `OPENAI_MODEL`       | No       | `gpt-4o-mini` | Chat model to use                            |
| `OPENAI_TEMPERATURE` | No       | `0.3`         | Higher = more creative, lower = more focused |

The key is read from the environment (loaded from `.env` via `python-dotenv`). It is never hard-coded. As an alternative to a `.env` file, you can export it in your shell:

```bash
export OPENAI_API_KEY=sk-...
```

**3. Run the server**

```bash
uvicorn main:app --reload
```

The app starts on http://127.0.0.1:8000. Interactive docs are at http://127.0.0.1:8000/docs.

## Usage

Ask a question:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is FastAPI in one sentence?", "session_id": "user1"}'
```

Response:

```json
{
  "answer": "FastAPI is a modern Python web framework for building APIs quickly...",
  "session_id": "user1"
}
```

Reuse the same `session_id` to keep conversation context. Clear it with:

```bash
curl -X POST "http://127.0.0.1:8000/reset?session_id=user1"
```

## Notes

- Memory is in-process, so it resets when the server restarts. For production, replace the in-memory history dict with a persistent backend (Redis, a database, etc.).
- `gpt-4o-mini` is set as the default. If your account lacks access to a given model, change `OPENAI_MODEL` in `.env` to one you can use.
- Never commit your `.env` file or real key to version control.

# Data Ingestion Notebook (pandas)

`data_ingestion.ipynb` is a reusable pandas workflow that takes raw data from CSV, JSON, or plain text into a clean, analysis-ready CSV. It generates a small messy sample dataset so it runs end to end with no external files — point `load_data` at your own path to use it for real.

## Pipeline

| Step              | Action                                                                                        |
| ----------------- | --------------------------------------------------------------------------------------------- |
| Load              | `load_data()` dispatches on file extension: `.csv`, `.json`, and `.txt`/`.text`               |
| Inspect           | `shape`, `dtypes`, `head()`, and a missing-value count on the raw frame                       |
| Normalize columns | Lowercases, strips whitespace, drops punctuation, and turns spaces into underscores           |
| Handle missing    | Drops empty rows/columns; fills numeric gaps with the median, text/categorical with `unknown` |
| EDA               | `head()`, `describe()` (numeric and object), and `value_counts()` on key categories           |
| Export            | Saves the cleaned frame to `cleaned_orders.csv`                                               |

## Requirements

- Python 3.10+
- pip packages: `pandas`, `jupyter` (or `notebook` / JupyterLab)

## Usage

```bash
pip install pandas jupyter
jupyter notebook data_ingestion.ipynb
```

Run the cells top to bottom. The notebook writes the sample inputs to `sample_data/` and the result to `cleaned_orders.csv`.

## Using Your Own Data

Replace the sample path with your file — the rest of the pipeline is unchanged:

```python
df = load_data("path/to/your_file.csv")   # or .json / .txt
df = normalize_columns(df)
df = handle_missing(df)
df.to_csv("cleaned_output.csv", index=False)
```

`load_data` returns a DataFrame for CSV and JSON; text files become a single `text` column with blank lines dropped.
