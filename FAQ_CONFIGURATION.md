# Configuration FAQ

## ❓ How do I load items to the database?

### **Short Answer: It's Automatic!**

The lore database is **automatically populated** when you run the pipeline. You don't need to manually load anything.

### **How It Works:**

```
1. Create Project in UI → Enter series concept
                ↓
2. Run Pipeline → Click "🚀 Run Full Pipeline"
                ↓
3. Series Refiner → Creates characters, locations, world elements
                ↓
4. Auto-Storage → Lore saved to Pinecone + JSON (automatic!)
                ↓
5. All Agents → Auto-query lore before generating content
```

### **What Gets Stored:**

After the **Series Refiner** stage completes:

✅ **Characters**
- Name, role, description
- Traits, motivations
- Relationships with other characters

✅ **Locations**
- Name, description
- Significance to story
- Atmospheric details

✅ **World Elements**
- Magic systems, technology
- Rules and limitations
- Cultural elements

### **Enable Lore Database:**

**In UI:**
1. Open sidebar (left side)
2. Enter **Pinecone API Key** (get free at pinecone.io)
3. Check **"Enable Lore Vector Database"** when creating project

**Without Pinecone:**
- Lore still works (JSON-only)
- No semantic search (less smart matching)
- Still enforces consistency

### **View Your Lore:**

After running the pipeline:
1. Go to **📊 Analytics** page
2. Scroll to **🎭 Lore Database** section
3. See character count, expand to view details

### **Manual Lore Editing:**

If you want to manually edit lore:

1. Load project in UI (**📂 Load Project**)
2. Find JSON file: `output/your_project_id_state.json`
3. Edit the `series.lore` section
4. Reload project in UI

---

## ❓ How do I select individual models for agents?

### **Option 1: Use Presets (In UI)**

The UI currently supports **5 presets**:

| Preset | Use Case | Cost |
|--------|----------|------|
| `balanced` | General use, good quality | $$ |
| `creative` | Maximum creativity, experimental | $$ |
| `precise` | Complex lore, consistency | $$ |
| `cost_optimized` | Budget projects (~70% savings) | $ |
| `premium` | Best quality, final manuscripts | $$$ |

**How to use:**
1. **✨ New Project** page
2. Under "Model Configuration"
3. Select preset from dropdown

### **Option 2: Custom Per-Agent Config (Python)**

For full control over each agent's model:

**Step 1: Create config file**

See: `custom_pipeline_example.py` (already created for you!)

**Example:**
```python
custom_config = {
    "series": {
        "model": "openai/gpt-4-turbo",
        "temperature": 0.3
    },
    "prose": {
        "model": "anthropic/claude-3-opus",
        "temperature": 0.95,
        "max_tokens": 2000
    },
    "qa": {
        "model": "openai/gpt-4",
        "temperature": 0.5
    }
    # Other agents use defaults
}
```

**Step 2: Initialize pipeline**
```python
pipeline = FictionPipeline(
    project_id="my_novel",
    model_config=custom_config  # Custom config
)
```

**Step 3: Run**
```python
final = pipeline.run(project)
```

### **Available Models:**

You can use ANY model from OpenRouter:

**Anthropic (Best for creative writing):**
- `anthropic/claude-3.5-sonnet` - Balanced, recommended
- `anthropic/claude-3-opus` - Best quality
- `anthropic/claude-3-haiku` - Fast & cheap

**OpenAI:**
- `openai/gpt-4-turbo`
- `openai/gpt-4o`
- `openai/gpt-4o-mini`

**Google:**
- `google/gemini-pro-1.5`
- `google/gemini-flash-1.5`

**Meta:**
- `meta-llama/llama-3.1-405b-instruct`
- `meta-llama/llama-3.1-70b-instruct`

Full list: https://openrouter.ai/models

### **Per-Agent Settings:**

Each agent can have:

```python
{
    "model": "anthropic/claude-3.5-sonnet",
    "temperature": 0.7,           # 0.0-1.0 (lower=consistent, higher=creative)
    "max_tokens": 2000,           # Max response length
    "top_p": 0.9,                 # Nucleus sampling (optional)
    "frequency_penalty": 0.3,     # Reduce repetition (optional)
    "presence_penalty": 0.2       # Encourage variety (optional)
}
```

### **Recommended Agent Configurations:**

**For Maximum Quality:**
```python
{
    "series": {"model": "anthropic/claude-3-opus", "temperature": 0.3},
    "book": {"model": "anthropic/claude-3-opus", "temperature": 0.3},
    "prose": {"model": "anthropic/claude-3-opus", "temperature": 0.9},
    "qa": {"model": "openai/gpt-4", "temperature": 0.4}
}
```

