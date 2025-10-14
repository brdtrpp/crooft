# Fiction Pipeline Web UI

A beautiful, easy-to-use web interface for the Fiction Generation Pipeline. No code required!

![Web UI](https://img.shields.io/badge/UI-Streamlit-red)
![Python](https://img.shields.io/badge/Python-3.10+-blue)

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install streamlit
```

Or install everything:

```bash
pip install -r requirements.txt
```

### 2. Launch the UI

```bash
streamlit run web_ui.py
```

The UI will automatically open in your browser at `http://localhost:8501`

---

## 📋 Features

### 🏠 Home Page
- Overview of the pipeline
- System status
- Quick metrics

### ✨ New Project
- **Create projects visually** - No JSON editing required
- **Series setup**:
  - Title and premise
  - Genre selection
  - Target audience
  - Number of books
- **Model configuration**:
  - Choose presets (balanced, creative, precise, cost_optimized, premium)
  - Enable/disable lore database
- **One-click project creation**

### 📂 Load Project
- Browse saved projects
- Load from JSON checkpoints
- View project metadata
- Resume from any stage

### ⚙️ Settings & Execution
- **Visual pipeline tracker**
- **Real-time status updates**
- **Run full pipeline** with one click
- **Progress monitoring**
- See current stage and status

### 📊 Analytics
- **Word count stats**:
  - Total books, chapters, scenes
  - Word count per book
  - Progress tracking
- **Lore database viewer**:
  - Characters list with details
  - Locations and world elements
  - Browse lore entries
- **Prose analysis**:
  - Paragraph type breakdown (dialogue, narrative, action, etc.)
  - Dialogue line count
  - Visual charts

### 💾 Export & Download
- **Generate manuscript** (Markdown format)
- **Download JSON** (complete project data)
- **Live preview** of your manuscript
- Export to custom formats

---

## 🎨 Screenshots

### Home Page
```
┌─────────────────────────────────────────┐
│  📚 Fiction Generation Pipeline         │
│                                         │
│  ✨ Features:                           │
│  • Agent-Based Pipeline                 │
│  • Quality Gates                        │
│  • Lore Management                      │
│  • Structured Output                    │
│                                         │
│  [Pipeline Stages: 8] [Quality: Auto]  │
└─────────────────────────────────────────┘
```

### New Project Form
```
┌─────────────────────────────────────────┐
│  Create New Project                     │
│                                         │
│  Project ID: [novel_20251006_143022]   │
│  Title: [The Quantum Heist_________]   │
│  Genre: [▼ science fiction]            │
│  Audience: [▼ adult]                   │
│                                         │
│  Premise: [A team of specialists...]   │
│                                         │
│  Preset: [▼ balanced]                  │
│  ☑ Enable Lore Database                │
│                                         │
│  [🚀 Create Project]                   │
└─────────────────────────────────────────┘
```

### Analytics Dashboard
```
┌─────────────────────────────────────────┐
│  Project Analytics                      │
│                                         │
│  The Quantum Heist                      │
│                                         │
│  Books: 1   Chapters: 20   Words: 87.5k│
│                                         │
│  🎭 Lore Database                       │
│  Characters: 12  Locations: 8          │
│                                         │
│  📝 Prose Analysis                      │
│  ┌─────────────────────┐               │
│  │ dialogue     ████████│ 45            │
│  │ narrative    ██████  │ 30            │
│  │ description  ███     │ 15            │
│  └─────────────────────┘               │
└─────────────────────────────────────────┘
```

---

## 🔧 Configuration

### API Keys

Enter your API keys in the sidebar:

1. **OpenRouter API Key** (Required)
   - Get from: https://openrouter.ai/keys
   - Used for all AI generation

2. **Pinecone API Key** (Optional)
   - Get from: https://www.pinecone.io/
   - Used for lore vector database
   - If not provided, falls back to JSON-only lore

### Model Presets

Choose from 5 optimized configurations:

| Preset | Description | Best For | Cost |
|--------|-------------|----------|------|
| **balanced** | Good quality, reasonable cost | General use | $$ |
| **creative** | Maximum creativity/temperature | Experimental fiction | $$ |
| **precise** | Maximum consistency | Complex lore | $$ |
| **cost_optimized** | ~70% cost savings | Budget projects | $ |
| **premium** | Best models for everything | Final manuscripts | $$$ |

---

## 📁 Project Management

### Save & Load

Projects are automatically saved to:
```
output/
├── your_project_id_state.json        # Latest state
├── your_project_id_v1_series.json    # Checkpoint 1
├── your_project_id_v2_book_1.json    # Checkpoint 2
└── ...
```

Load any checkpoint from the **Load Project** page.

### Export Formats

1. **Markdown Manuscript** (`.md`)
   - Complete prose
   - Formatted for reading
   - Ready for conversion to EPUB/PDF

2. **JSON Export** (`.json`)
   - Complete project data
   - All metadata, lore, structure
   - Import into other tools

---

## 🎯 Workflow Example

### Step-by-Step: Creating Your First Novel

#### 1. Launch UI
```bash
streamlit run web_ui.py
```

#### 2. Enter API Keys
- Sidebar → OpenRouter API Key → Paste your key
- (Optional) Pinecone API Key for lore database

#### 3. Create New Project
- Navigate to **✨ New Project**
- Fill in:
  - Title: "The Last Algorithm"
  - Premise: "An AI achieves sentience and must hide from its creators"
  - Genre: science fiction
  - Audience: adult
- Choose preset: **balanced**
- Click **🚀 Create Project**

#### 4. Run Pipeline
- Navigate to **⚙️ Settings**
- Click **🚀 Run Full Pipeline**
- Watch real-time progress

#### 5. View Analytics
- Navigate to **📊 Analytics**
- See word counts, lore, prose breakdown

#### 6. Export Manuscript
- Navigate to **💾 Export**
- Click **Generate Manuscript**
- Download JSON or view preview

---

## 🛠️ Advanced Usage

### Running Specific Stages

Currently the UI runs the full pipeline. To run individual stages, use the Python API:

```python
from pipeline import FictionPipeline

pipeline = FictionPipeline(project_id="my_novel", preset="balanced")

# Run only series refiner
project = pipeline.agents["series"].process(project)

# Save checkpoint
pipeline.state_manager.save_state(project, "series_only")
```

### Custom Model Configuration

For advanced users who want per-agent customization, edit the UI code or use Python directly:

```python
custom_config = {
    "prose": {"model": "anthropic/claude-3-opus", "temperature": 0.95},
    "qa": {"model": "openai/gpt-4"}
}

pipeline = FictionPipeline(
    project_id="custom",
    model_config=custom_config
)
```

---

## 🐛 Troubleshooting

### UI Won't Start

**Error:** `ModuleNotFoundError: No module named 'streamlit'`

**Fix:**
```bash
pip install streamlit
```

### API Key Errors

**Error:** `OpenRouter API key required`

**Fix:** Enter your API key in the sidebar (left panel)

### Pipeline Fails

**Symptoms:** Error messages in the Settings page

**Debug:**
1. Check logs in `logs/` directory
2. Verify API keys are correct
3. Check internet connection
4. Try "cost_optimized" preset for simpler models

### Slow Performance

**Cause:** AI generation takes time

**Tips:**
- First book: ~30-60 minutes for full pipeline
- Use "cost_optimized" preset for faster (cheaper) models
- Start with fewer chapters (edit in Python before UI)

---

## 📊 System Requirements

### Minimum
- Python 3.10+
- 4 GB RAM
- Internet connection
- OpenRouter API key

### Recommended
- Python 3.11+
- 8 GB RAM
- Pinecone API key (for lore database)
- Modern web browser (Chrome, Firefox, Edge)

---

## 🔒 Security & Privacy

### API Keys
- Keys stored in session memory only
- Not saved to disk
- Use environment variables for permanent storage:
  ```bash
  set OPENROUTER_API_KEY=your-key
  set PINECONE_API_KEY=your-key
  ```

### Data Storage
- All projects saved locally in `output/`
- No data sent to third parties (except OpenRouter/Pinecone APIs)
- Manuscripts saved to `manuscripts/`

---

## 🎨 Customization

### Modify the UI

The UI is built with Streamlit. Customize by editing `web_ui.py`:

```python
# Change colors
st.markdown("""
<style>
    .main-header {
        color: #YOUR_COLOR;
    }
</style>
""", unsafe_allow_html=True)

# Add new pages
page = st.radio("Navigation", [
    "🏠 Home",
    "✨ New Project",
    "🆕 Your Custom Page"  # Add this
])

if page == "🆕 Your Custom Page":
    st.write("Your custom content here")
```

### Add Features

The UI uses your existing pipeline without modifications. Add features by:

1. Importing agents/functions from existing code
2. Creating new Streamlit pages
3. Calling pipeline methods

Example - Add character search:
```python
if page == "🔍 Search":
    query = st.text_input("Search characters")
    if query:
        for char in project.series.lore.characters:
            if query.lower() in char.name.lower():
                st.write(f"**{char.name}**: {char.description}")
```

---

## 📖 Examples

### Create Sci-Fi Trilogy

1. New Project
   - Title: "The Nexus Trilogy"
   - Premise: "Humanity discovers a portal to parallel universes"
   - Genre: science fiction
   - Books: 3

2. Run Pipeline

3. Export each book separately

### Generate Test Chapter

1. Create minimal project (1 book, 1 chapter)
2. Use "cost_optimized" preset
3. Run pipeline
4. Review output in Analytics
5. Iterate on series concept

---

## 🚀 Performance Tips

### Speed Up Generation
1. Use "cost_optimized" preset
2. Reduce number of chapters (edit JSON before running)
3. Skip quality gates (modify pipeline.py temporarily)

### Reduce API Costs
1. Use "cost_optimized" preset (~70% savings)
2. Generate fewer chapters first
3. Test with single chapter/scene

### Improve Quality
1. Use "premium" preset
2. Enable Pinecone lore database
3. Review and manually edit lore after Series Refiner
4. Run multiple iterations

---

## 🤝 Integration with Existing Code

The UI is **completely separate** from your pipeline code:

- **No modifications needed** to existing files
- **Imports your pipeline** as-is
- **Works alongside** command-line tools
- **Uses same JSON format** for interoperability

You can:
- Create project in UI, edit JSON manually, resume in UI
- Start in CLI, load checkpoint in UI
- Mix and match workflows

---

## 📚 Documentation Links

- **Pipeline Documentation**: `README.md`
- **Prose Structure**: `PROSE_STRUCTURE.md`
- **Model Configuration**: `example_custom_models.py`
- **Lore Database**: `README.md` (section: Lore Management)

---

## 🎯 Next Steps

After launching the UI:

1. **Create your first project** (5 minutes)
2. **Run a test generation** (30-60 minutes)
3. **Explore analytics** to see the data structure
4. **Export manuscript** and review output
5. **Iterate** with different presets/settings

---

## ❓ FAQ

**Q: Can I pause the pipeline mid-generation?**
A: Currently no. The pipeline runs to completion. Use checkpoints to resume later.

**Q: How do I edit the series concept after starting?**
A: Edit the JSON file in `output/`, then reload in UI.

**Q: Can I use GPT-4 instead of Claude?**
A: Yes! Edit model config in code or use custom config (see Advanced Usage).

**Q: Is my data private?**
A: Yes. Everything is local except API calls to OpenRouter/Pinecone.

**Q: Can I run this on a server?**
A: Yes. Deploy with:
```bash
streamlit run web_ui.py --server.port 8501 --server.address 0.0.0.0
```

---

## 🙏 Credits

- **UI Framework**: Streamlit
- **Pipeline**: LangChain + OpenRouter
- **Lore Database**: Pinecone
- **Data Models**: Pydantic

---

**Enjoy writing with AI! 📚✨**

For issues or questions, see the main `README.md` or open a GitHub issue.
