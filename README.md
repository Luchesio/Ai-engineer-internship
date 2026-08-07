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

# Task 5 — Semantic Search (Embeddings + Top-K Retrieval)

`semantic_search.py` stores a small set of text documents, indexes them as embeddings, and retrieves the most relevant ones for a query by **semantic similarity** rather than keyword matching. This is the retrieval core behind a RAG pipeline.

## How It Works

| Piece           | Role                                                                                     |
| --------------- | ---------------------------------------------------------------------------------------- |
| `embed()`       | Turns text into normalized vectors with the `all-MiniLM-L6-v2` sentence-transformer      |
| `VectorStore`   | Holds documents + embeddings; handles cosine search and saving/loading the index to disk |
| `build_index()` | Embeds the document set and persists it under `index/`                                   |
| `search()`      | Embeds a query and returns the top-k closest documents with similarity scores            |

Embeddings are L2-normalized, so cosine similarity reduces to a single dot product (`embeddings @ query`). The index — `index/documents.json` and `index/embeddings.npy` — is written on the first run and reused afterward, so documents are stored once and retrieved on demand.

Because matching happens in embedding space, a query like _"How can I make my phone battery last longer?"_ surfaces the document about lithium-ion battery lifespan even though they share almost no words.

## Requirements

- Python 3.10+
- pip packages: `sentence-transformers`, `numpy`

The model (~80 MB) downloads automatically from Hugging Face on first run.

## Setup & Usage

```bash
pip install -r requirements.txt
cd "Task 5"
python semantic_search.py
```

The script builds the index (first run only), then prints the top-3 results for a set of demo queries:

```
Query: How can I make my phone battery last longer?
  1. [0.541] To extend a lithium-ion battery's lifespan, avoid full discharges and keep the charge between 20 and 80 percent.
  2. [0.187] Electric cars produce no tailpipe emissions, though their footprint depends on how the electricity is generated.
  3. [0.143] Regular exercise strengthens the heart, improves sleep, and helps the body manage stress.
```

Pass your own queries as command-line arguments to search interactively:

```bash
python semantic_search.py "what should I eat to stay healthy" "how do I save bread for later"
```

## Using Your Own Data

Replace the `DOCUMENTS` list with your own texts, delete the `index/` folder so it rebuilds, and run again:

```python
DOCUMENTS = ["Your first document...", "Your second document..."]
```

For larger collections, swap the in-memory `VectorStore` for a dedicated vector database (FAISS, Chroma, Qdrant) — the `embed()` / `search()` interface stays the same.

# Task 6 — Notebook with RAG-Powered Q&A (FAISS)

`Task 6/rag_qa.ipynb` answers domain-specific questions by **retrieving** relevant passages from a knowledge base and **generating** an answer grounded in them. It combines the embedding/retrieval idea from Task 5 with the OpenAI model from Task 3, swapping the hand-rolled vector store for a **FAISS** index.

## How It Works

| Step      | Action                                                                               |
| --------- | ------------------------------------------------------------------------------------ |
| Documents | A small domain knowledge base (a fictional product, _Lumen_) defined in the notebook |
| Chunk     | Each document is split into overlapping word windows that keep their source title    |
| Embed     | Chunks are encoded into normalized vectors with `all-MiniLM-L6-v2`                   |
| Index     | Vectors go into a FAISS `IndexFlatIP` (cosine similarity on normalized vectors)      |
| Retrieve  | The query is embedded and FAISS returns the top-k closest chunks with scores         |
| Generate  | Retrieved chunks become the context for the LLM, which answers and cites its sources |

The FAISS index and chunk metadata are written to `Task 6/rag_index/` on the first run and reused afterward. The model is told to answer **only** from the retrieved context and to say so when the answer isn't there — so out-of-domain questions get a grounded refusal instead of a hallucination.

Because the knowledge base describes a product the model has never seen, correct answers can only come from retrieval. That is the whole point of RAG, and it makes the demo easy to verify.

## Requirements

- Python 3.10+
- pip packages: `faiss-cpu`, `sentence-transformers`, `numpy`, `langchain-core`, `langchain-openai`, `python-dotenv`, `jupyter`

The embedding model (~80 MB) downloads automatically from Hugging Face on first run.

## Setup & Usage

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. (Optional) Configure your OpenAI key**

The generation step uses the same OpenAI setup as Task 3. Without a key the notebook still runs and returns the retrieved context, so you can see retrieval working first.

```bash
export OPENAI_API_KEY=sk-...your actual key...
# optional: export OPENAI_MODEL=gpt-4o-mini
```

**3. Run the notebook**

```bash
cd "Task 6"
jupyter notebook rag_qa.ipynb
```

Run the cells top to bottom. The notebook builds the FAISS index, then answers a set of in-domain questions (each with its sources) and one out-of-domain question to show the grounded refusal.

| Variable         | Required | Default       | Purpose                                                |
| ---------------- | -------- | ------------- | ------------------------------------------------------ |
| `OPENAI_API_KEY` | No\*     | —             | Enables LLM answer generation; omit for retrieval-only |
| `OPENAI_MODEL`   | No       | `gpt-4o-mini` | Chat model used to synthesize the answer               |

\*Without a key, the notebook returns the retrieved context instead of a generated answer.

## Using Your Own Data

1. Replace the `DOCUMENTS` list with your own `{"title": ..., "text": ...}` entries (or load them from files, a database, or an API).
2. Delete the `Task 6/rag_index/` folder so the index rebuilds against the new content.
3. Re-run the notebook top to bottom.

