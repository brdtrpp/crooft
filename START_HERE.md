# 🚀 Quick Start Guide - Fiction Pipeline UI

## ✅ All Dependencies Installed!

All required packages are now installed:
- ✅ Streamlit (Web UI framework)
- ✅ Pinecone (Lore database)
- ✅ LangChain (AI pipeline)
- ✅ All other dependencies

---

## 🎯 Launch the UI (Choose ONE method)

### **Method 1: Double-Click the Launcher** (Easiest!)

1. Find the file: `launch_ui.bat`
2. **Double-click it**
3. If Streamlit asks for email, just press **Enter** to skip
4. Browser will open automatically at `http://localhost:8501`

---

### **Method 2: Command Line**

Open a new terminal/command prompt and run:

```bash
C:\Users\trapp\AppData\Local\Programs\Python\Python313\python.exe -m streamlit run web_ui.py
```

Then:
1. Press **Enter** when it asks for email (optional)
2. Browser opens at `http://localhost:8501`

---

## 🎨 What You'll See

The UI has 6 pages:

1. **🏠 Home** - Overview and status
2. **✨ New Project** - Create projects visually
3. **📂 Load Project** - Load saved projects
4. **⚙️ Settings** - Run the pipeline
5. **📊 Analytics** - View stats and lore
6. **💾 Export** - Download manuscripts

---

## 📝 First-Time Setup

### 1. Enter Your API Key

When the UI opens:
- Look for the **sidebar** (left side)
- Enter your **OpenRouter API Key**
- (Optional) Enter **Pinecone API Key** for lore database

### 2. Create Your First Project

- Click **✨ New Project** in sidebar
- Fill in:
  - **Title**: "My First Novel"
  - **Premise**: "A brief description of your story"
  - **Genre**: Choose from dropdown
  - **Preset**: Start with "balanced"
- Click **🚀 Create Project**

### 3. Run the Pipeline

- Click **⚙️ Settings** in sidebar
- Click **🚀 Run Full Pipeline**
- Watch the progress!

---

## 🐛 Troubleshooting

### UI Won't Open in Browser

Manually go to: **http://localhost:8501**

### "Email:" Prompt Stuck

Just press **Enter** - it's optional Streamlit analytics

### Port Already in Use

If you see "Address already in use":
```bash
# Kill any old Streamlit processes, then try again
```

### API Errors

Make sure you entered your OpenRouter API key in the sidebar!

---

## 💡 Pro Tips

1. **Start Small**: Create 1 book with 5 chapters first
2. **Use Presets**: "cost_optimized" saves ~70% on API costs
3. **Enable Lore DB**: Add Pinecone key for better consistency
4. **Save Often**: Projects auto-save to `output/` directory
5. **Check Analytics**: See word counts and prose breakdowns

---

## 📚 Documentation

- **UI Guide**: `UI_README.md`
- **Pipeline Docs**: `README.md`
- **Prose Structure**: `PROSE_STRUCTURE.md`
- **Model Config**: `example_custom_models.py`

---

## 🎯 Ready to Start?

### Quick Start:
1. **Double-click**: `launch_ui.bat`
2. **Press Enter** when asked for email
3. **Browser opens** automatically
4. **Enter API key** in sidebar
5. **Create project** → Run pipeline → Export!

---

**Enjoy creating your novel! 📚✨**
