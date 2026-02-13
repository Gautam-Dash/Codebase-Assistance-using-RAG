# Quick Start Guide

Get up and running with the RAG System in 5 minutes.

## 1. Install Dependencies

```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## 2. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit .env file and add your settings:
# - OPENAI_API_KEY (required for query expansion)
# - REPO_PATH (path to codebase you want to index)
```

## 3. Index Your Codebase

```bash
# Index a repository
python -m cli init --repo-path /path/to/your/repo

# Or use the configured REPO_PATH from .env
python -m cli init
```

This will:
- ✓ Scan your repository for code files
- ✓ Parse code structure using AST analysis
- ✓ Generate embeddings for each code chunk
- ✓ Build and save FAISS index for fast retrieval

**Typical time for 10k files:** 5-15 minutes

## 4. Search Your Code

### Option A: CLI Search

```bash
python -m cli search "authentication middleware"
python -m cli search "error handling" --top-k 10
```

### Option B: Interactive Mode

```bash
python -m cli interactive

# Type queries and get results
>>> database connection pooling
>>> REST API implementation
>>> quit
```

### Option C: Streamlit UI (Recommended)

```bash
streamlit run src/ui/app.py
```

Then open http://localhost:8501 in your browser.

## 5. Check System Status

```bash
# View system status
python -m cli status

# View all configuration
python -m cli config --list
```

## Common Tasks

### Search Without Query Expansion
```bash
python -m cli search "your query" --no-expansion
```

### Get More Results
```bash
python -m cli search "your query" --top-k 20
```

### Disable Git Context
```bash
python -m cli search "your query" --no-context
```

## Using in Python Code

```python
from src.rag_system import RAGSystem

# Initialize
rag = RAGSystem()
rag.load_existing_index()

# Search
results = rag.search("authentication", top_k=5)

# Process results
for result in results:
    chunk = result.ranked_result.result.chunk
    score = result.ranked_result.final_score
    print(f"{chunk.file_path}: {score:.3f}")
    print(chunk.content[:200])
```

## Troubleshooting

### "Index not found" Error
```bash
# Rebuild the index
python -m cli init
```

### "OpenAI API key not set"
- Make sure OPENAI_API_KEY is set in .env
- Query expansion is optional; search works without it

### Poor Search Results
1. Try with more retrieval candidates: `--top-k 20`
2. Lower the re-ranking threshold in .env
3. Check REPO_PATH points to correct repository

### Out of Memory
- Reduce CHUNK_SIZE in .env
- Use smaller embedding model
- Index fewer files

## Next Steps

- Read the [full documentation](README.md)
- Explore [examples](examples/)
- Check [source code](src/) for advanced usage
- Contribute improvements on GitHub

## Need Help?

1. Check README.md for detailed documentation
2. Review example scripts in `examples/`
3. Check inline code documentation
4. See troubleshooting section in README

---

Happy searching! 🔍