Tune `chunk_size` / `overlap` for your document length and `TOP_K` for how much context each answer sees. For large collections, swap `IndexFlatIP` for an approximate FAISS index such as `IndexIVFFlat` — the `retrieve()` / `answer()` interface stays the same.

# Task 7 — Real-Time Data Chatbot (Tool Calling + FastAPI)

A chatbot that answers questions using **live external data**. It builds on the Task 3 chatbot by giving the model tools it can call on its own: the LLM decides when a question needs current weather or exchange rates, calls the matching API, and answers from the real values it gets back.

## How It Works

| Piece          | Role                                                                                 |
| -------------- | ------------------------------------------------------------------------------------ |
| `tools.py`     | Two tools — `get_weather` (Open-Meteo) and `convert_currency` (open.er-api.com)      |
| `chatbot.py`   | Binds the tools to the model and runs the tool-calling loop with per-session history |
| `main.py`      | FastAPI app exposing `/chat`, `/reset`, and a health check at `/`                    |
| `.env.example` | Template for required environment variables                                          |

The model is bound to the tools with `bind_tools`. On each turn it may respond with tool calls instead of text; `ask()` runs those tools, appends the results, and calls the model again until it returns a final answer. Both APIs are keyless, so the only credential you need is an OpenAI key. The weather tool geocodes the city first, then reads current conditions; the currency tool pulls live rates and covers 160+ currencies (including NGN).

## Requirements

- Python 3.10+
- pip packages: `fastapi`, `uvicorn`, `httpx`, `langchain-core`, `langchain-openai`, `python-dotenv`, `pydantic`

## Setup

**1. Install dependencies**

```bash
cd "Task 7"
pip install -r ../requirements.txt
```

**2. Configure your API key**

```bash
cp .env.example .env
```

Then edit `.env`:

```
OPENAI_API_KEY=sk-...your actual key...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.2
```

| Variable             | Required | Default       | Purpose                                      |
| -------------------- | -------- | ------------- | -------------------------------------------- |
| `OPENAI_API_KEY`     | Yes      | —             | Your OpenAI secret key                       |
| `OPENAI_MODEL`       | No       | `gpt-4o-mini` | Chat model to use                            |
| `OPENAI_TEMPERATURE` | No       | `0.2`         | Higher = more creative, lower = more focused |

**3. Run the server**

```bash
uvicorn main:app --reload
```

The app starts on http://127.0.0.1:8000, with interactive docs at http://127.0.0.1:8000/docs.

## Usage

Ask about the weather:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the weather in Lagos right now?", "session_id": "user1"}'
```

Ask about currency:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How much is 50 USD in NGN?", "session_id": "user1"}'
```

Response:

```json
{
  "answer": "It's 29°C and partly cloudy in Lagos right now...",
  "session_id": "user1"
}
```

Reuse the same `session_id` to keep context (e.g. ask a follow-up like "and in Abuja?"). Clear it with:

```bash
curl -X POST "http://127.0.0.1:8000/reset?session_id=user1"
```

## Notes

