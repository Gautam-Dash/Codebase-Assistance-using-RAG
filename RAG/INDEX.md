# RAG System - Complete Index

Welcome to the Codebase RAG System! This file helps you navigate the project.

## 📖 Start Here

### For First-Time Users
1. **Read**: [QUICKSTART.md](QUICKSTART.md) (5 minutes)
2. **Install**: [INSTALLATION.md](INSTALLATION.md) (detailed setup)
3. **Use**: Follow the quick start instructions

### For Detailed Understanding
1. **Overview**: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
2. **Complete Docs**: [README.md](README.md)
3. **Completion Report**: [PROJECT_COMPLETION.md](PROJECT_COMPLETION.md)

## 📁 Project Structure

```
RAG/
├── Documentation
│   ├── README.md                          # Complete feature documentation
│   ├── QUICKSTART.md                      # 5-minute setup guide
│   ├── INSTALLATION.md                    # Detailed installation
│   ├── PROJECT_SUMMARY.md                 # Architecture overview
│   ├── PROJECT_COMPLETION.md              # Completion report
│   └── INDEX.md (this file)              # Navigation guide
│
├── Source Code (~1,700 lines)
│   └── src/
│       ├── rag_system.py                  # Main orchestrator
│       ├── config.py                      # Configuration
│       ├── ingestion/
│       │   └── code_ingestion.py          # AST parsing & chunking
│       ├── retrieval/
│       │   └── semantic_retriever.py      # FAISS search
│       ├── query_expansion/
│       │   └── llm_expander.py            # LLM query expansion
│       ├── ranking/
│       │   └── cross_encoder.py           # Re-ranking
│       ├── context/
│       │   └── git_context.py             # Git integration
│       ├── ui/
│       │   └── app.py                     # Streamlit UI
│       └── utils/
│           ├── logger.py                  # Logging
│           └── models.py                  # Data models
│
├── Interface
│   └── cli.py                             # Command-line interface
│
├── Configuration
│   ├── requirements.txt                   # Python dependencies
│   ├── .env.example                       # Config template
│   └── .gitignore                         # Git ignore rules
│
├── Examples
│   ├── example_build_and_search.py        # Build & search demo
│   └── example_advanced_search.py         # Advanced features demo
│
├── Testing
│   └── tests/
│       └── test_components.py             # Unit tests
│
└── Data (created at runtime)
    └── data/
        └── faiss_index/                   # Vector search index
```

## 🚀 Quick Navigation

### "How do I...?"

#### Get Started Quickly?
→ [QUICKSTART.md](QUICKSTART.md)

#### Install Everything?
→ [INSTALLATION.md](INSTALLATION.md)