**For Cost Savings:**
```python
{
    "series": {"model": "anthropic/claude-3-haiku", "temperature": 0.3},
    "book": {"model": "anthropic/claude-3-haiku", "temperature": 0.3},
    "chapter": {"model": "anthropic/claude-3-haiku", "temperature": 0.4},
    "scene": {"model": "anthropic/claude-3-haiku", "temperature": 0.5},
    "beat": {"model": "anthropic/claude-3-haiku", "temperature": 0.3},
    "prose": {"model": "anthropic/claude-3.5-sonnet", "temperature": 0.8},  # Keep good for prose
    "qa": {"model": "anthropic/claude-3-haiku", "temperature": 0.5},
    "lore": {"model": "anthropic/claude-3-haiku", "temperature": 0.4}
}
```

**For Mixed Providers:**
```python
{
    "series": {"model": "google/gemini-pro-1.5", "temperature": 0.3},
    "prose": {"model": "anthropic/claude-3-opus", "temperature": 0.9},
    "qa": {"model": "openai/gpt-4", "temperature": 0.4}
}
```

---

## ❓ Does this save my settings?

### **What's Saved:**

✅ **Project data** → `output/project_id_state.json`
- Series metadata
- Book/chapter/scene structure
- All lore
- Generated prose
- QA reports

✅ **Checkpoints** → `output/project_id_v1_stage.json`
- After every major stage
- Versioned for rollback

✅ **Manuscripts** → `manuscripts/project_id_manuscript.md`
- Exported prose (Markdown)
- Final JSON

### **What's NOT Saved (Session Only):**

❌ **API Keys** - Re-enter each session (security)
❌ **UI preferences** - Reset on refresh
❌ **Model presets** - Choose again per project

### **Why API Keys Aren't Saved:**

For **security**, API keys are stored in:
- Session memory only
- Not written to disk
- Cleared when you close UI

**To Save API Keys Permanently:**

Set environment variables (one-time setup):

**Windows:**
```bash
setx OPENROUTER_API_KEY "your-key-here"
setx PINECONE_API_KEY "your-pinecone-key"
```

**Linux/Mac:**
```bash
export OPENROUTER_API_KEY="your-key-here"
export PINECONE_API_KEY="your-pinecone-key"
```

Or create `.env` file:
```
OPENROUTER_API_KEY=your-key-here
PINECONE_API_KEY=your-pinecone-key
```

Then UI auto-loads them!

### **Loading Previous Projects:**

1. **📂 Load Project** page
2. Select from dropdown (shows all saved projects)
3. Click **Load**
4. Project restored with all data

### **Resume from Checkpoint:**

All pipeline runs save checkpoints. To resume:

1. Load project JSON
2. Pipeline checks `processing_stage`
3. Resumes from last completed stage

---

## 📖 Quick Reference

| Task | Method |
|------|--------|
| **Load lore to database** | Automatic during pipeline run |
| **View lore** | UI → 📊 Analytics → Lore Database |
| **Edit lore** | Edit `output/project_state.json` |
| **Use preset models** | UI → ✨ New Project → Select preset |
| **Custom per-agent models** | Use `custom_pipeline_example.py` |
| **Save API keys permanently** | Create `.env` file or set env vars |
| **Load saved project** | UI → 📂 Load Project |
| **View model config** | UI shows on pipeline init |

---

## 🚀 Examples

### Example 1: Create Project with Lore Database

1. Launch UI: `launch_ui.bat`
2. Enter API keys in sidebar:
   - OpenRouter: `sk-or-v1-...`
   - Pinecone: `your-pinecone-key`
3. **✨ New Project**
4. Fill in series info
5. Check **"Enable Lore Vector Database"**
6. Choose preset: **"balanced"**
7. **🚀 Create Project**
8. **⚙️ Settings** → **Run Full Pipeline**
9. After Series Refiner completes → Lore auto-stored
10. **📊 Analytics** → View lore

### Example 2: Custom Model Config (Python)

```python
# Edit custom_pipeline_example.py with your config
custom_config = {
    "prose": {
        "model": "anthropic/claude-3-opus",
        "temperature": 0.95
    }
}

# Run it
python custom_pipeline_example.py
```

### Example 3: Load and Continue Project

1. UI → **📂 Load Project**
2. Select: `my_novel_001_state.json`
3. Click **Load**
4. **⚙️ Settings** → **Run Full Pipeline** (continues from last stage)

---

## 💡 Pro Tips

1. **Start with presets** - They're optimized for most use cases
2. **Enable Pinecone** - Much better lore consistency
3. **Save .env file** - Never re-enter API keys
4. **Check Analytics** - View lore after Series Refiner
5. **Use cost_optimized** - For testing/first drafts
6. **Use premium** - For final manuscripts
7. **Custom config** - When you need specific model per stage

---

**Need more help? See:**
- `README.md` - Full pipeline documentation
- `UI_README.md` - Complete UI guide
- `example_custom_models.py` - Preset examples
- `custom_pipeline_example.py` - Per-agent config examples