- No API keys are needed for the data sources — [Open-Meteo](https://open-meteo.com) and [open.er-api.com](https://www.exchangerate-api.com) are both free and keyless. Only the OpenAI key is required.
- The model is instructed to answer only from tool results, so it won't invent a temperature or rate when a call fails; it reports the problem instead.
- To add a new capability, write another `@tool` function in `tools.py` and add it to the `TOOLS` list — the loop in `chatbot.py` picks it up automatically.
- Memory is in-process and resets on restart. For production, back the history dict with Redis or a database.

# Task 8 — Accuracy Test Report (Chatbot Evaluation)

An evaluation harness that measures how accurately the Task 7 chatbot answers questions. It runs a suite of test cases with predefined expected answers against the live chatbot, scores every response automatically, and generates a full PDF report plus a CSV of raw results.

## How It Works

| Piece                      | Role                                                                                       |
| -------------------------- | ------------------------------------------------------------------------------------------ |
| `test_cases.json`          | 18 test cases across 6 categories, each with expected answers and machine-checkable checks |
| `run_accuracy_test.py`     | Runs each case against the Task 7 chatbot, scores it, and writes the outputs               |
| `Accuracy Test Report.pdf` | The generated report: objective, methodology, results tables, and analysis                 |
| `results.csv`              | Raw per-case results (question, expected, actual answer, pass/fail, failure reason)        |

Each case defines one or more user turns, a human-readable expected answer, and assertions the chatbot's reply must satisfy — required keywords (`contains_all` / `contains_any`), forbidden keywords, and regex patterns. A case passes only if every assertion holds. Every case runs in a fresh session, so results can't leak between tests.

| Category          | Cases | What it verifies                                                                 |
| ----------------- | ----- | -------------------------------------------------------------------------------- |
| General knowledge | 5     | Factual answers (capitals, authors, chemistry, astronomy)                        |
| Math & reasoning  | 4     | Correct arithmetic and simple logic                                              |
| Weather tool      | 3     | Live temperatures via the tool, plus graceful failure on an unknown place        |
| Currency tool     | 3     | Live conversions via the tool, plus graceful failure on an invalid currency code |
| Memory            | 2     | Multi-turn recall of facts stated earlier in the session                         |
| Robustness        | 1     | Declining a nonsensical premise instead of hallucinating                         |

Because tool-backed answers change with real-world data, those cases assert **structure** (right city, a value of the right shape from the tool, no invented numbers on failure) rather than a fixed temperature or rate — this keeps the evaluation deterministic while tolerating natural wording variation.

## Requirements

- Python 3.10+
- Everything from Task 7, plus `reportlab` for the PDF

## Setup & Usage

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Configure your API key** — same as Task 7 (`OPENAI_API_KEY` in `Task 7/.env` or exported in your shell).

**3. Run the evaluation**

```bash
cd "Task 8"
python run_accuracy_test.py
```

The script prints a PASS/FAIL line per case and an overall accuracy score, then writes `results.csv` and regenerates `Accuracy Test Report.pdf` with the results of that run.

To verify the pipeline without spending API credits, run it with simulated answers:

```bash
python run_accuracy_test.py --mock
```

## Extending the Suite

Add new cases to `test_cases.json` — the harness picks them up automatically:

```json
{
  "id": "GK-06",
  "category": "general_knowledge",
  "turns": ["What is the boiling point of water at sea level in Celsius?"],
  "expected_answer": "100°C",
  "checks": { "regex": "\\b100\\b" }
}
```

Multi-turn cases list several strings in `turns`; only the final answer is scored. Ideas for deeper evaluation: semantic-similarity scoring with the Task 5 embedding model, an LLM-as-judge pass for open-ended answers, repeating each case N times to measure consistency, and tracking latency and cost per case.

# Task 9 — Stateful Chatbot with Session History (SQLite + FastAPI)

A chatbot that **maintains context across turns** — and across server restarts. Tasks 3 and 7 keep history in an in-process dict that vanishes on restart; Task 9 makes state a first-class feature by persisting every session to SQLite and exposing endpoints to inspect, resume, and delete conversations.

## How It Works

| Piece          | Role                                                                                     |
| -------------- | ---------------------------------------------------------------------------------------- |
| `storage.py`   | SQLite session store — `sessions` and `messages` tables, created automatically on start  |
| `chatbot.py`   | LCEL chain that loads each session's history from SQLite and replays it into the prompt  |
| `main.py`      | FastAPI app: `/chat` plus session management (`/sessions`, history, delete)              |
| `demo.py`      | Scripted multi-turn conversation that proves the bot remembers earlier turns             |
| `.env.example` | Template for required environment variables                                              |

On every `/chat` call the app loads that session's transcript from SQLite, replays the most recent `HISTORY_WINDOW` messages into the prompt, gets the answer, and writes both the question and the answer back to the database. The full transcript is always stored — the window only bounds what is sent to the model, so long conversations don't blow up the prompt. Omit `session_id` and the server mints a new one and returns it; reuse it to continue the conversation, even after a restart.

## Requirements

- Python 3.10+
- pip packages: `fastapi`, `uvicorn`, `httpx`, `langchain-core`, `langchain-openai`, `python-dotenv`, `pydantic`

SQLite ships with Python — no database server or extra install needed.

## Setup

**1. Install dependencies**

```bash
cd "Task 9"
pip install -r ../requirements.txt
```

**2. Configure your API key**

```bash
cp .env.example .env
```

Then edit `.env`:

```
OPENAI_API_KEY=sk-...your actual key...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.3
HISTORY_WINDOW=20
```

| Variable             | Required | Default       | Purpose                                                  |
| -------------------- | -------- | ------------- | -------------------------------------------------------- |
| `OPENAI_API_KEY`     | Yes      | —             | Your OpenAI secret key                                   |
| `OPENAI_MODEL`       | No       | `gpt-4o-mini` | Chat model to use                                        |
| `OPENAI_TEMPERATURE` | No       | `0.3`         | Higher = more creative, lower = more focused             |
| `HISTORY_WINDOW`     | No       | `20`          | Max recent messages replayed into the prompt per session |

**3. Run the server**

```bash
uvicorn main:app --reload
```

The app starts on http://127.0.0.1:8000, with interactive docs at http://127.0.0.1:8000/docs. `sessions.db` is created next to the code on first run.

## Usage

Start a conversation (no `session_id` — the server creates one):

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "My name is Ada and I live in Lagos."}'
```

```json
{
  "answer": "Nice to meet you, Ada! ...",
  "session_id": "a1b2c3d4e5f6",
  "turns_in_session": 1
}
```

Ask a follow-up with the returned `session_id` — the bot answers from context:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is my name and where do I live?", "session_id": "a1b2c3d4e5f6"}'
```

Inspect and manage sessions:

```bash
curl http://127.0.0.1:8000/sessions                          # list all sessions with message counts
curl http://127.0.0.1:8000/sessions/a1b2c3d4e5f6/history     # full stored transcript
curl -X DELETE http://127.0.0.1:8000/sessions/a1b2c3d4e5f6   # delete a session and its history
```

## Running the Demo

With the server running, in a second terminal:

```bash
cd "Task 9"
python demo.py
```

The script runs a five-turn conversation: it tells the bot a name, city, and preference in the early turns, then asks questions that can only be answered correctly if the earlier turns were remembered. It prints each exchange and finishes with the persisted transcript size.

To prove state survives a restart, stop the server (Ctrl+C), start it again, and resume the same session:

```bash
CHATBOT_SESSION=<session id printed by the demo> python demo.py
```

The bot still knows the name and city from before the restart, because the history lives in SQLite rather than process memory.

## Notes

- Concurrent sessions are fully isolated — each `session_id` has its own transcript, so parallel users never see each other's context.
- `HISTORY_WINDOW` is a simple, predictable strategy for bounding prompt size. Natural upgrades: summarise older turns into a rolling summary, or retrieve only the most relevant past messages with the Task 5 embedding approach.
- SQLite is perfect for a single-process demo. Under real multi-instance load, swap `storage.py` for Postgres or Redis — `chatbot.py` and `main.py` only touch its functions, so nothing else changes.