#### Understand the Architecture?
→ [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

#### Learn All Features?
→ [README.md](README.md)

#### See What Was Built?
→ [PROJECT_COMPLETION.md](PROJECT_COMPLETION.md)

#### Use from Python?
→ Look at `examples/example_*.py`

#### Use from Command Line?
```bash
python -m cli --help
python -m cli search "your query"
python -m cli interactive
```

#### Use the Web UI?
```bash
streamlit run src/ui/app.py
```

## 📚 Documentation Map

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [QUICKSTART.md](QUICKSTART.md) | Get running in 5 min | 5 min |
| [INSTALLATION.md](INSTALLATION.md) | Detailed setup guide | 15 min |
| [README.md](README.md) | Complete documentation | 30 min |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Architecture overview | 20 min |
| [PROJECT_COMPLETION.md](PROJECT_COMPLETION.md) | What was built | 10 min |

## 🎯 Core Concepts

### The RAG Pipeline

```
Query
  ↓
[1. Query Expansion] (optional LLM expansion)
  ↓
[2. Semantic Retrieval] (FAISS vector search)
  ↓
[3. Cross-Encoder Re-ranking] (precise scoring)
  ↓
[4. Context Enrichment] (git history)
  ↓
Results with explanations
```

### Main Components

1. **Ingestion** (`src/ingestion/`)
   - Parses code using AST
   - Extracts functions, classes
   - Creates chunks with metadata

2. **Retrieval** (`src/retrieval/`)
   - Builds FAISS index
   - Performs vector search
   - Manages embeddings

3. **Expansion** (`src/query_expansion/`)
   - Rewrites queries with LLM
   - Multiple strategies
   - Improves recall

4. **Ranking** (`src/ranking/`)
   - Scores results with cross-encoder
   - Normalizes scores
   - Diversifies results

5. **Context** (`src/context/`)
   - Analyzes git history
   - Shows commit info
   - Detects related files

6. **UI** (`src/ui/`)
   - Streamlit web interface
   - Interactive search
   - Visualizations

## 💻 Command Reference

### Indexing
```bash
python -m cli init                    # Build index from repo
python -m cli init --repo-path /path  # Index specific path
```

### Searching
```bash
python -m cli search "query"          # Search from CLI
python -m cli search "query" --top-k 10  # More results
python -m cli search "query" --no-expansion  # Skip LLM
```

### Interactive
```bash
python -m cli interactive             # Start interactive mode
```

### Web UI
```bash
streamlit run src/ui/app.py          # Start web interface
```

### System
```bash
python -m cli status                 # Check system status
python -m cli config --list          # Show configuration
```

## 🔧 Configuration Guide

Key settings in `.env`:

```env
OPENAI_API_KEY=sk-...                # For query expansion
REPO_PATH=./repo_to_index            # Codebase to index
CHUNK_SIZE=512                       # Code chunk size
TOP_K_RETRIEVAL=10                   # Initial results
TOP_K_RANKING=5                      # Final results
RERANKER_THRESHOLD=0.5               # Quality gate
```

See `.env.example` for all options.

## 🧪 Examples

### Python API
```python
from src.rag_system import RAGSystem

rag = RAGSystem()
rag.load_existing_index()
results = rag.search("authentication", top_k=5)
```

### Run Examples
```bash
python examples/example_build_and_search.py
python examples/example_advanced_search.py
```

### Run Tests
```bash
pytest tests/
```

## 📊 Project Statistics

- **Total Code**: ~1,700 lines of Python
- **Documentation**: 2,000+ lines
- **Modules**: 7 core modules
- **Languages Supported**: 9 programming languages
- **Features**: 15+ major features

## 🎓 Learning Path

1. **Beginner**: Start with [QUICKSTART.md](QUICKSTART.md)
2. **Intermediate**: Read [README.md](README.md)
3. **Advanced**: Explore source code in `src/`
4. **Expert**: Modify and extend components

## 🆘 Troubleshooting

### Common Issues

**"Index not found"**
```bash
python -m cli init  # Rebuild index
```

**"OpenAI API key not set"**
- Edit `.env` and add your key
- Query expansion is optional

**"Poor search results"**
- Enable query expansion in `.env`
- Increase `TOP_K_RETRIEVAL`
- Lower `RERANKER_THRESHOLD`

For more help: See [INSTALLATION.md](INSTALLATION.md) troubleshooting section.

## 🌟 Key Features

✅ Multi-language code parsing (9 languages)
✅ AST-aware semantic chunking
✅ FAISS-based vector search
✅ LLM query expansion (5 strategies)
✅ Cross-encoder re-ranking
✅ Git commit context
✅ Streamlit web UI
✅ Full command-line interface
✅ Python API
✅ Production-ready code

## 📞 Support Resources

| Need | Resource |
|------|----------|
| Quick Start | [QUICKSTART.md](QUICKSTART.md) |
| Installation | [INSTALLATION.md](INSTALLATION.md) |
| Full Docs | [README.md](README.md) |
| Architecture | [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) |
| Overview | [PROJECT_COMPLETION.md](PROJECT_COMPLETION.md) |
| Code Examples | `examples/` directory |
| Tests | `tests/` directory |

## 🎯 Next Steps

1. **Choose Your Path**:
   - → [QUICKSTART.md](QUICKSTART.md) if you just want to get running
   - → [INSTALLATION.md](INSTALLATION.md) if you need detailed setup
   - → [README.md](README.md) if you want to understand everything

2. **Install & Configure**
   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Index Your Codebase**
   ```bash
   python -m cli init
   ```

4. **Start Searching**
   ```bash
   streamlit run src/ui/app.py
   ```

5. **Explore**
   - Try different queries
   - Adjust settings in the UI
   - Check commit history

---

**Ready to use the RAG system?** Start with [QUICKSTART.md](QUICKSTART.md) 🚀

For detailed information, see the documentation index above.
