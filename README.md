# SkillSling AI

SkillSling is a Streamlit-based study assistant designed to run with local models through Ollama. It supports multilingual tutoring, subject-specific prompting, basic fact lookup for a small set of topics, and optional PDF-based question answering.

## What it does

- Chats with a locally running Ollama model
- Supports English, Hindi, Hinglish, Tamil, and Telugu prompts
- Adjusts prompts for General, English, Social Science, Mathematics, and Science study
- Uses simple built-in handling for a few historical facts
- Can use SymPy for basic mathematics input such as integration
- Accepts a bounded PDF upload, extracts selectable text locally, and retrieves relevant excerpts from a local FAISS index when you ask questions
- Keeps the chat session in Streamlit session state

## Running it

The application expects **Ollama** to be installed and running locally. The model selector in the app includes:

```text
llama3.2:3b
llama3.1:8b
qwen2.5:7b-instruct
qwen2.5:7b-instruct-q4_K_M
phi3:mini
```

Pull at least one model before starting the app. For example:

```bash
ollama pull llama3.2:3b
```

Create a Python virtual environment and install the project's dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then start Streamlit:

```bash
streamlit run app.py
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Choosing a model

The available models are selectable from the sidebar. A subject can also change the recommended model automatically, but the final model selection remains under your control.

You do not need every model installed. Pull only the model you intend to use. For example:

```bash
ollama pull qwen2.5:7b-instruct
```

If Streamlit reports that Ollama is unavailable, start the Ollama service and make sure the selected model has already been pulled.

## PDF study material

The sidebar accepts PDF notes. When a PDF is uploaded, the app:

1. Checks that it is a PDF and enforces a 10 MiB upload limit.
2. Rejects password-protected files and PDFs above 100 pages.
3. Extracts up to 50,000 characters of selectable text. Scanned/image-only PDFs are not OCR-processed.
4. Splits extracted page text into chunks and builds a local FAISS vector index.
5. Retrieves up to four relevant excerpts for each chat question and supplies those excerpts to the local Ollama model as reference context.

The PDF bytes are parsed in the Streamlit process. The app does not send the file or extracted text to a hosted document-processing service. The vector index exists only in the active Streamlit session and is not saved as a persistent user library.

Because both embeddings and chat use Ollama, the selected model must be available to the Ollama server running on the same machine. A different model selection rebuilds the PDF index; removing the uploaded file clears the active index.

## PDF handling limits

The Streamlit upload limit is configured in `.streamlit/config.toml`. The Python extractor independently checks the byte size and PDF structure before parsing. These limits help bound memory and processing work, but do not provide malware scanning or safe handling guarantees for untrusted PDFs. Use only files you are permitted to process, and keep the app bound to a trusted local environment.

Run the PDF ingestion tests with:

```bash
python -m unittest discover -s tests -v
```

GitHub Actions runs these tests alongside the Python syntax check.

## Project dependencies

The main libraries are:

- Streamlit
- Ollama Python client
- LangChain community integrations
- LangChain Ollama integration
- FAISS
- PyPDF
- SymPy

These are defined in `requirements.txt`.

## Current limitations

This is a local prototype rather than a hosted tutoring service. Model quality, response speed, and PDF retrieval quality depend on the Ollama model and the machine running it.

The built-in fact database is intentionally small, and the mathematical parsing path is limited to the patterns the application currently recognizes.