# Task 10 — Document Summarization & Analysis Chain (Map-Reduce + FastAPI)

A chain that takes one or more documents and returns both a **narrative summary** and a **structured analysis** — topics, entities, key points, action items, risks, sentiment, and open questions. Give it several documents and it adds a cross-document synthesis that surfaces shared themes and, more usefully, places where the documents **contradict each other**.

Tasks 3, 7 and 9 all process a single short question per turn. Task 10 is the first chain that handles inputs larger than a context window, so it uses a map-reduce structure with a recursive collapse step rather than a single prompt.

## Workflow

![Workflow diagram](Task%2010/workflow.png)

The diagram is generated from `workflow.dot` (Graphviz). `workflow.mmd` holds the same graph in Mermaid for editing on GitHub:

```bash
cd "Task 10"
dot -Tpng -Gdpi=150 workflow.dot -o workflow.png
```

| Stage         | What happens                                                                                              |
| ------------- | --------------------------------------------------------------------------------------------------------- |
| 1. Ingest     | Extract text by file type, then split into 700-word windows with 80-word overlap                          |
| 2. Map        | One LLM call per chunk compresses it to a note; all chunks run concurrently via `abatch`                  |
| 3. Collapse   | While notes exceed `COLLAPSE_BATCH`, merge them in batches — repeats until they fit one prompt            |
| 4. Reduce     | `RunnableParallel` runs the summary and the structured analysis on the condensed text **at the same time** |
| 5. Synthesize | With more than one document, a final call compares the per-document reports                               |

Single-chunk documents skip stages 2 and 3 entirely and go straight to reduce, so short files cost exactly two LLM calls.

## How It Works

| Piece          | Role                                                                                    |
| -------------- | ----------------------------------------------------------------------------------------- |
| `loaders.py`   | Text extraction for `.pdf`, `.docx`, `.csv`, `.json`, `.txt`, `.md`, plus the chunker    |
| `models.py`    | Pydantic schemas — they define the LLM's output contract *and* the API response shape    |
| `chain.py`     | The LCEL chain: map, collapse, reduce, analyze, synthesize                               |
| `main.py`      | FastAPI app exposing `/analyze`, `/analyze/text`, and report retrieval                   |
| `demo.py`      | Runs the bundled samples through the API and prints a readable report                    |
| `samples/`     | Three related documents that deliberately disagree with each other                       |
| `.env.example` | Template for required environment variables                                              |

The analysis branch uses `model.with_structured_output(DocumentAnalysis)`, so the model returns a validated Pydantic object rather than free text that needs parsing. The same class is the FastAPI `response_model`, which means the schema is declared once and shows up automatically in `/docs`.

Both reduce branches read the *condensed* text rather than the summary, so the analysis sees the document's full detail instead of inheriting whatever the summary happened to keep.

## Requirements

- Python 3.10+
- pip packages: `fastapi`, `uvicorn`, `python-multipart`, `httpx`, `langchain-core`, `langchain-openai`, `python-dotenv`, `pydantic`, `pypdf`, `python-docx`
- Graphviz (only to re-render the diagram): `sudo apt install graphviz`

## Setup

**1. Install dependencies**

```bash
cd "Task 10"
pip install -r ../requirements.txt
```

**2. Configure your API key**

```bash
cp .env.example .env
```

Then edit `.env`:

```
OPENAI_API_KEY=sk-...your actual key...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.1
```

| Variable             | Required | Default       | Purpose                                                 |
| -------------------- | -------- | ------------- | ------------------------------------------------------- |
| `OPENAI_API_KEY`     | Yes      | —             | Your OpenAI secret key                                  |
| `OPENAI_MODEL`       | No       | `gpt-4o-mini` | Chat model to use                                       |
| `OPENAI_TEMPERATURE` | No       | `0.1`         | Kept low so summaries stay faithful to the source       |
| `MAX_CONCURRENCY`    | No       | `5`           | Parallel LLM calls, across both chunks and documents    |
| `COLLAPSE_BATCH`     | No       | `5`           | Notes merged per collapse call before re-checking       |

**3. Run the server**

```bash
uvicorn main:app --reload
```

The app starts on http://127.0.0.1:8000, with interactive docs at http://127.0.0.1:8000/docs.

## Usage

Upload one or more files:

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -F "files=@samples/incident_report.md" \
  -F "files=@samples/roadmap_meeting.txt"
```

Or send raw text with no file at all:

```bash
curl -X POST http://127.0.0.1:8000/analyze/text \
  -H "Content-Type: application/json" \
  -d '{"documents": [{"source": "note.txt", "text": "Paste any document text here..."}]}'
