# Fiction Generation Pipeline

A professional-grade AI-powered fiction writing system using LangChain and OpenRouter. This implements a hierarchical agent-based workflow with quality gates, lore management, and editorial review to generate complete novels from concept to polished manuscript.

## 🎯 Features

### Core Architecture
- **Agent-Based Pipeline**: Specialized AI agents for each stage of fiction creation
- **Quality Gates**: QA Agent + Lore Master validate every stage before progression
- **Lore Management**: Pinecone vector database tracks and enforces world-building consistency
- **Editorial Pipeline**: Professional editing workflow (Story Analysis → Consistency → Developmental → Line Editing)
- **State Persistence**: Checkpoint and resume capability at any stage
- **Structured Data**: Complete Pydantic schemas ensure type safety and validation

### Workflow Stages

```
Series Concept
    ↓
[Series Refiner] → Creates series outline, initial lore
    ↓ [QA + Lore Master validation]
[Book Outliner] → 3-act structure, character arcs, chapter scaffold
    ↓ [QA + Lore Master validation]
[Chapter Developer] → Detailed chapter breakdowns with scenes
    ↓ [QA + Lore Master validation]
[Scene Developer] → Scene-level detail (POV, conflicts, turning points)
    ↓ [QA + Lore Master validation]
[Beat Developer] → Story beats (action, dialogue, description units)
    ↓ [QA + Lore Master validation]
[Prose Generator] → Actual narrative prose from beats
    ↓ [QA + Lore Master validation]
[Editorial Phase] → Story Analyst → Consistency Validator → Dev Editor → Line Editor
    ↓ [Final QA]
[Export] → manuscript.md + complete project.json
```

## 📁 Project Structure

```
fiction-pipeline/
├── agents/                     # AI agents for each workflow stage
│   ├── __init__.py
│   ├── base_agent.py          # Abstract base class
│   ├── series_refiner.py      # Series outline creation
│   ├── book_outliner.py       # Book structure development
│   ├── chapter_developer.py   # Chapter breakdown
│   ├── scene_developer.py     # Scene development
│   ├── beat_developer.py      # Beat creation
│   ├── prose_generator.py     # Prose writing
│   ├── qa_agent.py            # Quality assurance
│   ├── lore_master.py         # Lore consistency checking
│   ├── story_analyst.py       # Developmental story analysis
│   ├── consistency_validator.py  # Continuity validation
│   ├── developmental_editor.py   # Structural editing
│   └── line_editor.py         # Prose polishing
├── models/
│   ├── __init__.py
│   └── schema.py              # Pydantic data models
├── validators/
│   └── schema_validator.py    # Schema validation
├── utils/
│   ├── logger.py              # Logging utilities
│   ├── state_manager.py       # Checkpoint management
│   ├── prompts.py             # Versioned prompt templates
│   └── lore_store.py          # Pinecone vector store wrapper
├── tests/                     # Unit and integration tests
├── output/                    # Generated JSON checkpoints
├── logs/                      # Execution logs
├── pipeline.py                # Main orchestrator
├── run.py                     # CLI entry point
├── requirements.txt
└── README.md
```

## 🚀 Installation

