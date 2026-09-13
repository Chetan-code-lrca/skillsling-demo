# SkillSling AI

SkillSling is a Streamlit-based study assistant designed to run with local models through Ollama. It supports multilingual tutoring, subject-specific prompting, basic fact lookup for a small set of topics, and optional PDF-based question answering.

## What it does

- Chats with a locally running Ollama model
- Supports English, Hindi, Hinglish, Tamil, and Telugu prompts
- Adjusts prompts for General, English, Social Science, Mathematics, and Science study
- Uses simple built-in handling for a few historical facts
- Can use SymPy for basic mathematics input such as integration
- Accepts a PDF and builds a local FAISS vector store from its contents for retrieval
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

1. Extracts its text with `PyPDFLoader`.
2. Splits the document into smaller chunks.
3. Creates embeddings using the selected Ollama model.
4. Stores those embeddings in a local FAISS vector store for the current Streamlit session.

The PDF is used as local study material; the repository does not upload it to a hosted service.

Because the embedding step also uses Ollama, the selected model must be available on the same machine running the app.

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