```

Response (trimmed):

```json
{
  "report_id": "9f2c1a7b4e02",
  "document_count": 2,
  "documents": [
    {
      "source": "incident_report.md",
      "words": 465,
      "chunks": 1,
      "summary": "INC-2481 is a SEV-2 incident report covering a 3h 14m checkout latency spike...",
      "analysis": {
        "document_type": "incident report",
        "topics": ["checkout latency", "database saturation", "release rollback"],
        "entities": [{ "name": "checkout-api", "type": "product", "mention": "the affected service" }],
        "key_points": ["p95 latency rose from 340 ms to 8.7 s across 18,400 attempts"],
        "action_items": ["Add an index on order_promotions.order_id — Chidera, due 14 March"],
        "risks": ["Staging data volume is not representative of production"],
        "sentiment": "negative",
        "sentiment_rationale": "The document reports a customer-facing outage and its causes.",
        "open_questions": ["Should schema changes on large tables require a query plan review?"]
      }
    }
  ],
  "synthesis": {
    "overview": "Both documents concern the March checkout incident...",
    "shared_themes": ["checkout latency", "staging/production parity"],
    "contradictions": [
      "The incident report assigns staging data seeding a 3 April due date, while the roadmap review defers that work to Q3."
    ],
    "combined_action_items": ["Fund checkout load tests for Q2", "Scope the PII scrubbing work by 3 April"]
  }
}
```

Retrieve a report you already generated:

```bash
curl http://127.0.0.1:8000/reports                  # list generated reports
curl http://127.0.0.1:8000/reports/9f2c1a7b4e02     # fetch one in full
```

| Endpoint                | Method | Purpose                                                       |
| ----------------------- | ------ | ------------------------------------------------------------- |
| `/`                     | GET    | Health check, active model, supported extensions              |
| `/analyze`              | POST   | Multipart upload of one or more documents                     |
| `/analyze/text`         | POST   | Same pipeline for text pasted directly into the request       |
| `/reports`              | GET    | List reports generated since startup                          |
| `/reports/{report_id}`  | GET    | Fetch a full report                                           |

## Running the Demo

With the server running, in a second terminal:

```bash
cd "Task 10"
python demo.py
```

It analyses all three bundled samples and prints each summary and analysis, then the cross-document synthesis. The samples are written to disagree: `incident_report.md` schedules staging data seeding for 3 April, `roadmap_meeting.txt` defers it to Q3, and `customer_feedback.csv` raises slow promo-code validation that the incident report never mentions and the meeting explicitly leaves out of the plan. A working synthesis step should surface all three.

Point it at your own files instead:

```bash
python demo.py ~/reports/q2-review.pdf ~/notes/standup.docx
```

## Notes

- Cost scales with chunks, not documents: an *n*-chunk document costs *n* map calls plus the collapse rounds plus 2, and short files stay at 2.
- `MAX_CONCURRENCY` bounds parallel calls at both levels — chunks within a document and documents within a request — so a 40-chunk upload won't trip provider rate limits.
- Prompts instruct the model to return empty lists rather than invent action items or risks, which is why an informational document comes back with `action_items: []` instead of filler.
- Scanned PDFs return a 415 with an explanation, since `pypdf` extracts embedded text and not images. Run OCR first if you need those.
- Reports are cached in-process and clear on restart. Persisting them is Task 9's `storage.py` pattern applied to a different table.
- The 5 MB upload cap in `main.py` is a guard, not a limit of the chain — the collapse loop handles arbitrarily long documents by design.
# Task 11 — Document Insight Agent (Tool-Calling Agent + FastAPI)

An **agent** that reads PDF and text documents and extracts structured, evidence-linked insights. Task 10 pushes every chunk of every document through a fixed chain. Task 11 inverts that: the model cannot see the documents at all and must reach them through tools, so it decides what to search for, which pages to open, and what is worth recording.

Every insight it records carries a verbatim quote and a location. The quote is checked against the source segment before the report is returned, so a hallucinated citation is caught by the code rather than trusted.

## How It Works

| Piece            | Role                                                                                    |
| ---------------- | --------------------------------------------------------------------------------------- |
| `documents.py`   | Loads PDF/txt/md into labelled segments; keyword search and quote verification           |
| `tools.py`       | The four tools the agent is bound to, closed over one workspace                          |
| `agent.py`       | The tool-calling loop, then a structured-output pass that writes the final summary       |
| `models.py`      | Pydantic schemas — the LLM's output contract and the API response shape                  |
| `main.py`        | FastAPI app exposing `/extract`, `/extract/text`, and report retrieval                   |
| `demo.py`        | Runs the bundled samples through the API and prints a readable report                    |
| `samples/`       | A 4-page PDF contract, board minutes, and a security review that disagree with each other |
| `.env.example`   | Template for required environment variables                                              |

### The agent's tools

| Tool                | What it gives the agent                                                        |
| ------------------- | ------------------------------------------------------------------------------ |
| `list_documents`    | Every document's segment labels, sizes, and a one-line preview of each segment  |
| `search_documents`  | Locations and snippets for a keyword query, ranked by term coverage             |
| `read_segments`     | The full text of up to four segments at a time                                  |
| `record_insight`    | Saves one finding with a category, quote, location, and confidence              |

PDFs are segmented by page (`p1`, `p2`, …), text and markdown into ~250-word blocks on paragraph boundaries (`s1`, `s2`, …). Labels are how the agent addresses the documents and how every insight is cited back.

### Why the loop matters

`record_insight` verifies the quote as it is stored and tells the agent when it fails: an unverified quote comes back with an instruction to re-read the segment and record it again. The agent usually fixes itself on the next turn. Whatever remains unverified stays in the response as `verified: false` rather than being silently dropped, and the report counts both.

Because the agent reads selectively, cost tracks what it chose to open rather than total document length. `stats` and `trace` in the response show exactly which tools ran and in what order, so the run is auditable after the fact.

Insights are typed: `key_fact`, `figure`, `date`, `obligation`, `risk`, `decision`, `open_question`, `contradiction`.

## Requirements

- Python 3.10+
- pip packages: `fastapi`, `uvicorn`, `python-multipart`, `httpx`, `langchain-core`, `langchain-openai`, `python-dotenv`, `pydantic`, `pypdf`, `reportlab`

`reportlab` is only needed to regenerate the sample PDF.

## Setup

**1. Install dependencies**

```bash
cd "Task 11"
pip install -r ../requirements.txt
```

**2. Configure your API key**

```bash
cp .env.example .env
```

Then edit `.env`:

```
OPENAI_API_KEY=sk-...your actual key...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.1
```

| Variable             | Required | Default       | Purpose                                            |
| -------------------- | -------- | ------------- | -------------------------------------------------- |
| `OPENAI_API_KEY`     | Yes      | —             | Your OpenAI secret key                             |
| `OPENAI_MODEL`       | No       | `gpt-4o-mini` | Chat model to use                                  |
| `OPENAI_TEMPERATURE` | No       | `0.1`         | Kept low so extractions stay faithful to the source |
| `MAX_AGENT_STEPS`    | No       | `14`          | Hard ceiling on model turns per run                |

**3. Run the server**

```bash
uvicorn main:app --reload
```

The app starts on http://127.0.0.1:8000, with interactive docs at http://127.0.0.1:8000/docs.

## Sample Documents

Three documents about the same engagement, written to disagree:

| File                   | What it is                          | Contains                                          |
| ---------------------- | ----------------------------------- | ------------------------------------------------- |
| `vendor_agreement.pdf` | 4-page master services agreement    | Fees, term, SLA, data clauses, liability cap      |
| `board_minutes.txt`    | Technology committee minutes        | Decisions, owners, dated actions, budget approval |
| `security_review.md`   | Third-party security review         | Seven findings, due dates, open questions         |

The disagreements are deliberate and checkable:

- The agreement sets fees of 8,750 GBP a month over 24 months (210,000 GBP); the minutes record the two-year cost as 180,000 GBP and skip further approval on that basis.
- Clause 4.2 requires 90 days notice to terminate; clause 11.3 in the same contract says 30 days. The minutes rely on the 30-day reading to waive a break-cost analysis.
- Clause 6.2 restricts hosting to the UK and Ireland; the security review finds a subprocessor in Frankfurt.
- The contract requires a penetration test every 12 months; the most recent one is 19 months old.

A working run should surface these as `contradiction` insights with quotes from both sides.

Regenerate the PDF after editing its source text:

```bash
cd "Task 11/samples"
python build_agreement_pdf.py
```

## Usage

Upload one or more documents:

```bash
curl -X POST http://127.0.0.1:8000/extract \
  -F "files=@samples/vendor_agreement.pdf" \
  -F "files=@samples/board_minutes.txt"
