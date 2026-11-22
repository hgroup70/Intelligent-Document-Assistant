# Intelligent Document Assistant

A Streamlit app for summarizing PDF and text documents and asking questions about them. Answers are generated only from the uploaded documents, and each answer shows the passages (and page numbers) it was based on.

It works with either OpenAI or Google Gemini, and uses LangChain + FAISS for retrieval.

## Features

- Upload PDF, TXT or Markdown files (drag and drop, several at once)
- Document list with name, size, page/word/character count and upload date; switch between documents or delete them
- Summaries in three lengths (short, medium, detailed): overview, key points, main ideas and conclusions
- Long documents are summarized section by section and then combined
- Download summaries as Markdown or PDF
- Chat with a document, or with all uploaded documents at once
- Citations under every answer with the matching excerpts and page numbers
- Follow-up questions use the previous messages in the conversation
- Conversations are saved per document and can be reopened or exported (Markdown / JSON)
- Switch between OpenAI and Gemini in the sidebar; model, temperature and number of retrieved chunks are adjustable
- Each browser session has its own workspace; optional login with username/password
- Error messages for unsupported or oversized files, scanned or password-protected PDFs, bad API keys, rate limits, etc.
- Example questions, plus generated questions specific to the document
- Search inside the extracted text

## Setup

Requires Python 3.10 or newer.

```bash
git clone <repo-url> doc-assistant
cd doc-assistant

python -m venv .venv
source .venv/bin/activate      # on Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
```

Then put at least one API key in `.env`:

```
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
DEFAULT_PROVIDER=openai
```

If you don't want to store a key in `.env`, you can also paste it in the Settings section of the sidebar. In that case it's only kept for the current session.

## Running

```bash
streamlit run app.py
```

The app opens at http://localhost:8501. There's a small example document in `samples/` if you want to try it quickly.

Tests:

```bash
pytest
```

The tests don't call any API. The end-to-end pipeline test uses fake embeddings and a fake model, and is skipped if LangChain/FAISS aren't installed.

With Docker:

```bash
docker build -t doc-assistant .
docker run -p 8501:8501 --env-file .env -v "$(pwd)/data:/app/data" doc-assistant
```

## Getting API keys

OpenAI: create a key at https://platform.openai.com/api-keys. The API needs billing or credits set up, which is separate from a ChatGPT subscription.

Gemini: create a key in Google AI Studio at https://aistudio.google.com/app/apikey. There is a free tier with rate limits.

Default models are `gpt-4o-mini` / `text-embedding-3-small` for OpenAI and `gemini-2.5-flash` / `gemini-embedding-001` for Gemini. They can be changed in `.env`.

## How it works

**Upload.** The file is checked (type, size, page count), and the text is extracted page by page with pdfplumber, with pypdf as a fallback. Text files are decoded as UTF-8, falling back to cp1252/latin-1. The extracted pages are saved as JSON in the user's workspace.

**Indexing.** Pages are split into chunks of about 1000 characters with 150 characters of overlap (`RecursiveCharacterTextSplitter`). Each chunk keeps its document id, name and page number. The chunks are embedded and stored in a local FAISS index. There is one index per document and embedding model, so switching from OpenAI to Gemini builds a second index instead of mixing embeddings.

**Questions.** If there is chat history, the question is first rewritten into a standalone question, so that something like "why?" still retrieves the right chunks. The top-k chunks are retrieved, numbered and put into the prompt. The model is told to answer only from them and to cite them as [1], [2], and so on. The last few turns of the conversation are included as memory. The answer is streamed, and the cited chunks are listed under it.

**Summaries.** Documents up to about 60k characters are sent in one request. Longer ones are split into sections (at most 40), and notes are written for each section, four requests at a time. The notes are then combined into the final summary. Summaries are cached per length.

**Storage.** Everything is stored under `data/workspaces/<workspace-id>/`:

```
documents.json
docs/<doc_id>/pages.json, summaries.json, questions.json
indexes/<doc_id>/<provider>__<embedding-model>/
conversations/<scope>/<conversation-id>.json
```

Without login, the workspace id is random and is also put in the URL (`?ws=...`) so that refreshing the page doesn't lose your documents. Anonymous workspaces that haven't been used for 7 days are deleted on startup. With `AUTH_ENABLED=true`, users sign in with the accounts in `APP_USERS` and each user keeps a fixed workspace. This login is fine for a small team or a demo. For a public deployment, put the app behind a proper auth proxy.

## Project structure

```
app.py                  entry point
src/core/               logic, no Streamlit imports
    config.py           settings from .env
    document_processor.py
    storage.py          workspaces, documents, conversations
    llm_provider.py     OpenAI / Gemini clients, error messages
    vector_store.py     chunking and FAISS indexes
    prompts.py
    summarizer.py
    qa_engine.py
    export.py           Markdown / JSON / PDF export
    auth.py
    service.py          used by the UI
src/ui/                 Streamlit pages and components
tests/
samples/
```

## Configuration

All options are listed in `.env.example`. The main ones:

| Variable | Default | |
|---|---|---|
| `DEFAULT_PROVIDER` | `openai` | `openai` or `gemini` |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | |
| `GEMINI_CHAT_MODEL` | `gemini-2.5-flash` | |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `1000` / `150` | in characters |
| `RETRIEVAL_K` | `5` | chunks per answer |
| `MAX_HISTORY_TURNS` | `6` | previous Q&A pairs sent as context |
| `MAX_FILE_SIZE_MB` | `50` | also change `maxUploadSize` in `.streamlit/config.toml` |
| `MAX_PAGES` | `500` | per PDF |
| `MAX_DOCUMENTS` | `25` | per workspace |
| `AUTH_ENABLED` | `false` | |
| `APP_USERS` | | `alice:password,bob:sha256:<hex>` |

## Known limitations

- Scanned PDFs without a text layer can't be read. Run them through OCR first, for example `ocrmypdf in.pdf out.pdf`.
- Tables and multi-column layouts are extracted as plain text, so some structure is lost.
- FAISS indexes are loaded with `allow_dangerous_deserialization=True`. That's fine because the app only loads indexes it created itself, but don't put files from elsewhere into `data/`.

## License

MIT