### Prerequisites
- Python 3.10+
- OpenRouter API key ([Get one here](https://openrouter.ai/keys))
- Pinecone API key (optional, for lore management) ([Get one here](https://www.pinecone.io/))

### Setup

```bash
# Clone or download the project
cd fiction-pipeline

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# Create .env file:
echo "OPENROUTER_API_KEY=your-key-here" > .env
echo "PINECONE_API_KEY=your-key-here" >> .env  # Optional
```

## 📝 Usage

### Quick Start

```python
from pipeline import FictionPipeline
from models.schema import FictionProject, Metadata, Series, Lore
from datetime import datetime

# Create initial project
project = FictionProject(
    metadata=Metadata(
        last_updated=datetime.now(),
        last_updated_by="User",
        processing_stage="series",
        status="draft",
        project_id="my_novel_001",
        iteration=1
    ),
    series=Series(
        title="The Quantum Heist",
        premise="A team of specialists must steal an impossible artifact from a time-locked vault.",
        genre="science fiction",
        target_audience="adult",
        themes=[],
        persistent_threads=[],
        lore=Lore(),
        books=[]
    )
)

# Initialize pipeline
pipeline = FictionPipeline(
    project_id="my_novel_001",
    output_dir="output"
)

# Run complete pipeline
final_project = pipeline.run(project)

# Export manuscript
pipeline.export_manuscript(final_project, "manuscripts/")
```

### CLI Usage

```bash
# Run full pipeline from series concept
python run.py --input series_concept.txt --project-id my-novel --output output/

# Resume from checkpoint
python run.py --project-id my-novel --resume

# Run specific stage only
python run.py --project-id my-novel --stage book_outliner

# Run with editorial phase
python run.py --project-id my-novel --run-editorial
```

### Input Format (series_concept.txt)

```
The Quantum Heist
A team of specialists must steal an impossible artifact from a time-locked vault.
science fiction
```

## 🎨 Model Configuration (**✅ FULLY CUSTOMIZABLE!**)

### Per-Agent Model Customization

Each agent in the pipeline can use a different model and parameters. Configure via **presets** or **custom configuration**.

### Quick Start: Using Presets

```python
from pipeline import FictionPipeline

# Option 1: Balanced (default) - Good quality, reasonable cost
pipeline = FictionPipeline(
    project_id="my-novel",
    preset="balanced"
)

# Option 2: Creative - Maximum creativity/temperature
pipeline = FictionPipeline(
    project_id="my-novel",
    preset="creative"
)

# Option 3: Precise - Maximum consistency, low temperature
pipeline = FictionPipeline(
    project_id="my-novel",
    preset="precise"
)

# Option 4: Cost Optimized - Uses Claude Haiku for most stages
pipeline = FictionPipeline(
    project_id="my-novel",
    preset="cost_optimized"
)

# Option 5: Premium - Claude Opus for everything (best quality, highest cost)
pipeline = FictionPipeline(
    project_id="my-novel",
    preset="premium"
)
```

### Custom Configuration Per Agent

```python
custom_config = {
    "prose": {
        "model": "anthropic/claude-3-opus",  # Best model for prose
        "temperature": 0.95,                 # Maximum creativity
        "max_tokens": 3000
    },
    "qa": {
        "model": "openai/gpt-4",            # Different provider for QA
        "temperature": 0.4
    },
    "series": {
        "temperature": 0.2                   # Very structured planning
    }
    # Other agents use defaults
}

pipeline = FictionPipeline(
    project_id="my-novel",
    model_config=custom_config
)
```

### Available Configuration Options

Each agent supports:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | str | `anthropic/claude-3.5-sonnet` | Model identifier |
| `temperature` | float | varies | 0.0-1.0 (lower=consistent, higher=creative) |
| `max_tokens` | int | varies | Maximum response length |
| `top_p` | float | None | Nucleus sampling (0.0-1.0) |
| `frequency_penalty` | float | None | Reduce repetition (-2.0 to 2.0) |
| `presence_penalty` | float | None | Encourage topic diversity (-2.0 to 2.0) |

### Default Temperatures by Agent

| Agent | Default Temp | Rationale |
|-------|--------------|-----------|
| `series` | 0.3 | Structured series planning |
| `book` | 0.3 | Logical act structure |
| `chapter` | 0.4 | Balanced scene planning |
| `scene` | 0.5 | Moderate beat creativity |
| `beat` | 0.3 | Structured beat planning |
| `prose` | **0.8** | **HIGH for creative prose** ✨ |
| `qa` | 0.5 | Balanced critical analysis |
| `lore` | 0.4 | Consistent lore validation |

### Preset Details

**`balanced`** (default)
- Claude 3.5 Sonnet for all agents
- Temperature: 0.3-0.8 (structured → creative)
- Best for: General use, good quality at reasonable cost

**`creative`**
- Claude 3.5 Sonnet for all agents
- Temperature: 0.5-0.95 (moderate → maximum creativity)
- Best for: Experimental fiction, literary prose, unique styles

**`precise`**
- Claude 3.5 Sonnet for all agents
- Temperature: 0.2-0.5 (very structured)
- Best for: Series with complex lore, technical accuracy needed

**`cost_optimized`**
- Claude Haiku for structure (series, book, chapter, scene, beat, qa, lore)
- Claude 3.5 Sonnet for prose only
- Best for: Budget-conscious projects, first drafts

**`premium`**
- Claude Opus for nearly everything
- Claude 3.5 Sonnet for beat stage only
- Temperature: Higher overall for quality + creativity
- Best for: Final polished manuscripts, maximum quality

### Available Models on OpenRouter

```python
# Anthropic (Best for creative writing)
"anthropic/claude-3.5-sonnet"  # Balanced, recommended
"anthropic/claude-3-opus"      # Best quality, highest cost
"anthropic/claude-3-haiku"     # Fast and cheap

# OpenAI
"openai/gpt-4-turbo"
"openai/gpt-4o"
"openai/gpt-4o-mini"

# Google
"google/gemini-pro-1.5"
"google/gemini-flash-1.5"

# Meta
"meta-llama/llama-3.1-405b-instruct"
"meta-llama/llama-3.1-70b-instruct"

# See full list: https://openrouter.ai/models
```

### Example: Mix and Match Providers

```python
# Use Claude for prose, GPT-4 for QA, Gemini for structure
config = {
    "series": {"model": "google/gemini-pro-1.5", "temperature": 0.3},
    "book": {"model": "google/gemini-pro-1.5", "temperature": 0.3},
    "prose": {"model": "anthropic/claude-3-opus", "temperature": 0.9},
    "qa": {"model": "openai/gpt-4", "temperature": 0.4}
}

pipeline = FictionPipeline(project_id="test", model_config=config)
```

### Configuration at Runtime

When you initialize the pipeline, it prints the active configuration:

```
🤖 Model Configuration:
  series       → anthropic/claude-3.5-sonnet              (temp=0.3)
  book         → anthropic/claude-3.5-sonnet              (temp=0.3)
  chapter      → anthropic/claude-3.5-sonnet              (temp=0.4)
  scene        → anthropic/claude-3.5-sonnet              (temp=0.5)
  beat         → anthropic/claude-3.5-sonnet              (temp=0.3)
  prose        → anthropic/claude-3-opus                  (temp=0.9)
  qa           → openai/gpt-4                             (temp=0.4)
  lore         → anthropic/claude-3.5-sonnet              (temp=0.4)
```

See `example_custom_models.py` for complete working examples.

## 🗂️ Data Schema

### Complete Hierarchy

```
FictionProject
├── metadata (version, status, stage)
├── series
│   ├── title, premise, themes, genre
│   ├── lore
│   │   ├── characters (name, role, traits, relationships)
│   │   ├── locations (name, description, significance)
│   │   └── world_elements (name, type, rules)
│   └── books[]
│       ├── title, premise, themes
│       ├── act_structure (3 acts with key events)
│       ├── character_arcs[]
│       └── chapters[]
│           ├── title, purpose, act
│           ├── character_focus (POV, present, arc moments)
│           └── scenes[]
│               ├── purpose, scene_type, POV, setting
│               ├── conflicts[], turning_points[]
│               └── beats[]
│                   ├── description, emotional_tone
│                   └── prose (content, word_count)
├── qa_reports[] (quality assurance feedback)
├── editorial_reports[] (story analysis, consistency, edits)
└── revision_history[] (change tracking)
```

## 🔍 Quality Gates

Every stage includes validation:

1. **Schema Validation**: Pydantic ensures data structure integrity
2. **QA Agent Review**: Checks structure, pacing, character arcs, themes
3. **Lore Master Validation**: Enforces consistency with established lore
4. **Retry Logic**: Automatically retries with feedback (max 3 attempts)

### Approval Flow

```
[Agent Generates Content]
    ↓
[Schema Validator] → PASS/FAIL
    ↓ PASS
[QA Agent] → Scores + Approval
    ↓ APPROVED?
    ├─ NO → Inject feedback, retry (max 3x)
    └─ YES → Continue
        ↓
[Lore Master] → Lore Validation
    ↓ APPROVED?
    ├─ NO → Inject feedback, retry (max 3x)
    └─ YES → Advance to next stage
```

## 🎭 Lore Management (**✅ IMPLEMENTED!**)

### Automatic Lore Database with Pinecone

The system automatically stores and queries lore using a vector database for consistency:

**Setup (Optional but Recommended):**

1. **Get Pinecone API Key**: Sign up at [pinecone.io](https://www.pinecone.io/)
2. **Set Environment Variable**:
   ```bash
   # Windows
   set PINECONE_API_KEY=your-pinecone-key

   # Linux/Mac
   export PINECONE_API_KEY=your-pinecone-key
   ```
3. **Enable in Pipeline**:
   ```python
   pipeline = FictionPipeline(
       project_id="my-novel",
       use_lore_db=True  # Default: True
   )
   ```

**What Happens Automatically:**

1. **After Series Refiner** → All lore (characters, locations, world elements) stored in Pinecone
2. **Before Each Generation** → Agents query relevant lore (semantic search, top 10 matches)
3. **During Quality Gates** → Lore Master checks for contradictions
4. **Lore Gets Injected** → Relevant lore added to prompts automatically

**If Pinecone Not Available:**
- System falls back to JSON-only lore storage
- Prints warning: `⚠️ Warning: PINECONE_API_KEY not set. Lore vector store disabled.`
- Everything still works, just without semantic lore retrieval

### Lore Workflow

```
[Series Refiner] → Creates initial lore entries
    ↓
[Store in Pinecone] ✅ AUTOMATIC → Vector embeddings
    ↓
[Each Agent] ✅ AUTOMATIC → Queries relevant lore (top 10) via semantic search
    ↓ (Lore injected into prompts)
[Generate Content] → Uses relevant lore context
    ↓
[Lore Master] → Quality Gate:
    ├─ Detects lore breaks → FAIL, retry with feedback
    └─ Detects new lore → Logged in qa_reports
```

### Example Lore Query

When generating Chapter 3, the system automatically:
```python
# Behind the scenes:
lore = lore_store.query_lore(
    query="Chapter 3: The protagonist confronts the antagonist",
    project_id="my-novel",
    top_k=10
)
# Returns: protagonist details, antagonist info, relevant locations, rules
# → Injected into prompt to ensure consistency
```

## ✍️ Editorial Pipeline

Professional editing workflow after prose generation:

### Phase 1: Developmental Editing

```
[Story Analyst] → Compare prose vs. original outline
    ↓ Identifies:
    ├─ Plot holes
    ├─ Character arc breaks
    ├─ Pacing issues
    └─ Theme drift
    ↓
[Consistency Validator] → Check lore/continuity
    ↓ Identifies:
    ├─ Lore violations
    ├─ Timeline conflicts
    └─ Logic gaps
    ↓
[Developmental Editor] → Fix major issues
    ↓ (Re-analyze until approved)
```

### Phase 2: Line Editing

```
[Line Editor] → Sentence-level polish
    ↓ Improves:
    ├─ Tighten prose (remove fluff)
    ├─ Fix awkward sentences
    ├─ Enhance descriptions
    └─ Polish voice consistency
    ↓
[Final QA] → Approval gate
    ↓ APPROVED?
    └─ YES → Export manuscript
```

## 💰 Cost Estimation

Using **Claude 3.5 Sonnet** on OpenRouter:

| Stage | API Calls | Est. Cost |
|-------|-----------|-----------|
| Series Refiner | 1 | $0.10 |
| Book Outliner | 1 per book | $0.20 |
| Chapter Developer | ~20 | $2.00 |
| Scene Developer | ~60 | $4.00 |
| Beat Developer | ~200 | $6.00 |
| Prose Generator | ~200 | $15.00 |
| QA + Lore (all stages) | ~40 | $3.00 |
| Editorial Phase | ~50 | $5.00 |
| **Total (1 book, ~100k words)** | **~600** | **~$35** |

### Cost-Saving Tips

1. **Use `cost_optimized` preset**: Automatically uses Claude Haiku for structure stages
   ```python
   pipeline = FictionPipeline(project_id="my-novel", preset="cost_optimized")
   ```
   Estimated savings: ~70% reduction ($35 → ~$10 per book)

2. **Generate fewer chapters first**: Test with 5 chapters before full book

3. **Skip editorial**: Go straight from prose to export

4. **Use model mixing**: Cheap models for structure, good model for prose only
   ```python
   config = {
       "series": {"model": "anthropic/claude-3-haiku"},
       "book": {"model": "anthropic/claude-3-haiku"},
       "chapter": {"model": "anthropic/claude-3-haiku"},
       "scene": {"model": "anthropic/claude-3-haiku"},
       "prose": {"model": "anthropic/claude-3.5-sonnet", "temperature": 0.8}
   }
   ```

## 🧪 Testing

```bash
# Run unit tests
pytest tests/test_schema.py

# Run integration tests
pytest tests/test_pipeline.py

# Test with minimal fixture
python run.py --input tests/fixtures/minimal_series.txt --project-id test-001
```

## 🔧 Advanced Configuration

### Environment Variables

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-...

# Optional
PINECONE_API_KEY=...  # For lore vector database
```

### Pipeline Initialization Options

```python
pipeline = FictionPipeline(
    project_id="my-novel",           # Unique identifier
    output_dir="output",             # Checkpoint directory
    openrouter_api_key="sk-or-...",  # Or use env var
    use_lore_db=True,                # Enable Pinecone (default: True)
    preset="balanced",               # Preset configuration
    model_config=None                # Custom per-agent config
)
```

### Reproducibility

For deterministic outputs (useful for testing), use low temperatures:

```python
pipeline = FictionPipeline(
    project_id="test",
    preset="precise"  # All temperatures 0.2-0.5
)
```

Note: True determinism requires model provider support (some models don't support seed parameters).

## 📊 Output

### Generated Files

```
output/
├── my-novel_state.json         # Complete project data
├── my-novel_v1.json            # Checkpoint after stage 1
├── my-novel_v2.json            # Checkpoint after stage 2
└── ...

manuscripts/
├── my-novel_manuscript.md      # Final prose (Markdown format)
└── my-novel_final.json         # Complete project with all metadata
```

### Manuscript Format

```markdown
# The Quantum Heist
*A team of specialists must steal an impossible artifact from a time-locked vault.*

---

# Book 1: The Impossible Score

## Chapter 1: The Recruiting Drive

[Scene 1 prose...]

[Scene 2 prose...]

## Chapter 2: First Contact

[...]
```

## 🛠️ Extending the Pipeline

### Add Custom Agents

```python
from agents.base_agent import BaseAgent

class MyCustomAgent(BaseAgent):
    def get_prompt(self):
        return "Your custom prompt here..."

    def process(self, input_data: FictionProject):
        # Your logic here
        return input_data
```

### Custom Prompts

Edit prompt templates in `utils/prompts.py` or override in agent classes.

### Add New Stages

```python
# In pipeline.py
stages = ["series", "book", "chapter", "scene", "beat", "my_custom_stage", "prose", "editorial"]
```

## 🐛 Troubleshooting

### Common Issues

**Error: `No module named 'langchain_openai'`**
```bash
pip install langchain-openai
```

**Error: API Key not found**
```bash
# Check environment variable
echo %OPENROUTER_API_KEY%  # Windows
echo $OPENROUTER_API_KEY   # Linux/Mac

# Or pass directly:
pipeline = FictionPipeline(openrouter_api_key="your-key")
```

**Error: JSON parsing failed**
- Agent returned invalid JSON
- Check logs in `logs/` directory
- Try lowering temperature or using more capable model

**Error: Rate limit exceeded**
- Add delays between API calls
- Switch to different model
- Implement exponential backoff

### Lore Breaks

If Lore Master repeatedly fails:
1. Check `editorial_reports` in output JSON
2. Review conflicting lore entries
3. Manually edit lore in `series.lore` section
4. Resume pipeline

## 📚 Examples

### Minimal Series Concept

```python
concept = """
Echoes of Tomorrow
A time traveler discovers they're trapped in a loop, reliving the same day where Earth is destroyed.
science fiction thriller
"""
```

### Fantasy Series

```python
concept = """
The Shattered Crown
In a world where magic is dying, a young mage must find the fragments of an ancient artifact to save their kingdom.
epic fantasy
"""
```

### Mystery Series

```python
concept = """
The Cryptographer's Code
A librarian discovers century-old encrypted messages in books that predict modern murders.
mystery thriller
"""
```

## 🎯 Roadmap

### Current Status
- ✅ Complete data schema
- ✅ Agent architecture
- ✅ Quality gates
- ✅ Series Refiner agent (full implementation)
- ⚠️ Other agents (placeholder - expand as needed)
- ⚠️ Lore vector store (integration ready, needs Pinecone key)
- ⚠️ Editorial pipeline (structure in place, agents need expansion)

### Future Enhancements
- [ ] Parallel scene processing (speed optimization)
- [ ] Multi-POV character management
- [ ] Subplot tracking and weaving
- [ ] Chapter summaries for continuity
- [ ] Character consistency analyzer
- [ ] Plot hole detection (automated)
- [ ] Export to EPUB/DOCX formats
- [ ] Web UI for project management
- [ ] Collaborative editing support

## 📖 Documentation

### Key Concepts

**Agents**: Specialized AI workers that handle one transformation step (e.g., outline → chapters)

**Quality Gates**: Validation checkpoints that enforce quality standards before progression

**Lore**: World-building database (characters, locations, rules) enforced across all content

**Beats**: Smallest narrative units (~200-800 words each) that become prose paragraphs

**Editorial Phase**: Post-prose workflow that fixes plot holes, consistency issues, and polishes prose

### Best Practices

1. **Start small**: Generate 1 book with 10 chapters before scaling to full series
2. **Review checkpoints**: Examine JSON output after each major stage
3. **Iterate on lore**: Refine lore entries manually for better consistency
4. **Use version control**: Track your `output/` directory with git
5. **Save intermediate states**: Keep all checkpoint JSONs for rollback capability

## 🤝 Contributing

This is a modular system designed for expansion. To add new agents:

1. Create new agent file in `agents/`
2. Inherit from `BaseAgent`
3. Implement `get_prompt()` and `process()` methods
4. Add to pipeline stages in `pipeline.py`
5. Update schema if needed

## 📄 License

MIT License - Use freely for commercial or personal projects.

## 🙏 Credits

- **Architecture**: Based on professional fiction editing workflows
- **LangChain**: Agent orchestration framework
- **OpenRouter**: Multi-model API access
- **Pydantic**: Data validation and serialization

---

**Happy Writing! 📚✨**

For questions or issues, please open a GitHub issue or check the project documentation.