```

Steer the agent toward a particular question:

```bash
curl -X POST http://127.0.0.1:8000/extract \
  -F "files=@samples/vendor_agreement.pdf" \
  -F "focus=exit terms, notice periods, and anything that locks us in"
```

Or send raw text with no file:

```bash
curl -X POST http://127.0.0.1:8000/extract/text \
  -H "Content-Type: application/json" \
  -d '{"documents": [{"filename": "note.txt", "text": "Paste any document text here..."}]}'
```

Response (trimmed):

```json
{
  "report_id": "4c81be09a2f7",
  "focus": null,
  "documents": [
    {
      "doc_id": "doc1",
      "filename": "vendor_agreement.pdf",
      "kind": "pdf",
      "segments": 4,
      "words": 975,
      "segments_read": ["p1", "p2", "p4"]
    }
  ],
  "summary": {
    "title": "Northwind reconciliation platform engagement",
    "document_types": ["master services agreement", "committee minutes"],
    "overview": "The agreement appoints Northwind Systems for a 24-month term from 1 April 2026...",
    "entities": [
      { "name": "Northwind Systems Ltd", "type": "organization", "role": "supplier of the platform" }
    ],
    "timeline": [{ "date": "30 June 2026", "event": "Implementation completion deadline" }],
    "open_questions": ["Which notice period governs — clause 4.2 or clause 11.3?"],
    "recommended_actions": ["Resolve the conflicting notice periods before signature"]
  },
  "insights": [
    {
      "category": "contradiction",
      "statement": "The contract states two different notice periods for termination.",
      "evidence": "Either party may terminate this Agreement at any time by giving 30 days written notice",
      "doc_id": "doc1",
      "location": "p4",
      "confidence": "high",
      "verified": true
    },
    {
      "category": "figure",
      "statement": "The combined monthly charge is 8,750 GBP excluding VAT.",
      "evidence": "giving a combined monthly charge of 8,750 GBP exclusive of VAT",
      "doc_id": "doc1",
      "location": "p1",
      "confidence": "high",
      "verified": true
    }
  ],
  "insights_by_category": { "contradiction": 1, "figure": 1 },
  "stats": {
    "steps": 9,
    "tool_calls": 14,
    "tools_used": { "list_documents": 1, "search_documents": 3, "read_segments": 4, "record_insight": 6 },
    "insights_recorded": 12,
    "insights_verified": 12
  },
  "trace": ["list_documents()", "search_documents(query='termination notice', doc_id=all)"]
}
```

Retrieve a report generated earlier:

```bash
curl http://127.0.0.1:8000/reports                  # list reports
curl http://127.0.0.1:8000/reports/4c81be09a2f7     # fetch one in full
```

| Endpoint               | Method | Purpose                                                    |
| ---------------------- | ------ | ---------------------------------------------------------- |
| `/`                    | GET    | Health check, active model, supported extensions           |
| `/extract`             | POST   | Multipart upload of one or more documents, optional `focus` |
| `/extract/text`        | POST   | Same pipeline for text sent directly in the request        |
| `/reports`             | GET    | List reports generated since startup                       |
| `/reports/{report_id}` | GET    | Fetch a full report                                        |

## Running the Demo

With the server running, in a second terminal:

```bash
cd "Task 11"
python demo.py
```

It sends all three samples, prints every insight with its quote and citation, then the entity list, timeline, open questions, and the agent's full tool trace. Insights whose quotes failed verification are marked inline.

Give it a focus, or point it at your own files:

```bash
AGENT_FOCUS="financial exposure and exit terms" python demo.py
python demo.py ~/contracts/lease.pdf ~/notes/handover.md
```

## Notes

- Quote verification normalises whitespace and case before matching, so PDF line wrapping doesn't cause false negatives. It is a substring check, not a similarity score: a paraphrase fails, which is the intent.
- `MAX_AGENT_STEPS` bounds the loop. If the agent hits the ceiling, whatever it recorded is still returned, and `stats.steps` shows it stopped early.
- `search_documents` is keyword-based on purpose. It keeps the agent cheap and dependency-free; swapping in the Task 5 embedding search would be a change to one method on `Workspace`.
- The agent reads at most four segments per call, which keeps any one tool result small enough to leave room for the rest of the conversation.
- Scanned PDFs raise a 415 with an explanation, since `pypdf` reads embedded text and not images. Run OCR first.
- Reports are cached in-process and clear on restart, same as Task 10.

# Task 12 — Chatbot REST API (JSON Envelope + Local Deployment)

A REST API that wraps a stateful chatbot and returns the **same JSON shape on every response** — successes, validation failures, rate limits, and upstream errors alike. Tasks 3, 7, and 9 expose a chatbot over HTTP; Task 12 is about the wrapper itself: one response contract, typed errors, request tracing, rate limiting, metrics, tests, and a local deployment that runs with or without an OpenAI key.

## The Response Contract

Every JSON response has four top-level keys, always present:

```json
{
  "success": true,
  "data": { "reply": "...", "session_id": "a1b2c3d4e5f6", "turn": 3, "model": "gpt-4o-mini",
            "usage": { "prompt_tokens": 412, "completion_tokens": 88, "total_tokens": 500 } },
  "error": null,
  "meta": { "request_id": "9f2c1a7b4e02d8c1", "timestamp": "2026-03-14T09:12:44.318+00:00",
            "duration_ms": 812.4, "version": "1.0.0" }
}
```

Failures fill `error` and null out `data`:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "validation_error",
    "message": "The request body failed validation.",
    "details": [{ "field": "message", "problem": "String should have at least 1 character" }]
  },
  "meta": { "request_id": "3ab7...", "timestamp": "...", "duration_ms": 1.4, "version": "1.0.0" }
}
```

