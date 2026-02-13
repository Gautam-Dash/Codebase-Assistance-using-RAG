# Installation & Setup Guide

Comprehensive setup instructions for the Codebase RAG System.

## System Requirements

- **Python**: 3.10 or higher
- **RAM**: 8GB minimum (16GB recommended for large codebases)
- **Disk Space**: 5-20GB depending on codebase size
- **OS**: Windows, macOS, Linux
- **Git**: Required for commit context features

## Step-by-Step Installation

### 1. Clone and Navigate

```bash
cd c:\Users\user\Documents\RAG
```

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

This installs:
- `fastapi` & `uvicorn`: REST API framework
- `streamlit`: Web UI framework
- `langchain`: LLM integration
- `faiss-cpu`: Vector search library
- `sentence-transformers`: Embedding models
- `torch`: Deep learning framework
- `transformers`: NLP models
- `gitpython`: Git repository analysis
- `pydantic`: Configuration management
- And other supporting packages

### 4. Setup Configuration

```bash
# Copy example environment file
copy .env.example .env

# Edit .env with your settings
notepad .env
```

**Required settings:**

```env
# API Key for LLM features (required for query expansion)
OPENAI_API_KEY=your_api_key_here

# Path to repository you want to index (adjust path)
REPO_PATH=./repo_to_index

# Data path for FAISS index
FAISS_INDEX_PATH=./data/faiss_index
```

**Optional settings:**

```env
# Performance tuning
CHUNK_SIZE=512          # Size of code chunks
CHUNK_OVERLAP=50        # Overlap between chunks
MAX_WORKERS=4           # Parallel processing threads
BATCH_SIZE=32           # Embedding batch size

# Search parameters
TOP_K_RETRIEVAL=10      # Initial results before re-ranking
TOP_K_RANKING=5         # Final results after re-ranking
RERANKER_THRESHOLD=0.5  # Minimum score threshold

# Models
EMBEDDING_MODEL=text-embedding-3-small
RERANKER_MODEL=cross-encoder/mmarco-mMiniLMv2-L12-H384-v1

# File handling
INCLUDE_EXTENSIONS=.py,.js,.ts,.java,.cpp,.c,.go,.rs,.rb,.php
EXCLUDE_PATTERNS=__pycache__,node_modules,.git,.env
```

### 5. Get OpenAI API Key

If using LLM features (query expansion):

1. Visit https://platform.openai.com/api-keys
2. Create new API key
3. Add to `.env`: `OPENAI_API_KEY=sk-...`

Note: Query expansion is optional; basic search works without it.

### 6. Prepare Repository

Create the directory for your codebase:

```bash
mkdir repo_to_index
# Copy your codebase here, or update REPO_PATH in .env
```

Or use an existing repository:

```bash
# Update REPO_PATH in .env to point to your repo
REPO_PATH=C:\Users\user\Documents\my-project
```

## Verification

### Test Installation

```bash
# Check Python
python --version

# Check imports
python -c "import faiss; import streamlit; import sentence_transformers; print('✓ All imports successful')"

# Check configuration
python -m cli config --list

# Check system status
python -m cli status
```

### Build Index

```bash
# Index the repository
python -m cli init

# This will:
# - Scan repository for code files
# - Parse with AST analysis
# - Generate embeddings
# - Build FAISS index (5-15 min for 10k files)
```

### Verify Search Works

```bash
# Try a simple search
python -m cli search "function definition"

# Should return relevant code chunks
```

## Configuration Tips

### For Development (Small Repos)

```env
CHUNK_SIZE=512
TOP_K_RETRIEVAL=20
TOP_K_RANKING=10
RERANKER_THRESHOLD=0.3
```

### For Production (Large Codebases)

```env
CHUNK_SIZE=256
MAX_WORKERS=8
BATCH_SIZE=64
TOP_K_RETRIEVAL=50
TOP_K_RANKING=5
RERANKER_THRESHOLD=0.6
```

### For Memory-Constrained Systems

```env
CHUNK_SIZE=256
BATCH_SIZE=16
MAX_WORKERS=2
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### For Maximum Quality

```env
CHUNK_SIZE=1024
TOP_K_RETRIEVAL=100
TOP_K_RANKING=10
RERANKER_THRESHOLD=0.3
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
```

## Common Installation Issues

### Issue: "No module named 'torch'"
**Solution:**
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Issue: "FAISS not found"
**Solution:**
```bash
pip install faiss-cpu
# Or for GPU:
pip install faiss-gpu
```

### Issue: "OpenAI API key not found"
**Solution:**
1. Add to `.env`: `OPENAI_API_KEY=your_key`
2. Note: Key is only needed for query expansion
3. Basic search works without it

### Issue: "Permission denied" on Windows
**Solution:**
```bash
# Run as Administrator or use:
python -m venv venv
.\venv\Scripts\activate.bat
```

### Issue: "Module not found" errors
**Solution:**
```bash
# Ensure venv is activated
# Reinstall requirements
pip install --upgrade -r requirements.txt
```

## Performance Optimization

### Faster Indexing

```python
# In .env
BATCH_SIZE=64
MAX_WORKERS=8
```

### Faster Searches

```python
# In .env
TOP_K_RETRIEVAL=20  # Don't retrieve too many
CHUNK_SIZE=256      # Smaller chunks = faster search
```

### Lower Memory Usage

```python
# In .env
CHUNK_SIZE=256
BATCH_SIZE=16
MAX_WORKERS=2
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Running the System

### 1. Index Your Code

```bash
python -m cli init --repo-path /path/to/repo
```

### 2. Start Searching

**CLI:**
```bash
python -m cli interactive
```

**UI:**
```bash
streamlit run src/ui/app.py
```

**Python API:**
```python
from src.rag_system import RAGSystem
rag = RAGSystem()
rag.load_existing_index()
results = rag.search("your query")
```

## Upgrading

### Update Dependencies

```bash
pip install --upgrade -r requirements.txt
```

### Update Models

Models download automatically on first use. To manually update:

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
# Downloads latest version

from transformers import AutoModel
model = AutoModel.from_pretrained('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1')
# Downloads latest cross-encoder
```

## Next Steps

1. **Read Quick Start**: See [QUICKSTART.md](QUICKSTART.md)
2. **Read Full Docs**: See [README.md](README.md)
3. **Try Examples**: See [examples/](examples/)
4. **Run UI**: `streamlit run src/ui/app.py`

## Support

For installation issues:

1. Check this guide's troubleshooting section
2. Verify all prerequisites are installed
3. Check Python version: `python --version` (should be 3.10+)
4. Verify venv is activated
5. Check .env configuration

---

**Ready to index your codebase?**

```bash
python -m cli init
```