A client parses one shape and branches on `success`. `error.code` is the stable value to branch on; `error.message` is for humans and may be reworded.

| Code                | HTTP | Meaning                                        |
| ------------------- | ---- | ---------------------------------------------- |
| `validation_error`  | 422  | Body failed schema validation; see `details`   |
| `missing_api_key`   | 401  | `X-API-Key` header absent while keys are set   |
| `invalid_api_key`   | 401  | Key not recognised                             |
| `rate_limited`      | 429  | Per-minute limit reached; `Retry-After` is set |
| `session_not_found` | 404  | No such session                                |
| `not_found`         | 404  | No such route                                  |
| `upstream_error`    | 502  | The model call failed or timed out             |
| `internal_error`    | 500  | Unexpected server error                        |

## How It Works

| Piece            | Role                                                                                 |
| ---------------- | ------------------------------------------------------------------------------------- |
| `config.py`      | Every setting read from the environment in one place                                 |
| `schemas.py`     | `Envelope[T]` plus the request and data models it wraps                              |
| `runtime.py`     | Request IDs, timing, JSON logging, API-key auth, rate limiting, metrics              |
| `chatbot.py`     | The wrapped engine — LangChain chain, SQLite-backed history, streaming, mock mode    |
| `storage.py`     | SQLite session store, created on start                                               |
| `main.py`        | Routes and the exception handlers that put every error into the envelope             |
| `client.py`      | Demo client: a multi-turn conversation, a streamed reply, and an error response      |
| `tests/`         | pytest suite covering the contract, run entirely in mock mode                        |
| `Dockerfile`     | Container image with a health check                                                  |
| `run.sh`         | One-command local start                                                              |

`Envelope[T]` is a generic Pydantic model, so `Envelope[ChatData]` is the declared `response_model` on `/v1/chat` and the full envelope shows up in `/docs` with the right `data` type rather than a loose object.

Errors reach the envelope through exception handlers rather than try/except in each route. `APIError` carries an HTTP status and a stable code; FastAPI's validation errors are reshaped into per-field entries; anything unhandled becomes `internal_error`, with the underlying message shown only when `DEBUG=1`.

`ContextMiddleware` assigns a request ID (or reuses an inbound `X-Request-ID`), times the request, records it in the metrics counters, sets `X-Request-ID` and `X-Response-Time-Ms` on the response, and writes one JSON log line per request. The same ID appears in `meta.request_id`, so a user-reported response can be found in the logs directly.

Rate limiting is a fixed window per minute, keyed by API key when keys are configured and by client IP otherwise. When keys are not configured the API is open, which is the sensible local default.

## Endpoints

| Endpoint                    | Method | Auth | Purpose                                       |
| --------------------------- | ------ | ---- | --------------------------------------------- |
| `/healthz`                  | GET    | No   | Liveness, version, active model, session count |
| `/v1/chat`                  | POST   | Yes  | Send a message, get a reply                   |
| `/v1/chat/stream`           | POST   | Yes  | Same, streamed as NDJSON                      |
| `/v1/sessions`              | GET    | Yes  | List sessions with message counts             |
| `/v1/sessions/{id}`         | GET    | Yes  | Full stored transcript                        |
| `/v1/sessions/{id}`         | DELETE | Yes  | Delete a session and its history              |
| `/v1/metrics`               | GET    | Yes  | Request counts, error counts, latency, tokens |

`/healthz` is deliberately unauthenticated so container and uptime checks work without a credential.

## Requirements

- Python 3.10+
- pip packages: `fastapi`, `uvicorn`, `httpx`, `langchain-core`, `langchain-openai`, `python-dotenv`, `pydantic`, `pytest`, `pytest-asyncio`
- Docker (optional, for the container route)

SQLite ships with Python — no database server needed.

## Deploying Locally

**Option A — one command**

```bash
cd "Task 12"
./run.sh
```

It copies `.env.example` to `.env` on first run, installs anything missing, and starts uvicorn on http://127.0.0.1:8000. Docs at `/docs`, health at `/healthz`.

**Option B — no API key**

Mock mode returns deterministic canned replies through the whole stack, so you can exercise the API, the envelope, streaming, and the tests without spending anything:

```bash
MOCK=1 ./run.sh
```

**Option C — Docker**

```bash
cd "Task 12"
cp .env.example .env        # add your key, or set MOCK=1
docker compose up --build
```

The compose file mounts a named volume at `/data` so `chatbot.db` survives container rebuilds, and the image ships a `HEALTHCHECK` that polls `/healthz`.

**Option D — manual**

```bash
cd "Task 12"
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

## Configuration

| Variable                | Default        | Purpose                                                     |
| ----------------------- | -------------- | ----------------------------------------------------------- |
| `OPENAI_API_KEY`        | —              | Required unless `MOCK=1`                                    |
| `OPENAI_MODEL`          | `gpt-4o-mini`  | Chat model to use                                           |
| `OPENAI_TEMPERATURE`    | `0.3`          | Higher = more creative, lower = more focused                |
| `MOCK`                  | `0`            | `1` serves canned replies with no upstream calls            |
| `DEBUG`                 | `0`            | `1` returns the real message on `internal_error`            |
| `HISTORY_WINDOW`        | `20`           | Recent messages replayed into the prompt per session        |
| `REQUEST_TIMEOUT`       | `60`           | Seconds before an upstream call becomes `upstream_error`    |
| `MAX_MESSAGE_CHARS`     | `4000`         | Longer messages are rejected as `validation_error`          |
| `API_KEYS`              | empty          | Comma-separated keys; empty disables auth                   |
| `RATE_LIMIT_PER_MINUTE` | `30`           | Per key or per IP; `0` disables                             |
| `CORS_ORIGINS`          | `*`            | Comma-separated allowed origins                             |
| `DB_PATH`               | `chatbot.db`   | SQLite file location                                        |
| `HOST` / `PORT`         | `127.0.0.1` / `8000` | Bind address used by `run.sh`                         |

## Usage

Start a conversation (omit `session_id` and the server mints one):

```bash
curl -X POST http://127.0.0.1:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "My name is Ada and I work in Lagos."}'
```

Continue it with the returned `session_id`:

```bash
curl -X POST http://127.0.0.1:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my name?", "session_id": "a1b2c3d4e5f6"}'
```

With auth enabled, add the header:

```bash
curl -X POST http://127.0.0.1:8000/v1/chat \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

Stream a reply. This is the one endpoint that isn't enveloped — it emits NDJSON, one JSON object per line, so a client can render tokens as they arrive:

```bash
curl -N -X POST http://127.0.0.1:8000/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain REST in two sentences."}'
```

```
{"type": "start", "session_id": "a1b2c3d4e5f6", "request_id": "9f2c1a7b4e02d8c1"}
{"type": "token", "text": "REST "}
{"type": "token", "text": "is "}
{"type": "end", "session_id": "a1b2c3d4e5f6", "turn": 4}
```

Manage sessions and check the counters:

```bash
curl http://127.0.0.1:8000/v1/sessions
curl http://127.0.0.1:8000/v1/sessions/a1b2c3d4e5f6
curl -X DELETE http://127.0.0.1:8000/v1/sessions/a1b2c3d4e5f6
curl http://127.0.0.1:8000/v1/metrics
```

## Running the Demo Client

With the server running, in a second terminal:

```bash
cd "Task 12"
python client.py
```

It runs a three-turn conversation, streams a fourth reply token by token, deliberately sends an invalid request to show the error envelope, then prints the stored transcript size and the server metrics. Set `API_KEY` if auth is enabled, or `API_URL` to point at a different host.

## Tests

```bash
cd "Task 12"
pytest -q
```

Eleven tests run against `TestClient` in mock mode, so they need no API key and make no network calls. They cover the envelope shape on every response, session continuity across turns, each error code, the rate limit and its `Retry-After` header, request-ID echo, NDJSON streaming, and API-key enforcement.

## Notes

- Mock mode is what makes the suite cheap and deterministic. It sits at the boundary of `chatbot.py`, so everything above it — routing, validation, auth, rate limiting, storage, the envelope — is the same code in both modes.
- The rate limiter and metrics live in process memory. Behind more than one worker each process would count separately; Redis is the usual replacement, and only `runtime.py` changes.
- SQLite with the default settings is fine for a single-process deployment. Under real concurrent load, move `storage.py` to Postgres — nothing else touches the database.
- The streaming endpoint stores the full reply only after the stream closes, so a client that disconnects mid-stream leaves nothing half-written in the transcript.
- `API_KEYS` empty means open, which is right for local work and wrong for anything exposed. Set it before binding to `0.0.0.0`.
- Token counts come from the provider's usage metadata when available and fall back to a character estimate otherwise, so treat `usage` in mock mode as indicative only.