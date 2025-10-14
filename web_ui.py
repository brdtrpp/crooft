"""
Fiction Pipeline Web UI
A Streamlit-based interface for the fiction generation pipeline
"""

import os
import sys
import builtins

# Fix Windows console encoding for emoji/UTF-8 characters
# Set environment variables BEFORE any imports that might use them
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'

    # Monkey-patch print to handle encoding errors gracefully
    _original_print = builtins.print
    def safe_print(*args, **kwargs):
        """Print that safely handles encoding errors on Windows"""
        try:
            _original_print(*args, **kwargs)
        except UnicodeEncodeError:
            # If encoding fails, convert to ASCII with replacement
            safe_args = []
            for arg in args:
                if isinstance(arg, str):
                    safe_args.append(arg.encode('ascii', errors='replace').decode('ascii'))
                else:
                    safe_args.append(arg)
            kwargs.pop('file', None)  # Remove file kwarg if present
            _original_print(*safe_args, **kwargs)
        except Exception:
            # Silently ignore other print errors in web UI context
            pass
    builtins.print = safe_print

import streamlit as st
import json
import hmac
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if "passwords" in st.secrets and st.session_state["username"] in st.secrets["passwords"]:
            if hmac.compare_digest(
                st.session_state["password"],
                st.secrets["passwords"][st.session_state["username"]],
            ):
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # Don't store password
                return
        st.session_state["password_correct"] = False

    # Return True if password already validated or if no authentication is configured
    if st.session_state.get("password_correct", False):
        return True

    # Skip authentication if no passwords configured (for local development)
    if "passwords" not in st.secrets:
        return True

    # Show login form
    st.markdown("## 🔐 Fiction Pipeline Login")
    st.text_input("Username", key="username")
    st.text_input("Password", type="password", key="password", on_change=password_entered)
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 User not known or password incorrect")
    return False

# Import existing pipeline (no code changes needed)
from pipeline import FictionPipeline, create_project_from_concept
from models.schema import FictionProject, Metadata, Series, Lore
from utils.state_manager import StateManager

# Page config
st.set_page_config(
    page_title="Fiction Pipeline",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check authentication before showing any content
if not check_password():
    st.stop()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .status-running {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
    }
    .status-complete {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
    }
    .status-error {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
    }

    /* Streamlined style guide section */
    .style-guide-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
    }

    /* Better spacing for form elements */
    .stSelectbox, .stFileUploader {
        margin-bottom: 0.5rem;
    }

    /* Compact button styling */
    .stButton button {
        font-weight: 500;
    }

    /* Info text styling */
    .stCaption {
        font-size: 0.85rem;
        color: #6c757d;
        margin-top: 0.25rem;
    }

    /* Sidebar selectbox - make it more prominent */
    section[data-testid="stSidebar"] .stSelectbox {
        border-radius: 0.5rem;
        padding: 0.25rem;
    }

    /* Cleaner section dividers */
    section[data-testid="stSidebar"] hr {
        margin: 1rem 0;
        border-color: #dee2e6;
    }

    /* Sidebar headings */
    section[data-testid="stSidebar"] h2 {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    section[data-testid="stSidebar"] h3 {
        font-size: 1.1rem;
        font-weight: 500;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'project' not in st.session_state:
    st.session_state.project = None
if 'pipeline' not in st.session_state:
    st.session_state.pipeline = None
if 'running' not in st.session_state:
    st.session_state.running = False
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'auto_loaded' not in st.session_state:
    st.session_state.auto_loaded = False

# Auto-load last project on startup
if not st.session_state.auto_loaded and st.session_state.project is None:
    output_dir = "output"
    if os.path.exists(output_dir):
        json_files = [f for f in os.listdir(output_dir) if f.endswith("_state.json")]
        if json_files:
            # Get most recently modified project
            latest_file = max(json_files, key=lambda f: os.path.getmtime(os.path.join(output_dir, f)))
            try:
                file_path = os.path.join(output_dir, latest_file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                st.session_state.project = FictionProject(**project_data)
            except:
                pass  # Silently fail if project can't be loaded
    st.session_state.auto_loaded = True

# Sidebar
with st.sidebar:
    st.markdown("## 📚 Fiction Pipeline")
    st.markdown("---")

    # Navigation with selectbox (cleaner than radio buttons)
    page = st.selectbox(
        "📍 Navigation",
        ["Home", "New Project", "Load Project", "Project Manager", "Stage Viewer", "Step-by-Step", "Prose Reader", "Editing Suite", "Chat", "Settings", "Agent Config", "Analytics", "Export"],
        label_visibility="visible"
    )

    st.markdown("---")

    # API Keys - Load from secrets (secure for deployment)
    st.markdown("### 🔑 API Configuration")

    try:
        # Try to load from Streamlit secrets first (for deployment)
        if "OPENROUTER_API_KEY" in st.secrets:
            openrouter_key = st.secrets["OPENROUTER_API_KEY"]
            pinecone_key = st.secrets.get("PINECONE_API_KEY", "")
            st.success("✅ API keys loaded from secure storage")
        else:
            # Fallback to environment variables (for local development)
            openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
            pinecone_key = os.getenv("PINECONE_API_KEY", "")
            if openrouter_key:
                st.info("ℹ️ Using API keys from environment")
            else:
                st.warning("⚠️ No API keys configured")

        # Set environment variables
        if openrouter_key:
            os.environ["OPENROUTER_API_KEY"] = openrouter_key
        if pinecone_key:
            os.environ["PINECONE_API_KEY"] = pinecone_key

    except Exception as e:
        st.error(f"⚠️ Error loading API keys: {str(e)}")
        openrouter_key = ""
        pinecone_key = ""

    # Optional: Developer override (hidden in expander)
    with st.expander("🔧 Developer Override", expanded=False):
        st.caption("For testing only - leave empty to use default keys")
        override_openrouter = st.text_input(
            "Override OpenRouter Key",
            type="password",
            help="Leave empty to use default"
        )
        override_pinecone = st.text_input(
            "Override Pinecone Key",
            type="password",
            help="Leave empty to use default"
        )

        if override_openrouter:
            openrouter_key = override_openrouter
            os.environ["OPENROUTER_API_KEY"] = override_openrouter
            st.caption("✓ Using override for OpenRouter")
        if override_pinecone:
            pinecone_key = override_pinecone
            os.environ["PINECONE_API_KEY"] = override_pinecone
            st.caption("✓ Using override for Pinecone")

    st.markdown("---")

    # Global Model Configuration (available across all pages)
    st.markdown("### ⚙️ Model Configuration")

    preset = st.selectbox(
        "Preset",
        [
            "balanced",
            "creative",
            "precise",
            "cost_optimized",
            "premium",
            "balanced_nsfw",
            "creative_nsfw",
            "precise_nsfw",
            "cost_optimized_nsfw",
            "premium_nsfw"
        ],
        index=9,  # Default to premium_nsfw
        help="Standard presets use Claude/Gemini. NSFW presets use uncensored models for prose generation."
    )

    use_lore_db = st.checkbox("Enable Lore Vector Database", value=bool(pinecone_key))

    # Show current model configuration
    with st.expander("📋 View Current Model Config", expanded=False):
        from utils.model_config import ModelConfig
        preset_config = ModelConfig.get_presets().get(preset, {})

        if preset_config:
            st.caption(f"**Preset: {preset}**")
            for agent, config in preset_config.items():
                model_name = config.get('model', 'anthropic/claude-3.5-sonnet')
                temp = config.get('temperature', 0.7)
                st.text(f"{agent:12} → {model_name:40} (temp={temp})")
        else:
            st.caption("Using default configuration")

    st.markdown("---")

    # Current project status
    st.markdown("### 📂 Current Project")
    if 'project' in st.session_state and st.session_state.project:
        project = st.session_state.project
        st.success(f"✅ **Loaded**")
        st.caption(f"**Title:** {project.series.title}")
        st.caption(f"**ID:** {project.metadata.project_id}")
        st.caption(f"**Stage:** {project.metadata.processing_stage}")
        st.caption(f"**Books:** {len(project.series.books)}")
    else:
        st.warning("No project loaded")
        st.caption("Create or load a project to begin")

# Main content
if page == "Home":
    st.markdown('<p class="main-header">Fiction Generation Pipeline</p>', unsafe_allow_html=True)

    st.markdown("""
    ### Welcome to the AI-Powered Fiction Writing System

    This tool uses advanced AI agents to help you write complete novels from concept to finished manuscript.

    #### 🚀 Quick Start
    1. **New Project**: Create a new series from a concept
    2. **Configure**: Choose your AI models and presets
    3. **Generate**: Let the pipeline create your story
    4. **Export**: Download your manuscript

    #### ✨ Features
    - **Agent-Based Pipeline**: Specialized AI for each stage
    - **Quality Gates**: Automatic QA and lore validation
    - **Lore Management**: Consistent world-building
    - **Structured Output**: Paragraph-level dialogue tracking
    - **Model Customization**: Mix models per stage
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Pipeline Stages", "8")
    with col2:
        st.metric("Quality Gates", "Auto")
    with col3:
        st.metric("Lore Tracking", "✓" if pinecone_key else "JSON")

    st.markdown("---")

    if st.session_state.project:
        st.success(f"📖 Current Project: **{st.session_state.project.metadata.project_id}**")
        st.info(f"Series: {st.session_state.project.series.title}")

elif page == "New Project":
    st.markdown('<p class="main-header">Create New Project</p>', unsafe_allow_html=True)

    with st.form("new_project"):
        st.markdown("### Series Information")

        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("Series Title", placeholder="The Quantum Heist")
            # Genre selection with multi-select support
            all_genres = [
                # Standard Genres
                "Science Fiction",
                "Fantasy",
                "Urban Fantasy",
                "Dark Fantasy",
                "Epic Fantasy",
                "High Fantasy",
                "Low Fantasy",
                "Space Opera",
                "Cyberpunk",
                "Steampunk",
                "Dystopian",
                "Post-Apocalyptic",
                "Time Travel",
                "Alternate History",
                "Military Science Fiction",
                "Hard Science Fiction",
                "Sword and Sorcery",
                "Mystery",
                "Thriller",
                "Psychological Thriller",
                "Crime Fiction",
                "Detective Fiction",
                "Cozy Mystery",
                "Legal Thriller",
                "Spy Thriller",
                "Techno-Thriller",
                "Romance",
                "Contemporary Romance",
                "Paranormal Romance",
                "Romantic Suspense",
                "Historical Romance",
                "Regency Romance",
                "Horror",
                "Gothic Horror",
                "Psychological Horror",
                "Supernatural Horror",
                "Body Horror",
                "Literary Fiction",
                "Contemporary Fiction",
                "Historical Fiction",
                "Women's Fiction",
                "Coming of Age",
                "Action Adventure",
                "Military Fiction",
                "Western",
                "Pirate Adventure",
                "Young Adult",
                "Young Adult Fantasy",
                "Young Adult Science Fiction",
                "Young Adult Romance",
                "Middle Grade",
                "Humor",
                "Satire",
                "Comic Fantasy",
                "LitRPG",
                "GameLit",
                "Portal Fantasy",
                "Progression Fantasy",
                "Cultivation",
                "Superhero Fiction",
                "Magical Realism",
                # NSFW Genres (marked with 🔞)
                "🔞 Erotica",
                "🔞 Erotic Romance",
                "🔞 Erotic Fantasy",
                "🔞 Erotic Science Fiction",
                "🔞 Erotic Horror",
                "🔞 Erotic Thriller",
                "🔞 Dark Erotica",
                "🔞 Dark Romance",
                "🔞 BDSM Romance",
                "🔞 BDSM Erotica",
                "🔞 Paranormal Erotica",
                "🔞 Contemporary Erotica",
                "🔞 Historical Erotica",
                "🔞 Regency Erotica",
                "🔞 Victorian Erotica",
                "🔞 Medieval Erotica",
                "🔞 Harem",
                "🔞 Reverse Harem",
                "🔞 Poly Romance",
                "🔞 Monster Romance",
                "🔞 Alien Romance",
                "🔞 Shifter Romance",
                "🔞 Vampire Romance",
                "🔞 Dragon Romance",
                "🔞 Fae Romance",
                "🔞 Omegaverse",
                "🔞 Omegaverse (Alpha/Beta/Omega)",
                "🔞 Mpreg",
                "🔞 Futanari",
                "🔞 Tentacle Erotica",
                "🔞 Breeding Kink",
                "🔞 Age Gap Romance",
                "🔞 Taboo Romance",
                "🔞 Forbidden Romance",
                "🔞 Mafia Romance",
                "🔞 MC Romance (Motorcycle Club)",
                "🔞 Billionaire Romance",
                "🔞 Office Romance",
                "🔞 Teacher/Student",
                "🔞 Step-Family Romance",
                "🔞 Supernatural Romance",
                "🔞 Cyberpunk Erotica",
                "🔞 Space Opera Erotica",
                "🔞 Post-Apocalyptic Erotica",
                "🔞 Dystopian Erotica",
                "🔞 Urban Fantasy Erotica",
                "🔞 Paranormal Romance (Explicit)",
                "🔞 Gay Romance",
                "🔞 Lesbian Romance",
                "🔞 MMF Romance",
                "🔞 MFM Romance",
                "🔞 MMM Romance",
                "🔞 FFF Romance",
                "🔞 Bisexual Romance",
                "🔞 Trans Romance",
                "🔞 Non-Binary Romance",
                "🔞 Queer Erotica",
                "🔞 Menage Romance",
                "🔞 Group Romance",
                "🔞 Orgy Fiction",
                "🔞 MILF Romance",
                "🔞 Daddy Kink",
                "🔞 Sugar Daddy Romance",
                "🔞 Virgin Romance",
                "🔞 Innocent Romance",
                "🔞 Corruption Kink",
                "🔞 Power Exchange",
                "🔞 Dom/Sub Romance",
                "🔞 Master/Slave",
                "🔞 Slave Fiction",
                "🔞 Captive Romance",
                "🔞 Kidnapping Romance",
                "🔞 Enemies to Lovers (Explicit)",
                "🔞 Bully Romance",
                "🔞 Stalker Romance",
                "🔞 Non-Con/Dub-Con",
                "🔞 Coercion Romance",
                "🔞 Forced Marriage",
                "🔞 Arranged Marriage (Explicit)",
                "🔞 Breeding Programs",
                "🔞 Sex Worker Fiction",
                "🔞 Escort Romance",
                "🔞 Stripper Romance",
                "🔞 Cam Girl Fiction",
                "🔞 OnlyFans Fiction",
                "🔞 Adult Industry Fiction",
                "🔞 Rock Star Romance",
                "🔞 Celebrity Romance",
                "🔞 Sports Romance (Explicit)",
                "🔞 Military Romance (Explicit)",
                "🔞 Pirate Erotica",
                "🔞 Viking Romance",
                "🔞 Highlander Romance",
                "🔞 Western Erotica",
                "🔞 Cowboy Romance",
                "🔞 Yakuza Romance",
                "🔞 Gangster Romance",
                "🔞 Crime Lord Romance",
                "🔞 Assassin Romance",
                "🔞 Hitman Romance",
                "🔞 Mercenary Romance",
                "🔞 Bounty Hunter Romance",
                "🔞 Royalty Erotica",
                "🔞 Prince/Princess Romance",
                "🔞 King/Queen Romance",
                "🔞 Noble Romance",
                "🔞 Medieval Romance (Explicit)",
                "🔞 Knight Romance",
                "🔞 Gladiator Romance",
                "🔞 Barbarian Romance",
                "🔞 Orc Romance",
                "🔞 Demon Romance",
                "🔞 Angel Romance",
                "🔞 God/Goddess Romance",
                "🔞 Mythology Erotica",
                "🔞 Sci-Fi Breeding",
                "🔞 Alien Abduction Romance",
                "🔞 AI Romance",
                "🔞 Android/Cyborg Romance",
                "🔞 Clone Romance",
                "🔞 Genetic Engineering Erotica",
                "🔞 Medical Kink",
                "🔞 Doctor/Patient",
                "🔞 Nurse Romance",
                "🔞 Therapist Romance",
                "🔞 Boss/Employee",
                "🔞 CEO Romance",
                "🔞 Secretary Romance",
                "🔞 Workplace Romance (Explicit)",
                "🔞 College Romance (18+)",
                "🔞 Professor/Student (18+)",
                "🔞 Academy Romance (Explicit)",
                "🔞 Magic Academy Erotica",
                "🔞 Superhero Erotica",
                "🔞 Villain Romance",
                "🔞 Anti-Hero Romance",
                "🔞 Monster Girl",
                "🔞 Monster Boy",
                "🔞 Naga Romance",
                "🔞 Centaur Romance",
                "🔞 Minotaur Romance",
                "🔞 Werewolf Romance (Explicit)",
                "🔞 Bear Shifter Romance",
                "🔞 Cat Shifter Romance",
                "🔞 Dinosaur Shifter Romance",
                "🔞 Exotic Shifter Romance",
                "🔞 Merman/Mermaid Romance",
                "🔞 Siren Romance",
                "🔞 Succubus/Incubus",
                "🔞 Witch Romance",
                "🔞 Warlock Romance",
                "🔞 Necromancer Romance",
                "🔞 Blood Play",
                "🔞 Vampire Feeding Kink",
                "🔞 Size Difference",
                "🔞 Size Kink (Giant/Tiny)",
                "🔞 Macro/Micro",
                "🔞 Vore Fiction",
                "🔞 Pregnancy Romance",
                "🔞 Lactation Kink",
                "🔞 Exhibitionism",
                "🔞 Voyeurism",
                "🔞 Public Sex",
                "🔞 Cuckolding",
                "🔞 Wife Sharing",
                "🔞 Swinging",
                "🔞 Open Relationship Fiction",
                "🔞 Cheating Romance",
                "🔞 Affair Fiction",
                "🔞 Second Chance Romance (Explicit)",
                "🔞 Reunion Romance (Explicit)",
                "🔞 Friends to Lovers (Explicit)",
                "🔞 Best Friend's Sibling",
                "🔞 Brother's Best Friend",
                "🔞 Single Parent Romance (Explicit)",
                "🔞 Nanny Romance",
                "🔞 Bodyguard Romance (Explicit)",
                "🔞 Protector Romance",
                "🔞 Rescue Romance",
                "🔞 Survival Romance (Explicit)",
                "🔞 Apocalypse Erotica",
                "🔞 Zombie Apocalypse Romance",
                "🔞 Wasteland Romance",
                "🔞 Space Station Erotica",
                "🔞 Spaceship Romance",
                "🔞 Colony Romance",
                "🔞 Time Travel Erotica",
                "🔞 Historical Time Travel Romance",
                "🔞 Reincarnation Romance",
                "🔞 Soul Mate Romance (Explicit)",
                "🔞 Fated Mates",
                "🔞 Mate Bond Fiction",
                "🔞 Scent Kink",
                "🔞 Heat Cycles",
                "🔞 Rut Fiction",
                "🔞 Pack Dynamics",
                "🔞 Claiming/Marking",
                "🔞 Bonding Fiction",
                "🔞 Twin Flames",
                "🔞 Multiple Mates",
                "🔞 Shared Mates",
                "🔞 Alien Mate Programs",
                "🔞 Interspecies Romance",
                "🔞 Cross-Species Breeding",
                "🔞 Xenophilia",
                "🔞 Monster Breeding",
                "🔞 Fantasy Breeding",
                "🔞 Dragon Hoard Romance",
                "🔞 Treasure Guardian Romance",
                "🔞 Dungeon Erotica",
                "🔞 LitRPG Erotica",
                "🔞 GameLit Romance",
                "🔞 Virtual Reality Erotica",
                "🔞 MMORPG Romance",
                "🔞 Isekai Erotica",
                "🔞 Transported to Another World Romance",
                "🔞 Cultivation Romance (Explicit)",
                "🔞 Wuxia Erotica",
                "🔞 Xianxia Romance",
                "🔞 Dual Cultivation",
                "🔞 Energy Transfer Romance",
                "🔞 Magic Sex",
                "🔞 Sex Magic",
                "🔞 Tantric Romance",
                "🔞 Ritual Sex",
                "🔞 Sacrifice Romance",
                "🔞 Religious Erotica",
                "🔞 Cult Romance",
                "🔞 Secret Society Romance",
                "🔞 Illuminati Romance",
                "🔞 Conspiracy Erotica",
                "🔞 Spy Romance (Explicit)",
                "🔞 Espionage Erotica",
                "🔞 Assassin's Creed Style Romance",
                "🔞 Thief Romance",
                "🔞 Heist Romance",
                "🔞 Con Artist Romance",
                "🔞 Criminal Romance",
                "🔞 Prison Romance",
                "🔞 Captivity Fiction (Explicit)",
                "🔞 Island Romance (Explicit)",
                "🔞 Stranded Romance",
                "🔞 Survival Island Erotica",
                "🔞 Treasure Island Romance",
                "🔞 Deserted Island Fiction"
            ]

            selected_genres = st.multiselect(
                "Genre(s) - Select one or blend multiple",
                all_genres,
                default=["Fantasy"],
                help="Select one genre or combine multiple for crossover fiction. 🔞 = Mature/NSFW content"
            )

            # Create genre string from selection
            if selected_genres:
                genre = " / ".join(selected_genres)
            else:
                genre = "Fantasy"  # Default fallback

        with col2:
            target_audience = st.selectbox("Target Audience", ["adult", "young adult", "middle grade"])
            num_books = st.number_input("Number of Books", min_value=1, max_value=25, value=1)
            target_word_count = st.number_input("Target Word Count per Book", min_value=50000, max_value=200000, value=100000, step=10000)
            chapters_per_book_range = st.slider("Chapters per Book (range)", min_value=5, max_value=50, value=(20, 26), help="Each book will have a chapter count within this range")

        premise = st.text_area(
            "Series Premise",
            placeholder="A team of specialists must steal an impossible artifact from a time-locked vault.",
            height=100
        )

        # Style Guide Selection
        st.markdown("### 📝 Prose Style Guide (Optional)")

        # Simple text area for copy/paste
        style_guide = st.text_area(
            "Paste or type your style guide",
            value="",
            height=200,
            placeholder="""Paste your style guide here, or type directly.

Examples:
- Write in the style of Brandon Sanderson with clear magic system explanations
- Use short, punchy sentences for action scenes
- Include vivid sensory details, especially smell and touch
- Favor showing over telling
- Character dialogue should be sharp and witty
- Avoid adverbs in dialogue tags

Leave blank to use default prose generation.""",
            help="Define the prose style for your series. This will be used throughout generation.",
            key="style_guide_text_input"
        )

        # Show word count if content exists
        if style_guide.strip():
            st.caption(f"📊 {len(style_guide.split())} words • {len(style_guide)} characters")

        submit = st.form_submit_button("🚀 Create Project", type="primary")

        if submit:
            if not title or not premise:
                st.error("Please fill in Title and Premise")
            elif not openrouter_key:
                st.error("OpenRouter API Key required")
            elif not selected_genres:
                st.error("Please select at least one genre")
            else:
                with st.spinner("Creating project..."):
                    try:
                        # Generate project_id from title
                        import re
                        # Create slug from title
                        slug = title.lower()
                        slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special chars
                        slug = re.sub(r'[-\s]+', '_', slug)  # Replace spaces/hyphens with underscores
                        slug = slug.strip('_')  # Remove leading/trailing underscores
                        # Add short date for uniqueness
                        date_str = datetime.now().strftime('%Y%m%d')
                        project_id = f"{slug}_{date_str}"

                        # Create project
                        project = FictionProject(
                            metadata=Metadata(
                                last_updated=datetime.now(),
                                last_updated_by="WebUI",
                                processing_stage="series",
                                status="draft",
                                project_id=project_id,
                                iteration=1
                            ),
                            series=Series(
                                title=title,
                                premise=premise,
                                genre=genre,
                                target_audience=target_audience,
                                themes=[],
                                persistent_threads=[],
                                lore=Lore(),
                                books=[],
                                style_guide=style_guide
                            )
                        )

                        # Store requirements in project metadata as custom fields
                        chapters_range_str = f"{chapters_per_book_range[0]}-{chapters_per_book_range[1]}"
                        project.metadata.project_id = f"{project_id}__{num_books}books_{chapters_range_str}ch_{target_word_count}w"

                        # Initialize pipeline
                        pipeline = FictionPipeline(
                            project_id=project_id,
                            output_dir="output",
                            openrouter_api_key=openrouter_key,
                            use_lore_db=use_lore_db,
                            preset=preset,
                            requirements={
                                "num_books": num_books,
                                "chapters_per_book_range": chapters_per_book_range,
                                "target_word_count": target_word_count
                            }
                        )

                        # Save project to disk so it shows up in Project Manager
                        pipeline.state_manager.save_state(project, "initial")

                        st.session_state.project = project
                        st.session_state.pipeline = pipeline

                        st.success(f"✅ Project created: {project_id}")
                        st.success(f"✅ Project saved to: output/{project.metadata.project_id}_state.json")
                        st.info("Go to 🎯 Step-by-Step or ⚙️ Settings to run the pipeline!")

                    except Exception as e:
                        st.error(f"Error creating project: {e}")

elif page == "Load Project":
    st.markdown('<p class="main-header">Load Existing Project</p>', unsafe_allow_html=True)

    output_dir = "output"
    if os.path.exists(output_dir):
        json_files = [f for f in os.listdir(output_dir) if f.endswith("_state.json")]

        if json_files:
            selected_file = st.selectbox("Select Project", json_files)

            if st.button("📂 Load Project"):
                with st.spinner("Loading..."):
                    try:
                        file_path = os.path.join(output_dir, selected_file)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            project_data = json.load(f)

                        project = FictionProject(**project_data)
                        st.session_state.project = project

                        # Recreate pipeline for loaded project
                        pipeline = FictionPipeline(
                            project_id=project_data['metadata'].get('project_id'),
                            output_dir=output_dir,
                            openrouter_api_key=openrouter_key,
                            preset=preset,
                            use_lore_db=use_lore_db
                        )
                        st.session_state.pipeline = pipeline

                        st.success(f"✅ Loaded: {project.metadata.project_id}")
                        st.info("💡 Go to **🎯 Step-by-Step** to continue working on this project")
                        st.json(project_data['metadata'])

                    except Exception as e:
                        st.error(f"Error loading project: {e}")
        else:
            st.info("No saved projects found in output/")
    else:
        st.warning("Output directory not found")

elif page == "Project Manager":
    st.markdown('<p class="main-header">Project Manager</p>', unsafe_allow_html=True)

    output_dir = "output"
    if not os.path.exists(output_dir):
        st.warning("Output directory not found")
    else:
        # Get all project state files (ending with _state.json)
        all_files = os.listdir(output_dir)
        state_files = [f for f in all_files if f.endswith("_state.json")]

        if not state_files:
            st.info("No projects found in output/")
        else:
            st.markdown(f"### {len(state_files)} Project(s)")

            # Load all project data
            projects_data = []
            for state_file_name in sorted(state_files):
                state_file = os.path.join(output_dir, state_file_name)
                project_name = state_file_name.replace("_state.json", "")

                try:
                    with open(state_file, 'r', encoding='utf-8') as f:
                        project_data = json.load(f)

                    metadata = project_data.get('metadata', {})
                    series = project_data.get('series', {})
                    books = len(series.get('books', []))
                    chapters = sum(len(book.get('chapters', [])) for book in series.get('books', []))

                    projects_data.append({
                        'file_name': state_file_name,
                        'project_name': project_name,
                        'title': series.get('title', 'N/A'),
                        'stage': metadata.get('processing_stage', 'N/A'),
                        'status': metadata.get('status', 'N/A'),
                        'books': books,
                        'chapters': chapters,
                        'last_updated': metadata.get('last_updated', 'N/A'),
                        'project_data': project_data,
                        'metadata': metadata,
                        'series': series
                    })
                except Exception as e:
                    projects_data.append({
                        'file_name': state_file_name,
                        'project_name': project_name,
                        'title': f'⚠️ Error loading',
                        'stage': '-',
                        'status': '-',
                        'books': 0,
                        'chapters': 0,
                        'last_updated': '-',
                        'error': str(e)
                    })

            # Streamlined table view
            for idx, proj in enumerate(projects_data):
                project_name = proj['project_name']

                # Single compact row
                col1, col2, col3 = st.columns([6, 3, 3])

                with col1:
                    st.markdown(f"**{proj['title']}** · `{proj['stage']}` · {proj['books']}B / {proj['chapters']}Ch")

                with col2:
                    load_btn, view_btn = st.columns(2)
                    with load_btn:
                        if st.button("📂 Load", key=f"load_{idx}", use_container_width=True):
                            if 'project_data' in proj:
                                try:
                                    project = FictionProject(**proj['project_data'])
                                    st.session_state.project = project
                                    pipeline = FictionPipeline(
                                        project_id=proj['metadata'].get('project_id'),
                                        output_dir=output_dir,
                                        openrouter_api_key=openrouter_key,
                                        preset=preset,
                                        use_lore_db=use_lore_db
                                    )
                                    st.session_state.pipeline = pipeline
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

                    with view_btn:
                        if st.button("👁️", key=f"view_{idx}", use_container_width=True):
                            st.session_state[f'viewing_{project_name}'] = not st.session_state.get(f'viewing_{project_name}', False)
                            st.rerun()

                with col3:
                    edit_btn, del_btn = st.columns(2)
                    with edit_btn:
                        if st.button("✏️", key=f"edit_{idx}", use_container_width=True):
                            st.session_state[f'editing_{project_name}'] = not st.session_state.get(f'editing_{project_name}', False)
                            st.rerun()

                    with del_btn:
                        if st.button("🗑️", key=f"del_{idx}", type="secondary", use_container_width=True):
                            st.session_state[f'confirm_delete_{project_name}'] = True
                            st.rerun()

                # Expandable sections (only shown when toggled)
                if st.session_state.get(f'viewing_{project_name}'):
                    st.caption(f"📄 **File:** {proj['file_name']}")
                    st.caption(f"📊 **Status:** {proj['status']} | **Last Updated:** {proj['last_updated']}")

                if st.session_state.get(f'editing_{project_name}'):
                    with st.form(key=f"edit_form_{idx}"):
                        new_title = st.text_input("Title", value=proj['series'].get('title', ''))
                        new_premise = st.text_area("Premise", value=proj['series'].get('premise', ''), height=100)

                        save_col, cancel_col = st.columns(2)
                        if save_col.form_submit_button("💾 Save", type="primary", use_container_width=True):
                            try:
                                proj['project_data']['series']['title'] = new_title
                                proj['project_data']['series']['premise'] = new_premise
                                proj['project_data']['metadata']['last_updated'] = datetime.now().isoformat()
                                with open(os.path.join(output_dir, proj['file_name']), 'w', encoding='utf-8') as f:
                                    json.dump(proj['project_data'], f, indent=2)
                                st.session_state[f'editing_{project_name}'] = False
                                st.success("✅ Saved!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

                        if cancel_col.form_submit_button("❌ Cancel", use_container_width=True):
                            st.session_state[f'editing_{project_name}'] = False
                            st.rerun()

                if st.session_state.get(f'confirm_delete_{project_name}'):
                    st.error(f"⚠️ Delete **{proj['title']}**?")
                    yes_col, no_col = st.columns(2)
                    if yes_col.button("✅ Yes, Delete", key=f"confirm_yes_{idx}", type="primary", use_container_width=True):
                        try:
                            os.remove(os.path.join(output_dir, proj['file_name']))
                            for f in all_files:
                                if f.startswith(project_name) and f != proj['file_name']:
                                    try:
                                        os.remove(os.path.join(output_dir, f))
                                    except:
                                        pass
                            if st.session_state.get('project') and 'metadata' in proj:
                                if st.session_state.project.metadata.project_id == proj['metadata'].get('project_id'):
                                    st.session_state.project = None
                                    st.session_state.pipeline = None
                            st.session_state[f'confirm_delete_{project_name}'] = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

                    if no_col.button("❌ Cancel", key=f"confirm_no_{idx}", use_container_width=True):
                        st.session_state[f'confirm_delete_{project_name}'] = False
                        st.rerun()

                st.divider()

            # Bulk actions
            st.markdown("---")
            st.markdown("### Bulk Actions")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("📊 Export Project List"):
                    project_list = []
                    for state_file_name in state_files:
                        state_file = os.path.join(output_dir, state_file_name)
                        try:
                            with open(state_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            project_list.append({
                                "filename": state_file_name,
                                "project_name": state_file_name.replace("_state.json", ""),
                                "title": data.get('series', {}).get('title'),
                                "stage": data.get('metadata', {}).get('processing_stage'),
                                "status": data.get('metadata', {}).get('status'),
                                "books": len(data.get('series', {}).get('books', [])),
                                "chapters": sum(len(book.get('chapters', [])) for book in data.get('series', {}).get('books', [])),
                                "last_updated": data.get('metadata', {}).get('last_updated')
                            })
                        except:
                            pass

                    if project_list:
                        st.download_button(
                            "💾 Download as JSON",
                            data=json.dumps(project_list, indent=2),
                            file_name=f"project_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )

            with col2:
                if st.button("🗑️ Delete All Projects", type="secondary"):
                    st.session_state['confirm_delete_all'] = True

            # Confirm delete all
            if st.session_state.get('confirm_delete_all'):
                st.error("⚠️ **DELETE ALL PROJECTS**")
                st.markdown("This will delete ALL projects and checkpoints. This CANNOT be undone!")

                col1, col2 = st.columns(2)
                if col1.button("✅ Yes, Delete Everything", key="confirm_delete_all_yes", type="primary"):
                    try:
                        deleted = 0
                        for f in all_files:
                            if f.endswith('.json'):
                                os.remove(os.path.join(output_dir, f))
                                deleted += 1
                        st.success(f"✅ Deleted {deleted} file(s)")
                        st.session_state.project = None
                        st.session_state.pipeline = None
                        st.session_state['confirm_delete_all'] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

                if col2.button("❌ Cancel", key="confirm_delete_all_no"):
                    st.session_state['confirm_delete_all'] = False
                    st.rerun()

elif page == "Stage Viewer":
    st.markdown('<p class="main-header">📊 Stage Viewer</p>', unsafe_allow_html=True)

    if st.session_state.project is None:
        st.warning("⚠️ No project loaded. Please create or load a project first.")
    else:
        project = st.session_state.project

        # Project overview
        st.markdown("### 📂 Project Overview")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Series", project.series.title)
        with col2:
            st.metric("Stage", project.metadata.processing_stage)
        with col3:
            st.metric("Status", project.metadata.status)
        with col4:
            st.metric("Books", len(project.series.books))

        st.markdown("---")

        # Stage selector
        stage_options = [
            "Series Outline",
            "Lore Database",
            "Book Outlines",
            "Chapter Outlines",
            "Scene Outlines",
            "Beat Development",
            "Prose Content",
            "QA Reports",
            "Editorial Reports"
        ]

        selected_stage = st.selectbox("Select Stage to View", stage_options)

        st.markdown("---")

        # Display selected stage data
        if selected_stage == "Series Outline":
            st.markdown("### 📖 Series Outline")

            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Title:** {project.series.title}")
                st.markdown(f"**Genre:** {project.series.genre}")
                if project.series.logline:
                    st.markdown(f"**Logline:** {project.series.logline}")
                st.markdown(f"**Target Audience:** {project.series.target_audience}")

            with col2:
                if project.series.themes:
                    st.markdown("**Themes:**")
                    for theme in project.series.themes:
                        st.markdown(f"- {theme}")

            st.markdown("#### Premise")
            st.text_area("Series Premise", project.series.premise, height=150, disabled=True, key="series_premise_view")

            if project.series.subgenres:
                st.markdown("#### Subgenres")
                st.write(", ".join(project.series.subgenres))

            if project.series.universe_principles:
                st.markdown("#### Universe Principles")
                for i, principle in enumerate(project.series.universe_principles):
                    with st.expander(f"Principle {i+1}"):
                        st.json(principle)

            if project.series.persistent_threads:
                st.markdown("#### Persistent Story Threads")
                for i, thread in enumerate(project.series.persistent_threads):
                    with st.expander(f"Thread {i+1}"):
                        st.json(thread)

        elif selected_stage == "Lore Database":
            st.markdown("### 🗺️ Lore Database")

            lore = project.series.lore

            tab1, tab2, tab3 = st.tabs(["Characters", "Locations", "World Elements"])

            with tab1:
                st.markdown(f"**Total Characters:** {len(lore.characters)}")
                for char in lore.characters:
                    with st.expander(f"👤 {char.name} - {char.role}"):
                        st.markdown(f"**Description:** {char.description}")
                        if char.traits:
                            st.markdown("**Traits:**")
                            for trait in char.traits:
                                st.markdown(f"- {trait}")
                        if char.relationships:
                            st.markdown("**Relationships:**")
                            for rel in char.relationships:
                                if isinstance(rel, dict):
                                    st.markdown(f"- {rel.get('name', 'Unknown')}: {rel.get('type', 'Unknown')}")
                                else:
                                    st.markdown(f"- {rel}")

            with tab2:
                st.markdown(f"**Total Locations:** {len(lore.locations)}")
                for loc in lore.locations:
                    with st.expander(f"📍 {loc.name}"):
                        st.markdown(f"**Description:** {loc.description}")
                        st.markdown(f"**Significance:** {loc.significance}")

            with tab3:
                st.markdown(f"**Total World Elements:** {len(lore.world_elements)}")
                for elem in lore.world_elements:
                    with st.expander(f"✨ {elem.name} ({elem.type})"):
                        st.markdown(f"**Description:** {elem.description}")
                        if elem.rules:
                            st.markdown("**Rules:**")
                            for rule in elem.rules:
                                st.markdown(f"- {rule}")

        elif selected_stage == "Book Outlines":
            st.markdown("### 📚 Book Outlines")

            if not project.series.books:
                st.info("No books outlined yet.")
            else:
                # Book selector
                book_titles = [f"Book {book.book_number}: {book.title or 'Untitled'}" for book in project.series.books]
                selected_book_idx = st.selectbox("Select Book", range(len(project.series.books)), format_func=lambda i: book_titles[i])

                book = project.series.books[selected_book_idx]

                st.markdown(f"### {book.title or 'Untitled'}")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Status", book.status)
                with col2:
                    st.metric("Target Words", f"{book.target_word_count:,}")
                with col3:
                    st.metric("Current Words", f"{book.current_word_count:,}")

                st.markdown("#### Premise")
                st.text_area("Book Premise", book.premise, height=150, disabled=True, key=f"book_{book.book_number}_premise")

                col1, col2 = st.columns(2)
                with col1:
                    if book.protagonist_goal:
                        st.markdown("**Protagonist Goal:**")
                        st.write(book.protagonist_goal)
                    if book.antagonistic_force:
                        st.markdown("**Antagonistic Force:**")
                        st.write(book.antagonistic_force)

                with col2:
                    if book.themes:
                        st.markdown("**Themes:**")
                        for theme in book.themes:
                            st.markdown(f"- {theme}")
                    if book.unique_hook:
                        st.markdown("**Unique Hook:**")
                        st.write(book.unique_hook)

                if book.act_structure:
                    st.markdown("#### Act Structure")
                    for act_name, act in book.act_structure.items():
                        with st.expander(f"{act_name} - {act.percentage}% ({act.word_target:,} words)"):
                            st.markdown(f"**Summary:** {act.summary}")
                            st.markdown(f"**Ending Hook:** {act.ending_hook}")
                            if act.key_events:
                                st.markdown("**Key Events:**")
                                for event in act.key_events:
                                    st.markdown(f"- {event}")
                            if act.midpoint:
                                st.markdown(f"**Midpoint:** {act.midpoint}")
                            if act.climax:
                                st.markdown(f"**Climax:** {act.climax}")
                            if act.resolution:
                                st.markdown(f"**Resolution:** {act.resolution}")

                if book.character_arcs:
                    st.markdown("#### Character Arcs")
                    for arc in book.character_arcs:
                        with st.expander(f"👤 {arc.character_name}"):
                            st.markdown(f"**Starting State:** {arc.starting_state}")
                            st.markdown(f"**Ending State:** {arc.ending_state}")
                            st.markdown(f"**Transformation:** {arc.transformation}")
                            if arc.key_moments:
                                st.markdown("**Key Moments:**")
                                for moment in arc.key_moments:
                                    st.markdown(f"- {moment}")

        elif selected_stage == "Chapter Outlines":
            st.markdown("### 📑 Chapter Outlines")

            if not project.series.books:
                st.info("No books available yet.")
            else:
                # Book selector
                book_titles = [f"Book {book.book_number}: {book.title or 'Untitled'}" for book in project.series.books]
                selected_book_idx = st.selectbox("Select Book", range(len(project.series.books)), format_func=lambda i: book_titles[i], key="chapter_book_select")

                book = project.series.books[selected_book_idx]

                if not book.chapters:
                    st.info("No chapters outlined yet for this book.")
                else:
                    # Chapter selector
                    chapter_titles = [f"Chapter {ch.chapter_number}: {ch.title or 'Untitled'}" for ch in book.chapters]
                    selected_chapter_idx = st.selectbox("Select Chapter", range(len(book.chapters)), format_func=lambda i: chapter_titles[i])

                    chapter = book.chapters[selected_chapter_idx]

                    st.markdown(f"### Chapter {chapter.chapter_number}: {chapter.title or 'Untitled'}")

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Act", chapter.act)
                    with col2:
                        st.metric("Status", chapter.status)
                    with col3:
                        st.metric("Planned Words", f"{chapter.planned_word_count:,}")
                    with col4:
                        st.metric("Actual Words", f"{chapter.actual_word_count:,}")

                    st.markdown("#### Purpose")
                    st.write(chapter.purpose)

                    col1, col2 = st.columns(2)
                    with col1:
                        if chapter.plot_points:
                            st.markdown("**Plot Points:**")
                            for point in chapter.plot_points:
                                st.markdown(f"- {point}")

                        if chapter.themes:
                            st.markdown("**Themes:**")
                            for theme in chapter.themes:
                                st.markdown(f"- {theme}")

                    with col2:
                        st.markdown("**Character Focus:**")
                        st.markdown(f"- POV: {chapter.character_focus.pov}")
                        if chapter.character_focus.present:
                            st.markdown(f"- Present: {', '.join(chapter.character_focus.present)}")

                        st.markdown("**Setting:**")
                        if chapter.setting.location:
                            st.markdown(f"- Location: {chapter.setting.location}")
                        if chapter.setting.time:
                            st.markdown(f"- Time: {chapter.setting.time}")
                        if chapter.setting.atmosphere:
                            st.markdown(f"- Atmosphere: {chapter.setting.atmosphere}")

                    if chapter.subplot_threads:
                        st.markdown("**Subplot Threads:**")
                        for thread in chapter.subplot_threads:
                            st.markdown(f"- {thread}")

        elif selected_stage == "Scene Outlines":
            st.markdown("### 🎬 Scene Outlines")

            if not project.series.books:
                st.info("No books available yet.")
            else:
                # Book selector
                book_titles = [f"Book {book.book_number}: {book.title or 'Untitled'}" for book in project.series.books]
                selected_book_idx = st.selectbox("Select Book", range(len(project.series.books)), format_func=lambda i: book_titles[i], key="scene_book_select")

                book = project.series.books[selected_book_idx]

                if not book.chapters:
                    st.info("No chapters available yet.")
                else:
                    # Chapter selector
                    chapter_titles = [f"Chapter {ch.chapter_number}: {ch.title or 'Untitled'}" for ch in book.chapters]
                    selected_chapter_idx = st.selectbox("Select Chapter", range(len(book.chapters)), format_func=lambda i: chapter_titles[i], key="scene_chapter_select")

                    chapter = book.chapters[selected_chapter_idx]

                    if not chapter.scenes:
                        st.info("No scenes developed yet for this chapter.")
                    else:
                        # Scene selector
                        scene_titles = [f"Scene {scene.scene_number}: {scene.title or 'Untitled'}" for scene in chapter.scenes]
                        selected_scene_idx = st.selectbox("Select Scene", range(len(chapter.scenes)), format_func=lambda i: scene_titles[i])

                        scene = chapter.scenes[selected_scene_idx]

                        st.markdown(f"### Scene {scene.scene_number}: {scene.title or 'Untitled'}")

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Type", scene.scene_type)
                        with col2:
                            st.metric("POV", scene.pov)
                        with col3:
                            st.metric("Planned Words", f"{scene.planned_word_count:,}")
                        with col4:
                            st.metric("Actual Words", f"{scene.actual_word_count:,}")

                        st.markdown("#### Purpose")
                        st.write(scene.purpose)

                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Setting:**")
                            if scene.setting.location:
                                st.markdown(f"- Location: {scene.setting.location}")
                            if scene.setting.time:
                                st.markdown(f"- Time: {scene.setting.time}")
                            if scene.setting.atmosphere:
                                st.markdown(f"- Atmosphere: {scene.setting.atmosphere}")

                            if scene.characters_present:
                                st.markdown("**Characters Present:**")
                                st.write(", ".join(scene.characters_present))

                        with col2:
                            if scene.conflicts:
                                st.markdown("**Conflicts:**")
                                for conflict in scene.conflicts:
                                    st.markdown(f"- {conflict.type}: {conflict.description}")

                            if scene.turning_points:
                                st.markdown("**Turning Points:**")
                                for tp in scene.turning_points:
                                    st.markdown(f"- {tp}")

                        if scene.subplot_advancement:
                            st.markdown("**Subplot Advancement:**")
                            for subplot in scene.subplot_advancement:
                                st.markdown(f"- {subplot}")

                        if scene.theme_expression:
                            st.markdown("**Theme Expression:**")
                            for theme in scene.theme_expression:
                                st.markdown(f"- {theme}")

        elif selected_stage == "Beat Development":
            st.markdown("### 🎵 Beat Development")

            if not project.series.books:
                st.info("No books available yet.")
            else:
                # Navigation selectors
                book_titles = [f"Book {book.book_number}: {book.title or 'Untitled'}" for book in project.series.books]
                selected_book_idx = st.selectbox("Select Book", range(len(project.series.books)), format_func=lambda i: book_titles[i], key="beat_book_select")

                book = project.series.books[selected_book_idx]

                if not book.chapters:
                    st.info("No chapters available yet.")
                else:
                    chapter_titles = [f"Chapter {ch.chapter_number}: {ch.title or 'Untitled'}" for ch in book.chapters]
                    selected_chapter_idx = st.selectbox("Select Chapter", range(len(book.chapters)), format_func=lambda i: chapter_titles[i], key="beat_chapter_select")

                    chapter = book.chapters[selected_chapter_idx]

                    if not chapter.scenes:
                        st.info("No scenes available yet.")
                    else:
                        scene_titles = [f"Scene {scene.scene_number}: {scene.title or 'Untitled'}" for scene in chapter.scenes]
                        selected_scene_idx = st.selectbox("Select Scene", range(len(chapter.scenes)), format_func=lambda i: scene_titles[i], key="beat_scene_select")

                        scene = chapter.scenes[selected_scene_idx]

                        if not scene.beats:
                            st.info("No beats developed yet for this scene.")
                        else:
                            st.markdown(f"### Beats for Scene {scene.scene_number}")
                            st.markdown(f"**Total Beats:** {len(scene.beats)}")

                            for beat in scene.beats:
                                with st.expander(f"Beat {beat.beat_number} - {beat.emotional_tone}"):
                                    st.markdown(f"**Description:** {beat.description}")
                                    st.markdown(f"**Emotional Tone:** {beat.emotional_tone}")

                                    if beat.character_actions:
                                        st.markdown("**Character Actions:**")
                                        for action in beat.character_actions:
                                            st.markdown(f"- {action}")

                                    if beat.dialogue_summary:
                                        st.markdown(f"**Dialogue Summary:** {beat.dialogue_summary}")

                                    if beat.prose:
                                        st.markdown(f"**Prose Status:** {beat.prose.status}")
                                        st.markdown(f"**Word Count:** {beat.prose.word_count}")

        elif selected_stage == "Prose Content":
            st.markdown("### 📝 Prose Content")

            if not project.series.books:
                st.info("No books available yet.")
            else:
                # Navigation selectors
                book_titles = [f"Book {book.book_number}: {book.title or 'Untitled'}" for book in project.series.books]
                selected_book_idx = st.selectbox("Select Book", range(len(project.series.books)), format_func=lambda i: book_titles[i], key="prose_book_select")

                book = project.series.books[selected_book_idx]

                if not book.chapters:
                    st.info("No chapters available yet.")
                else:
                    chapter_titles = [f"Chapter {ch.chapter_number}: {ch.title or 'Untitled'}" for ch in book.chapters]
                    selected_chapter_idx = st.selectbox("Select Chapter", range(len(book.chapters)), format_func=lambda i: chapter_titles[i], key="prose_chapter_select")

                    chapter = book.chapters[selected_chapter_idx]

                    if not chapter.scenes:
                        st.info("No scenes available yet.")
                    else:
                        scene_titles = [f"Scene {scene.scene_number}: {scene.title or 'Untitled'}" for scene in chapter.scenes]
                        selected_scene_idx = st.selectbox("Select Scene", range(len(chapter.scenes)), format_func=lambda i: scene_titles[i], key="prose_scene_select")

                        scene = chapter.scenes[selected_scene_idx]

                        if not scene.beats:
                            st.info("No beats available yet.")
                        else:
                            beat_titles = [f"Beat {beat.beat_number}" for beat in scene.beats]
                            selected_beat_idx = st.selectbox("Select Beat", range(len(scene.beats)), format_func=lambda i: beat_titles[i])

                            beat = scene.beats[selected_beat_idx]

                            if not beat.prose or not beat.prose.content:
                                st.info("No prose generated yet for this beat.")
                            else:
                                prose = beat.prose

                                st.markdown(f"### Beat {beat.beat_number} Prose")

                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Status", prose.status)
                                with col2:
                                    st.metric("Word Count", prose.word_count)
                                with col3:
                                    st.metric("Draft Version", prose.draft_version)

                                st.markdown("---")

                                if prose.paragraphs:
                                    st.markdown(f"**Paragraphs:** {len(prose.paragraphs)}")
                                    for para in prose.paragraphs:
                                        with st.expander(f"Paragraph {para.paragraph_number} ({para.paragraph_type})"):
                                            st.write(para.content)
                                            if para.dialogue_lines:
                                                st.markdown("**Dialogue:**")
                                                for line in para.dialogue_lines:
                                                    st.markdown(f"- **{line.speaker}:** {line.dialogue}")
                                                    if line.action:
                                                        st.caption(f"  _{line.action}_")
                                else:
                                    st.markdown("#### Content")
                                    st.text_area("Prose", prose.content, height=400, disabled=True, key=f"prose_{beat.beat_number}")

        elif selected_stage == "QA Reports":
            st.markdown("### ✅ QA Reports")

            if not project.qa_reports:
                st.info("No QA reports generated yet.")
            else:
                st.markdown(f"**Total Reports:** {len(project.qa_reports)}")

                for report in project.qa_reports:
                    with st.expander(f"QA Report - {report.scope} - {report.timestamp}"):
                        st.markdown(f"**Target:** {report.target_id}")
                        st.markdown(f"**Approval:** {report.approval}")

                        st.markdown("#### Scores")
                        score_cols = st.columns(len(report.scores))
                        for i, (key, value) in enumerate(report.scores.items()):
                            with score_cols[i]:
                                st.metric(key.replace('_', ' ').title(), f"{value}/10")

                        col1, col2 = st.columns(2)
                        with col1:
                            if report.strengths:
                                st.markdown("**Strengths:**")
                                for strength in report.strengths:
                                    st.markdown(f"✅ {strength}")

                        with col2:
                            if report.major_issues:
                                st.markdown("**Major Issues:**")
                                for issue in report.major_issues:
                                    st.markdown(f"⚠️ {issue}")

                        if report.revision_tasks:
                            st.markdown("**Revision Tasks:**")
                            for task in report.revision_tasks:
                                status_icon = "✅" if task.status == "completed" else "⏳"
                                st.markdown(f"{status_icon} [{task.priority}] {task.description}")

                        if report.reviewer_notes:
                            st.markdown("**Reviewer Notes:**")
                            st.write(report.reviewer_notes)

        elif selected_stage == "Editorial Reports":
            st.markdown("### 📋 Editorial Reports")

            if not project.editorial_reports:
                st.info("No editorial reports generated yet.")
            else:
                st.markdown(f"**Total Reports:** {len(project.editorial_reports)}")
                st.markdown(f"**Editorial Status:** {project.editorial_status}")

                for report in project.editorial_reports:
                    with st.expander(f"Editorial Report - {report.phase} - {report.timestamp}"):
                        st.markdown(f"**Reviewer:** {report.reviewer_agent}")
                        st.markdown(f"**Scope:** {report.scope}")
                        st.markdown(f"**Overall Score:** {report.overall_score}/10")
                        st.markdown(f"**Approval:** {report.approval}")

                        if report.developmental_issues:
                            st.markdown("#### Developmental Issues")
                            for issue in report.developmental_issues:
                                status_icon = "✅" if issue.status == "fixed" else "⚠️"
                                st.markdown(f"{status_icon} **[{issue.severity}] {issue.issue_type}**")
                                st.markdown(f"- Location: {issue.location}")
                                st.markdown(f"- {issue.description}")
                                st.markdown(f"- Suggested fix: {issue.suggested_fix}")

                        if report.consistency_issues:
                            st.markdown("#### Consistency Issues")
                            for issue in report.consistency_issues:
                                status_icon = "✅" if issue.status == "fixed" else "⚠️"
                                st.markdown(f"{status_icon} **[{issue.severity}] {issue.issue_type}**")
                                st.markdown(f"- Location: {issue.location}")
                                st.markdown(f"- {issue.description}")
                                if issue.resolution:
                                    st.markdown(f"- Resolution: {issue.resolution}")

                        if report.line_edit_changes > 0:
                            st.markdown("#### Line Editing")
                            st.markdown(f"**Changes Made:** {report.line_edit_changes}")
                            st.markdown(f"**Summary:** {report.line_edit_summary}")

                        if report.reviewer_notes:
                            st.markdown("**Reviewer Notes:**")
                            st.write(report.reviewer_notes)

                        if report.next_steps:
                            st.markdown("**Next Steps:**")
                            for step in report.next_steps:
                                st.markdown(f"- {step}")

elif page == "Step-by-Step":
    st.markdown('<p class="main-header">Step-by-Step Agent Execution</p>', unsafe_allow_html=True)

    # Debug info
    st.caption(f"🔍 Debug: Project in session state: {'project' in st.session_state}")
    if 'project' in st.session_state and st.session_state.project:
        st.caption(f"🔍 Debug: Project ID: {st.session_state.project.metadata.project_id}")

    if 'project' not in st.session_state or not st.session_state.project:
        st.warning("⚠️ No project loaded. Create or load a project first.")
        st.info("💡 Go to **📂 Load Project** or **📁 Project Manager** to load a project, then return here.")
    else:
        project = st.session_state.project
        pipeline = st.session_state.get('pipeline')

        if not pipeline:
            st.error("Pipeline not initialized. Please create a new project.")
        else:
            st.info(f"**Project:** {project.series.title} | **Stage:** {project.metadata.processing_stage} | **Status:** {project.metadata.status}")

            # Progress overview
            st.markdown("### Progress Overview")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Books", len(project.series.books))
            total_chapters = sum(len(book.chapters) for book in project.series.books) if project.series.books else 0
            col2.metric("Chapters", total_chapters)
            total_scenes = sum(len(ch.scenes) for book in project.series.books for ch in book.chapters) if project.series.books else 0
            col3.metric("Scenes", total_scenes)
            col4.metric("Lore Items", len(project.series.lore.characters) + len(project.series.lore.locations) + len(project.series.lore.world_elements))

            # Book status breakdown
            if project.series.books:
                with st.expander("📚 Book Status Breakdown", expanded=True):
                    for book in project.series.books:
                        status_icon = {
                            "planned": "⏳",
                            "outlined": "✅",
                            "drafted": "📝",
                            "complete": "🎉"
                        }.get(book.status, "❓")

                        chapter_count = len(book.chapters) if book.chapters else 0

                        # Count chapters with scenes
                        chapters_with_scenes = 0
                        total_scenes = 0
                        if book.chapters:
                            for chapter in book.chapters:
                                if chapter.scenes:
                                    chapters_with_scenes += 1
                                    total_scenes += len(chapter.scenes)

                        # Build progress string
                        progress_parts = [f"{chapter_count} ch"]
                        if chapters_with_scenes > 0:
                            progress_parts.append(f"{chapters_with_scenes}/{chapter_count} developed")
                        if total_scenes > 0:
                            progress_parts.append(f"{total_scenes} scenes")

                        progress_str = ", ".join(progress_parts)
                        st.caption(f"{status_icon} Book {book.book_number}: {book.title} - {book.status} ({progress_str})")

            st.markdown("---")

            # Define agent pipeline steps
            agents = [
                {
                    "name": "Series Refiner",
                    "key": "series",
                    "description": "Expands series concept into detailed outline with lore and book premises",
                    "stage": "series",
                    "enabled": True
                },
                {
                    "name": "Book Outliner",
                    "key": "book",
                    "description": f"Creates 3-act structure, character arcs, and chapter outlines ({sum(1 for b in project.series.books if b.status == 'planned')}/{len(project.series.books)} books remaining)",
                    "stage": "book",
                    "enabled": len(project.series.books) > 0 and any(b.status == "planned" for b in project.series.books)
                },
                {
                    "name": "Chapter Developer",
                    "key": "chapter",
                    "description": "Breaks chapters into detailed scenes",
                    "stage": "chapter",
                    "enabled": any(len(book.chapters) > 0 for book in project.series.books) if project.series.books else False
                },
                {
                    "name": "Scene Developer",
                    "key": "scene",
                    "description": "Develops scenes into story beats",
                    "stage": "scene",
                    "enabled": any(
                        len(ch.scenes) > 0
                        for book in project.series.books
                        for ch in book.chapters
                    ) if project.series.books else False
                },
                {
                    "name": "Prose Generator",
                    "key": "prose",
                    "description": "Generates actual prose from beats",
                    "stage": "prose",
                    "enabled": any(
                        len(scene.beats) > 0
                        for book in project.series.books
                        for ch in book.chapters
                        for scene in ch.scenes
                    ) if project.series.books else False
                },
                {
                    "name": "QA Agent",
                    "key": "qa",
                    "description": "Quality assurance and validation",
                    "stage": "qa",
                    "enabled": True
                },
                {
                    "name": "Lore Master",
                    "key": "lore",
                    "description": "Validates lore consistency and detects new lore",
                    "stage": "lore",
                    "enabled": True
                }
            ]

            st.markdown("### Available Agents")
            st.markdown("Run agents one at a time to control the generation process.")

            # Style Guide for Prose Generator
            st.markdown("---")
            with st.expander("📝 Prose Style Guide", expanded=False):
                if project.series.style_guide:
                    st.info("💡 Style guide was set during project creation. You can view and edit it below.")

                    # Show current style guide
                    current_style = st.text_area(
                        "Current Style Guide",
                        value=project.series.style_guide,
                        height=200,
                        key="view_edit_style_guide",
                        help="Edit the style guide for this project"
                    )

                    # Update button
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button("💾 Update Style Guide", use_container_width=True):
                            project.series.style_guide = current_style
                            pipeline.state_manager.save_state(project, "style_guide_updated")
                            st.success("✅ Style guide updated!")
                    with col2:
                        st.download_button(
                            "📥 Download Style Guide",
                            data=current_style,
                            file_name=f"style_guide_{project.metadata.project_id}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )

                    st.success(f"✅ Style guide active ({len(project.series.style_guide.split())} words)")
                else:
                    st.warning("⚠️ No style guide set for this project.")
                    st.info("💡 You can set a style guide during project creation, or add one here:")

                    # Allow adding a style guide to existing project
                    new_style_guide = st.text_area(
                        "Add Style Guide",
                        height=200,
                        placeholder="""Examples:
- Write in the style of Brandon Sanderson with clear magic system explanations
- Use short, punchy sentences for action scenes
- Include vivid sensory details, especially smell and touch
- Favor showing over telling
- Use present tense for flashbacks
- Character dialogue should be sharp and witty
- Avoid adverbs in dialogue tags""",
                        key="add_style_guide_input"
                    )

                    if st.button("💾 Add Style Guide to Project"):
                        if new_style_guide.strip():
                            project.series.style_guide = new_style_guide
                            pipeline.state_manager.save_state(project, "style_guide_added")
                            st.success("✅ Style guide added to project!")
                            st.rerun()
                        else:
                            st.error("Please enter a style guide first")

            # Auto-QA toggle
            st.markdown("---")
            auto_qa = st.checkbox(
                "🛡️ Enable Auto Quality Gates",
                value=st.session_state.get('auto_qa_enabled', True),
                help="Automatically run QA + Lore validation after each content generation agent"
            )
            st.session_state['auto_qa_enabled'] = auto_qa

            if auto_qa:
                st.info("✅ Quality gates will run automatically after Series, Book, and Chapter agents")
            else:
                st.warning("⚠️ Quality gates disabled - you must run QA and Lore manually")

            st.markdown("---")

            # Display agents in columns
            for i in range(0, len(agents), 2):
                col1, col2 = st.columns(2)

                for idx, col in enumerate([col1, col2]):
                    if i + idx < len(agents):
                        agent = agents[i + idx]

                        with col:
                            with st.container():
                                st.markdown(f"#### {agent['name']}")
                                st.caption(agent['description'])
                                st.caption(f"Stage: `{agent['stage']}`")

                                if not agent['enabled']:
                                    st.caption("⚠️ Prerequisites not met")

                                # Run button
                                if st.button(
                                    f"▶️ Run {agent['name']}",
                                    key=f"run_{agent['key']}",
                                    disabled=not agent['enabled'],
                                    type="primary" if agent['enabled'] else "secondary"
                                ):
                                    # Create a status container that will update
                                    status_container = st.empty()
                                    progress_bar = st.progress(0)

                                    with st.spinner(f"Running {agent['name']}..."):
                                        try:
                                            # Execute specific agent
                                            if agent['key'] == 'series':
                                                project = pipeline.agents["series"].process(project)
                                                pipeline.state_manager.save_state(project, "1_series_refined")

                                                # Store lore
                                                if pipeline.lore_store and pipeline.lore_store.enabled:
                                                    pipeline.lore_store.store_all_lore(project)

                                                # Auto quality gate
                                                if st.session_state.get('auto_qa_enabled', True):
                                                    st.info("🛡️ Running quality gates...")
                                                    try:
                                                        project = pipeline.quality_gate(project, "series", max_retries=3)
                                                        st.success("✅ Quality gates passed!")
                                                    except Exception as e:
                                                        st.error(f"❌ Quality gate failed: {e}")
                                                        raise

                                            elif agent['key'] == 'book':
                                                # Process ALL books with status "planned"
                                                books_to_outline = [b for b in project.series.books if b.status == "planned"]

                                                if not books_to_outline:
                                                    status_container.warning("All books are already outlined!")
                                                else:
                                                    total = len(books_to_outline)
                                                    for book_idx, book in enumerate(books_to_outline):
                                                        progress = (book_idx) / total
                                                        progress_bar.progress(progress)
                                                        status_container.info(f"📚 Outlining Book {book.book_number}/{len(project.series.books)}: {book.title}... ({book_idx + 1}/{total})")

                                                        pipeline.agents["book"].book_number = book.book_number
                                                        project = pipeline.agents["book"].process(project)
                                                        pipeline.state_manager.save_state(project, f"2_book_{book.book_number}_outlined")

                                                        # Auto quality gate
                                                        if st.session_state.get('auto_qa_enabled', True):
                                                            status_container.info(f"🛡️ Running quality gates for Book {book.book_number}...")
                                                            try:
                                                                project = pipeline.quality_gate(project, f"book_{book.book_number}", max_retries=3)
                                                            except Exception as e:
                                                                status_container.error(f"❌ Quality gate failed: {e}")
                                                                progress_bar.empty()
                                                                raise

                                                    progress_bar.progress(1.0)
                                                    status_container.success(f"✅ Completed outlining {total} books!")

                                            elif agent['key'] == 'chapter':
                                                # Process ALL pending chapters across all books
                                                chapters_to_develop = []
                                                for book in project.series.books:
                                                    for chapter_idx, chapter in enumerate(book.chapters):
                                                        if chapter.status == "planned":
                                                            chapters_to_develop.append((book, chapter_idx, chapter))

                                                if not chapters_to_develop:
                                                    status_container.warning("All chapters are already developed!")
                                                else:
                                                    total = len(chapters_to_develop)
                                                    for idx, (book, chapter_idx, chapter) in enumerate(chapters_to_develop):
                                                        progress = idx / total
                                                        progress_bar.progress(progress)
                                                        status_container.info(f"📖 Developing Book {book.book_number}, Ch {chapter.chapter_number} ({idx + 1}/{total})")

                                                        book_idx = book.book_number - 1
                                                        project = pipeline.agents["chapter"].process_chapter(project, book_idx, chapter_idx)
                                                        pipeline.state_manager.save_state(project, f"3_book{book.book_number}_ch{chapter.chapter_number}_developed")

                                                        # Auto quality gate (every 10 chapters to avoid too many checks)
                                                        if st.session_state.get('auto_qa_enabled', True):
                                                            if (idx + 1) % 10 == 0 or idx == 0:  # Every 10 chapters or first chapter
                                                                status_container.info(f"🛡️ Running quality gates (checkpoint {idx + 1}/{total})...")
                                                                try:
                                                                    project = pipeline.quality_gate(project, f"chapter_{chapter.chapter_number}", max_retries=3)
                                                                except Exception as e:
                                                                    status_container.error(f"❌ Quality gate failed: {e}")
                                                                    progress_bar.empty()
                                                                    raise

                                                    progress_bar.progress(1.0)
                                                    status_container.success(f"✅ Completed developing {total} chapters!")

                                            elif agent['key'] == 'scene':
                                                # Process ALL scenes that need beats
                                                scenes_to_develop = []
                                                for book in project.series.books:
                                                    for chapter_idx, chapter in enumerate(book.chapters):
                                                        for scene_idx, scene in enumerate(chapter.scenes):
                                                            if not scene.beats or len(scene.beats) == 0:
                                                                scenes_to_develop.append((book, chapter_idx, scene_idx, chapter, scene))

                                                if not scenes_to_develop:
                                                    status_container.warning("All scenes already have beats!")
                                                else:
                                                    total = len(scenes_to_develop)
                                                    for idx, (book, chapter_idx, scene_idx, chapter, scene) in enumerate(scenes_to_develop):
                                                        progress = idx / total
                                                        progress_bar.progress(progress)
                                                        status_container.info(f"🎬 Developing Book {book.book_number}, Ch {chapter.chapter_number}, Scene {scene.scene_number} ({idx + 1}/{total})")

                                                        book_idx = book.book_number - 1
                                                        project = pipeline.agents["scene"].process_scene(project, book_idx, chapter_idx, scene_idx)
                                                        pipeline.state_manager.save_state(project, f"4_book{book.book_number}_ch{chapter.chapter_number}_sc{scene.scene_number}_developed")

                                                        # Auto quality gate (every 50 scenes to avoid too many checks)
                                                        if st.session_state.get('auto_qa_enabled', True):
                                                            if (idx + 1) % 50 == 0 or idx == 0:  # Every 50 scenes or first scene
                                                                status_container.info(f"🛡️ Running quality gates (checkpoint {idx + 1}/{total})...")
                                                                try:
                                                                    project = pipeline.quality_gate(project, f"scene_{scene.scene_number}", max_retries=3)
                                                                except Exception as e:
                                                                    status_container.error(f"❌ Quality gate failed: {e}")
                                                                    progress_bar.empty()
                                                                    raise

                                                    progress_bar.progress(1.0)
                                                    status_container.success(f"✅ Completed developing {total} scenes!")

                                            elif agent['key'] == 'prose':
                                                # Get style guide from project (falls back to session state for backward compatibility)
                                                prose_style_guide = project.series.style_guide or st.session_state.get('prose_style_guide', '')

                                                # Process ALL beats that need prose
                                                beats_to_generate = []
                                                for book in project.series.books:
                                                    for chapter_idx, chapter in enumerate(book.chapters):
                                                        for scene_idx, scene in enumerate(chapter.scenes):
                                                            for beat_idx, beat in enumerate(scene.beats):
                                                                if not beat.prose or (not beat.prose.paragraphs and not beat.prose.content):
                                                                    beats_to_generate.append((book, chapter_idx, scene_idx, beat_idx, chapter, scene, beat))

                                                if not beats_to_generate:
                                                    status_container.warning("All beats already have prose!")
                                                else:
                                                    total = len(beats_to_generate)

                                                    # Show style guide info if present
                                                    if prose_style_guide.strip():
                                                        st.info(f"📝 Using style guide ({len(prose_style_guide.split())} words)")

                                                    for idx, (book, chapter_idx, scene_idx, beat_idx, chapter, scene, beat) in enumerate(beats_to_generate):
                                                        progress = idx / total
                                                        progress_bar.progress(progress)
                                                        status_container.info(f"✍️ Generating prose for Book {book.book_number}, Ch {chapter.chapter_number}, Scene {scene.scene_number}, Beat {beat_idx + 1} ({idx + 1}/{total})")

                                                        book_idx = book.book_number - 1
                                                        # Pass style guide to prose generator
                                                        project = pipeline.agents["prose"].process_beat(
                                                            project, book_idx, chapter_idx, scene_idx, beat_idx,
                                                            style_guide=prose_style_guide if prose_style_guide.strip() else None
                                                        )

                                                        # Save state every 100 beats or on first beat
                                                        if (idx + 1) % 100 == 0 or idx == 0:
                                                            pipeline.state_manager.save_state(project, f"5_book{book.book_number}_ch{chapter.chapter_number}_sc{scene.scene_number}_prose_checkpoint")

                                                    progress_bar.progress(1.0)
                                                    status_container.success(f"✅ Completed generating prose for {total} beats!")
                                                    # Final save
                                                    pipeline.state_manager.save_state(project, f"5_prose_complete")

                                            elif agent['key'] == 'qa':
                                                project, qa_report = pipeline.agents["qa"].process(project)
                                                st.success(f"QA Score: {qa_report.scores.get('overall', 0)}/10")
                                                st.write("**Strengths:**")
                                                for strength in qa_report.strengths:
                                                    st.write(f"- {strength}")
                                                if qa_report.major_issues:
                                                    st.warning("**Major Issues:**")
                                                    for issue in qa_report.major_issues:
                                                        st.write(f"- {issue}")

                                            elif agent['key'] == 'lore':
                                                project, lore_result = pipeline.agents["lore"].process(project)
                                                st.success(f"Lore Score: {lore_result['score']}/10")
                                                if lore_result.get('violations'):
                                                    st.warning("**Violations:**")
                                                    for violation in lore_result['violations']:
                                                        st.write(f"- [{violation.get('severity')}] {violation.get('violation')}")
                                                if lore_result.get('new_lore'):
                                                    st.info("**New Lore Detected:**")
                                                    for item in lore_result['new_lore']:
                                                        st.write(f"- {item.get('type')}: {item.get('name')}")

                                            # Update session state
                                            st.session_state.project = project
                                            st.success(f"✅ {agent['name']} completed successfully!")
                                            st.rerun()

                                        except Exception as e:
                                            st.error(f"❌ Error running {agent['name']}: {e}")
                                            import traceback
                                            st.code(traceback.format_exc())

                                st.markdown("---")

elif page == "Prose Reader":
    st.markdown('<p class="main-header">📖 Prose Reader</p>', unsafe_allow_html=True)

    if 'project' not in st.session_state or not st.session_state.project:
        st.warning("⚠️ No project loaded. Create or load a project first.")
        st.info("💡 Go to **📂 Load Project** or **📁 Project Manager** to load a project, then return here.")
    else:
        project = st.session_state.project

        st.info(f"**Reading:** {project.series.title}")

        # Check if there's any prose generated
        has_prose = False
        for book in project.series.books:
            for chapter in book.chapters:
                for scene in chapter.scenes:
                    for beat in scene.beats:
                        if beat.prose and (beat.prose.paragraphs or beat.prose.content):
                            has_prose = True
                            break

        if not has_prose:
            st.warning("⚠️ No prose generated yet. Use the **🎯 Step-by-Step** page to generate prose first.")
            st.info("💡 Run **Prose Generator** agent after developing scenes and beats.")
        else:
            # Book selection
            book_options = [f"Book {b.book_number}: {b.title}" for b in project.series.books]
            selected_book_str = st.selectbox("Select Book", book_options)
            selected_book_idx = int(selected_book_str.split(":")[0].split()[1]) - 1
            book = project.series.books[selected_book_idx]

            # Chapter selection
            if book.chapters:
                chapter_options = ["All Chapters"] + [f"Chapter {ch.chapter_number}: {ch.title}" for ch in book.chapters]
                selected_chapter_str = st.selectbox("Select Chapter", chapter_options)

                # Display options
                col1, col2, col3 = st.columns(3)
                with col1:
                    show_chapter_titles = st.checkbox("Show Chapter Titles", value=True)
                with col2:
                    show_scene_breaks = st.checkbox("Show Scene Breaks", value=True)
                with col3:
                    font_size = st.select_slider("Font Size", options=["Small", "Medium", "Large"], value="Medium")

                # Font size mapping
                font_size_map = {"Small": "1.0rem", "Medium": "1.2rem", "Large": "1.4rem"}
                prose_font_size = font_size_map[font_size]

                # Export options
                st.markdown("---")
                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("📥 Export to Markdown"):
                        # Generate markdown content
                        markdown_content = f"# {book.title}\n\n"

                        chapters_to_export = book.chapters if selected_chapter_str == "All Chapters" else [ch for ch in book.chapters if f"Chapter {ch.chapter_number}: {ch.title}" == selected_chapter_str]

                        for chapter in chapters_to_export:
                            markdown_content += f"## Chapter {chapter.chapter_number}: {chapter.title}\n\n"
                            for scene in chapter.scenes:
                                for beat in scene.beats:
                                    if beat.prose:
                                        if beat.prose.paragraphs:
                                            for para in beat.prose.paragraphs:
                                                markdown_content += f"{para.content}\n\n"
                                        elif beat.prose.content:
                                            markdown_content += f"{beat.prose.content}\n\n"
                                if show_scene_breaks and scene != chapter.scenes[-1]:
                                    markdown_content += "* * *\n\n"

                        # Download button
                        st.download_button(
                            "💾 Download Markdown",
                            data=markdown_content,
                            file_name=f"{book.title.replace(' ', '_')}_prose.md",
                            mime="text/markdown"
                        )

                with col2:
                    if st.button("📄 Export to Plain Text"):
                        # Generate plain text content
                        text_content = f"{book.title}\n{'=' * len(book.title)}\n\n"

                        chapters_to_export = book.chapters if selected_chapter_str == "All Chapters" else [ch for ch in book.chapters if f"Chapter {ch.chapter_number}: {ch.title}" == selected_chapter_str]

                        for chapter in chapters_to_export:
                            text_content += f"Chapter {chapter.chapter_number}: {chapter.title}\n{'-' * 40}\n\n"
                            for scene in chapter.scenes:
                                for beat in scene.beats:
                                    if beat.prose:
                                        if beat.prose.paragraphs:
                                            for para in beat.prose.paragraphs:
                                                text_content += f"{para.content}\n\n"
                                        elif beat.prose.content:
                                            text_content += f"{beat.prose.content}\n\n"
                                if show_scene_breaks and scene != chapter.scenes[-1]:
                                    text_content += "\n* * *\n\n"

                        st.download_button(
                            "💾 Download Text",
                            data=text_content,
                            file_name=f"{book.title.replace(' ', '_')}_prose.txt",
                            mime="text/plain"
                        )

                with col3:
                    if st.button("📊 Copy Word Count Stats"):
                        # Calculate stats
                        total_words = 0
                        chapters_to_count = book.chapters if selected_chapter_str == "All Chapters" else [ch for ch in book.chapters if f"Chapter {ch.chapter_number}: {ch.title}" == selected_chapter_str]

                        for chapter in chapters_to_count:
                            for scene in chapter.scenes:
                                for beat in scene.beats:
                                    if beat.prose:
                                        if beat.prose.paragraphs:
                                            for para in beat.prose.paragraphs:
                                                total_words += len(para.content.split())
                                        elif beat.prose.content:
                                            total_words += len(beat.prose.content.split())

                        stats_text = f"Book: {book.title}\nChapters: {len(chapters_to_count)}\nTotal Words: {total_words:,}"
                        st.code(stats_text)

                st.markdown("---")

                # Display prose with custom styling
                st.markdown(f"""
                <style>
                    .prose-container {{
                        font-family: 'Georgia', serif;
                        font-size: {prose_font_size};
                        line-height: 1.8;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 2rem;
                    }}
                    .chapter-title {{
                        font-size: 2rem;
                        font-weight: bold;
                        text-align: center;
                        margin: 2rem 0 1rem 0;
                        color: #1f77b4;
                    }}
                    .scene-break {{
                        text-align: center;
                        margin: 2rem 0;
                        color: #666;
                        font-size: 1.5rem;
                    }}
                    .prose-paragraph {{
                        text-indent: 2rem;
                        margin-bottom: 1rem;
                        text-align: justify;
                    }}
                    .prose-paragraph:first-of-type {{
                        text-indent: 0;
                    }}
                </style>
                """, unsafe_allow_html=True)

                # Display selected content
                if selected_chapter_str == "All Chapters":
                    # Display all chapters
                    for chapter in book.chapters:
                        if show_chapter_titles:
                            st.markdown(f'<div class="chapter-title">Chapter {chapter.chapter_number}: {chapter.title}</div>', unsafe_allow_html=True)

                        for scene_idx, scene in enumerate(chapter.scenes):
                            for beat in scene.beats:
                                if beat.prose:
                                    if beat.prose.paragraphs:
                                        for para in beat.prose.paragraphs:
                                            st.markdown(f'<div class="prose-paragraph">{para.content}</div>', unsafe_allow_html=True)
                                    elif beat.prose.content:
                                        st.markdown(f'<div class="prose-paragraph">{beat.prose.content}</div>', unsafe_allow_html=True)

                            if show_scene_breaks and scene_idx < len(chapter.scenes) - 1:
                                st.markdown('<div class="scene-break">* * *</div>', unsafe_allow_html=True)
                else:
                    # Display single chapter
                    chapter_num = int(selected_chapter_str.split(":")[0].split()[1])
                    chapter = book.chapters[chapter_num - 1]

                    if show_chapter_titles:
                        st.markdown(f'<div class="chapter-title">Chapter {chapter.chapter_number}: {chapter.title}</div>', unsafe_allow_html=True)

                    for scene_idx, scene in enumerate(chapter.scenes):
                        for beat in scene.beats:
                            if beat.prose:
                                if beat.prose.paragraphs:
                                    for para in beat.prose.paragraphs:
                                        st.markdown(f'<div class="prose-paragraph">{para.content}</div>', unsafe_allow_html=True)
                                elif beat.prose.content:
                                    st.markdown(f'<div class="prose-paragraph">{beat.prose.content}</div>', unsafe_allow_html=True)

                        if show_scene_breaks and scene_idx < len(chapter.scenes) - 1:
                            st.markdown('<div class="scene-break">* * *</div>', unsafe_allow_html=True)

                # Word count footer
                st.markdown("---")
                total_words_displayed = 0
                chapters_displayed = book.chapters if selected_chapter_str == "All Chapters" else [ch for ch in book.chapters if f"Chapter {ch.chapter_number}: {ch.title}" == selected_chapter_str]

                for chapter in chapters_displayed:
                    for scene in chapter.scenes:
                        for beat in scene.beats:
                            if beat.prose:
                                if beat.prose.paragraphs:
                                    for para in beat.prose.paragraphs:
                                        total_words_displayed += len(para.content.split())
                                elif beat.prose.content:
                                    total_words_displayed += len(beat.prose.content.split())

                col1, col2, col3 = st.columns(3)
                col1.metric("Chapters Displayed", len(chapters_displayed))
                col2.metric("Total Words", f"{total_words_displayed:,}")
                col3.metric("Estimated Pages", f"{total_words_displayed // 250}")

            else:
                st.warning("This book has no chapters yet.")

elif page == "Editing Suite":
    st.markdown('<p class="main-header">✏️ Editing Suite</p>', unsafe_allow_html=True)

    if 'project' not in st.session_state or not st.session_state.project:
        st.warning("⚠️ No project loaded. Create or load a project first.")
        st.info("💡 Go to **📂 Load Project** or **📁 Project Manager** to load a project, then return here.")
    else:
        project = st.session_state.project

        st.info(f"**Editing:** {project.series.title}")

        # Initialize edit history in session state
        if 'edit_history' not in st.session_state:
            st.session_state.edit_history = []

        # Editor selection
        st.markdown("### Select Editor")
        col1, col2 = st.columns([2, 3])

        with col1:
            editor_type = st.selectbox(
                "Editor Level",
                [
                    "Line Editor (Sentence-level)",
                    "Scene Editor (Coming soon)",
                    "Chapter Editor (Coming soon)",
                    "Book Editor (Coming soon)",
                    "Series Editor (Coming soon)",
                    "Copy Editor (Coming soon)"
                ]
            )

        with col2:
            if "Coming soon" in editor_type:
                st.warning("⚠️ This editor is not yet implemented")
            else:
                st.success("✅ Editor ready")

        st.markdown("---")

        # Only show Line Editor UI for now
        if editor_type == "Line Editor (Sentence-level)":
            st.markdown("### Line Editor Configuration")

            # Scope selection
            col1, col2, col3 = st.columns(3)

            with col1:
                book_options = [f"Book {b.book_number}: {b.title}" for b in project.series.books]
                selected_book_str = st.selectbox("Select Book", book_options, key="edit_book")
                book_idx = int(selected_book_str.split(":")[0].split()[1]) - 1
                book = project.series.books[book_idx]

            with col2:
                chapter_options = [f"Chapter {ch.chapter_number}: {ch.title}" for ch in book.chapters]
                selected_chapter_str = st.selectbox("Select Chapter", chapter_options, key="edit_chapter")
                chapter_idx = int(selected_chapter_str.split(":")[0].split()[1]) - 1
                chapter = book.chapters[chapter_idx]

            with col3:
                scene_options = [f"Scene {sc.scene_number}" for sc in chapter.scenes]
                selected_scene_str = st.selectbox("Select Scene", scene_options, key="edit_scene")
                scene_idx = int(selected_scene_str.split()[1]) - 1
                scene = chapter.scenes[scene_idx]

            # Style guide
            with st.expander("📝 Style Guide (Optional)", expanded=False):
                edit_style_guide = st.text_area(
                    "Style Guide for Editing",
                    value=project.series.style_guide or '',
                    height=150,
                    placeholder="Provide specific style guidelines for the editor to follow...",
                    help="Using the style guide set for this project"
                )

            st.markdown("---")

            # Actions
            st.markdown("### Actions")

            # Single scene analysis
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("🔍 Analyze This Scene", type="primary", use_container_width=True):
                    with st.spinner("Analyzing prose..."):
                        try:
                            # Initialize Line Editor
                            from agents.editors.line_editor import LineEditor
                            from langchain_openai import ChatOpenAI

                            llm = ChatOpenAI(
                                model="anthropic/claude-3.5-sonnet",
                                openai_api_key=openrouter_key,
                                openai_api_base="https://openrouter.ai/api/v1",
                                temperature=0.7
                            )

                            line_editor = LineEditor(
                                llm=llm,
                                style_guide=edit_style_guide if edit_style_guide.strip() else None
                            )

                            # Analyze
                            edit_report = line_editor.analyze(
                                project=project,
                                book_idx=book_idx,
                                chapter_idx=chapter_idx,
                                scene_idx=scene_idx
                            )

                            # Store report in session
                            st.session_state['current_edit_report'] = edit_report

                            st.success("✅ Analysis complete!")
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Analysis failed: {e}")
                            import traceback
                            st.code(traceback.format_exc())

            with col2:
                if st.button("⚡ Quick Fixes", use_container_width=True):
                    with st.spinner("Applying quick fixes..."):
                        try:
                            from agents.editors.line_editor import LineEditor
                            from langchain_openai import ChatOpenAI

                            llm = ChatOpenAI(
                                model="anthropic/claude-3.5-sonnet",
                                openai_api_key=openrouter_key,
                                openai_api_base="https://openrouter.ai/api/v1",
                                temperature=0.7
                            )

                            line_editor = LineEditor(llm=llm)

                            # Apply quick fixes
                            project = line_editor.quick_fixes(
                                project=project,
                                book_idx=book_idx,
                                chapter_idx=chapter_idx,
                                scene_idx=scene_idx
                            )

                            st.session_state.project = project
                            st.success("✅ Quick fixes applied!")

                            # Save state
                            if st.session_state.get('pipeline'):
                                st.session_state.pipeline.state_manager.save_state(
                                    project,
                                    f"edit_quickfix_b{book_idx+1}_ch{chapter_idx+1}_sc{scene_idx+1}"
                                )

                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Quick fixes failed: {e}")

            with col3:
                if st.button("💾 Save Changes", use_container_width=True):
                    if st.session_state.get('pipeline'):
                        st.session_state.pipeline.state_manager.save_state(
                            project,
                            f"edit_manual_b{book_idx+1}_ch{chapter_idx+1}_sc{scene_idx+1}"
                        )
                        st.success("✅ Changes saved!")
                    else:
                        st.error("Pipeline not initialized")

            st.markdown("---")

            # Batch mode actions
            st.markdown("### Batch Mode")
            st.caption("Analyze multiple scenes/chapters at once")

            batch_col1, batch_col2, batch_col3 = st.columns(3)

            with batch_col1:
                if st.button("📚 Analyze All Scenes in Chapter", use_container_width=True):
                    with st.spinner(f"Analyzing all scenes in Chapter {chapter.chapter_number}..."):
                        try:
                            import time
                            from agents.editors.line_editor import LineEditor
                            from langchain_openai import ChatOpenAI

                            # Track start time
                            start_time = time.time()

                            llm = ChatOpenAI(
                                model="anthropic/claude-3.5-sonnet",
                                openai_api_key=openrouter_key,
                                openai_api_base="https://openrouter.ai/api/v1",
                                temperature=0.7
                            )

                            line_editor = LineEditor(
                                llm=llm,
                                style_guide=edit_style_guide if edit_style_guide.strip() else None
                            )

                            # Analyze all scenes in chapter
                            all_reports = []
                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            for idx, scene in enumerate(chapter.scenes):
                                progress = (idx + 1) / len(chapter.scenes)
                                progress_bar.progress(progress)

                                # Calculate elapsed time
                                elapsed_time = time.time() - start_time
                                minutes = int(elapsed_time // 60)
                                seconds = int(elapsed_time % 60)
                                time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

                                # Show percentage and time
                                percentage = int(progress * 100)
                                status_text.text(f"Analyzing scene {scene.scene_number} of {len(chapter.scenes)}... {percentage}% - Elapsed: {time_str}")

                                report = line_editor.analyze(
                                    project=project,
                                    book_idx=book_idx,
                                    chapter_idx=chapter_idx,
                                    scene_idx=idx
                                )
                                all_reports.append(report)

                            # Calculate total runtime
                            total_time = time.time() - start_time
                            minutes = int(total_time // 60)
                            seconds = int(total_time % 60)
                            time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

                            progress_bar.empty()
                            status_text.empty()

                            # Store all reports
                            st.session_state['batch_edit_reports'] = all_reports
                            st.session_state['batch_mode'] = 'chapter_scenes'
                            st.success(f"✅ Analyzed {len(chapter.scenes)} scenes in {time_str}!")
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Batch analysis failed: {e}")

            with batch_col2:
                if st.button("📖 Analyze All Chapters in Book", use_container_width=True):
                    with st.spinner(f"Analyzing all chapters in {book.title}..."):
                        try:
                            import time
                            from agents.editors.chapter_editor import ChapterEditor
                            from langchain_openai import ChatOpenAI

                            # Track start time
                            start_time = time.time()

                            llm = ChatOpenAI(
                                model="anthropic/claude-3.5-sonnet",
                                openai_api_key=openrouter_key,
                                openai_api_base="https://openrouter.ai/api/v1",
                                temperature=0.7
                            )

                            chapter_editor = ChapterEditor(llm=llm)

                            # Analyze all chapters
                            all_reports = []
                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            for idx, ch in enumerate(book.chapters):
                                progress = (idx + 1) / len(book.chapters)
                                progress_bar.progress(progress)

                                # Calculate elapsed time
                                elapsed_time = time.time() - start_time
                                minutes = int(elapsed_time // 60)
                                seconds = int(elapsed_time % 60)
                                time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

                                # Show percentage and time
                                percentage = int(progress * 100)
                                status_text.text(f"Analyzing chapter {ch.chapter_number} of {len(book.chapters)}... {percentage}% - Elapsed: {time_str}")

                                report = chapter_editor.analyze(
                                    project=project,
                                    book_idx=book_idx,
                                    chapter_idx=idx
                                )
                                all_reports.append(report)

                            # Calculate total runtime
                            total_time = time.time() - start_time
                            minutes = int(total_time // 60)
                            seconds = int(total_time % 60)
                            time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

                            progress_bar.empty()
                            status_text.empty()

                            # Store all reports
                            st.session_state['batch_edit_reports'] = all_reports
                            st.session_state['batch_mode'] = 'book_chapters'
                            st.success(f"✅ Analyzed {len(book.chapters)} chapters in {time_str}!")
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Batch analysis failed: {e}")

            with batch_col3:
                if st.button("📕 Analyze Entire Book", use_container_width=True):
                    with st.spinner(f"Analyzing {book.title}..."):
                        try:
                            import time
                            from agents.editors.book_editor import BookEditor
                            from langchain_openai import ChatOpenAI

                            # Track start time
                            start_time = time.time()

                            llm = ChatOpenAI(
                                model="anthropic/claude-3.5-sonnet",
                                openai_api_key=openrouter_key,
                                openai_api_base="https://openrouter.ai/api/v1",
                                temperature=0.7
                            )

                            book_editor = BookEditor(llm=llm)

                            # Analyze book
                            report = book_editor.analyze(
                                project=project,
                                book_idx=book_idx
                            )

                            # Calculate total runtime
                            total_time = time.time() - start_time
                            minutes = int(total_time // 60)
                            seconds = int(total_time % 60)
                            time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

                            # Store report
                            st.session_state['current_edit_report'] = report
                            st.success(f"✅ Book analysis complete in {time_str}!")
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Analysis failed: {e}")

            # Series-level batch action
            if st.button("🌐 Analyze Entire Series", use_container_width=True):
                with st.spinner("Analyzing entire series..."):
                    try:
                        import time
                        from agents.editors.series_editor import SeriesEditor
                        from langchain_openai import ChatOpenAI

                        # Track start time
                        start_time = time.time()

                        llm = ChatOpenAI(
                            model="anthropic/claude-3.5-sonnet",
                            openai_api_key=openrouter_key,
                            openai_api_base="https://openrouter.ai/api/v1",
                            temperature=0.7
                        )

                        series_editor = SeriesEditor(llm=llm)

                        # Analyze series
                        report = series_editor.analyze(project=project)

                        # Calculate total runtime
                        total_time = time.time() - start_time
                        minutes = int(total_time // 60)
                        seconds = int(total_time % 60)
                        time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

                        # Store report
                        st.session_state['current_edit_report'] = report
                        st.success(f"✅ Series analysis complete in {time_str}!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Analysis failed: {e}")

            st.markdown("---")

            # Display edit report if available
            if 'current_edit_report' in st.session_state:
                edit_report = st.session_state['current_edit_report']

                st.markdown("### 📊 Edit Report")

                col1, col2, col3 = st.columns(3)
                col1.metric("Overall Score", f"{edit_report.overall_score}/10")
                col2.metric("Suggestions", len(edit_report.suggestions))
                col3.metric("Est. Time", edit_report.estimated_revision_time)

                # Strengths
                if edit_report.strengths:
                    with st.expander("✅ Strengths", expanded=True):
                        for strength in edit_report.strengths:
                            st.success(f"• {strength}")

                # Summary
                st.markdown("#### Summary")
                st.info(edit_report.summary)

                # Suggestions
                st.markdown("#### Suggestions")

                # Filter controls
                col1, col2 = st.columns(2)
                with col1:
                    severity_filter = st.multiselect(
                        "Filter by Severity",
                        ["critical", "major", "minor", "suggestion"],
                        default=["critical", "major", "minor", "suggestion"]
                    )
                with col2:
                    categories = list(set([s.category for s in edit_report.suggestions]))
                    category_filter = st.multiselect(
                        "Filter by Category",
                        categories,
                        default=categories
                    )

                # Display filtered suggestions
                filtered_suggestions = [
                    s for s in edit_report.suggestions
                    if s.severity in severity_filter and s.category in category_filter
                ]

                if not filtered_suggestions:
                    st.info("No suggestions match the current filters.")
                else:
                    for idx, suggestion in enumerate(filtered_suggestions):
                        severity_icons = {
                            "critical": "🔴",
                            "major": "🟠",
                            "minor": "🟡",
                            "suggestion": "🔵"
                        }
                        icon = severity_icons.get(suggestion.severity, "⚪")

                        with st.expander(f"{icon} {suggestion.severity.upper()}: {suggestion.category} - {suggestion.description[:60]}...", expanded=False):
                            st.markdown(f"**Category:** {suggestion.category}")
                            st.markdown(f"**Location:** {suggestion.location.get('hint', 'Scene level')}")

                            if suggestion.original_text:
                                st.markdown("**Original:**")
                                st.code(suggestion.original_text, language=None)

                            if suggestion.suggested_text:
                                st.markdown("**Suggested:**")
                                st.code(suggestion.suggested_text, language=None)

                            st.markdown("**Rationale:**")
                            st.write(suggestion.rationale)

                            col1, col2, col3 = st.columns(3)

                            with col1:
                                if st.button("✅ Apply", key=f"apply_{suggestion.edit_id}", use_container_width=True):
                                    try:
                                        from agents.editors.line_editor import LineEditor
                                        from langchain_openai import ChatOpenAI

                                        llm = ChatOpenAI(
                                            model="anthropic/claude-3.5-sonnet",
                                            openai_api_key=openrouter_key,
                                            openai_api_base="https://openrouter.ai/api/v1",
                                            temperature=0.7
                                        )

                                        line_editor = LineEditor(llm=llm)
                                        project = line_editor.apply_edit(project, suggestion)
                                        st.session_state.project = project

                                        # Track in edit history
                                        st.session_state.edit_history.append({
                                            'suggestion': suggestion,
                                            'applied': True,
                                            'timestamp': datetime.now().isoformat()
                                        })

                                        st.success("✅ Edit applied!")
                                        st.rerun()

                                    except Exception as e:
                                        st.error(f"Failed to apply edit: {e}")

                            with col2:
                                if st.button("❌ Reject", key=f"reject_{suggestion.edit_id}", use_container_width=True):
                                    # Track rejection
                                    st.session_state.edit_history.append({
                                        'suggestion': suggestion,
                                        'applied': False,
                                        'timestamp': datetime.now().isoformat()
                                    })
                                    st.info("Suggestion rejected")

                            with col3:
                                if st.button("✏️ Modify", key=f"modify_{suggestion.edit_id}", use_container_width=True):
                                    st.session_state[f'modify_{suggestion.edit_id}'] = True
                                    st.rerun()

                            # Show modification UI if requested
                            if st.session_state.get(f'modify_{suggestion.edit_id}'):
                                st.markdown("**Custom Edit:**")
                                custom_text = st.text_area(
                                    "Enter your version:",
                                    value=suggestion.suggested_text or suggestion.original_text,
                                    key=f"custom_{suggestion.edit_id}"
                                )

                                col1, col2 = st.columns(2)
                                if col1.button("Apply Custom", key=f"apply_custom_{suggestion.edit_id}"):
                                    # Create modified suggestion
                                    modified_suggestion = suggestion.copy()
                                    modified_suggestion.suggested_text = custom_text

                                    try:
                                        from agents.editors.line_editor import LineEditor
                                        from langchain_openai import ChatOpenAI

                                        llm = ChatOpenAI(
                                            model="anthropic/claude-3.5-sonnet",
                                            openai_api_key=openrouter_key,
                                            openai_api_base="https://openrouter.ai/api/v1",
                                            temperature=0.7
                                        )

                                        line_editor = LineEditor(llm=llm)
                                        project = line_editor.apply_edit(project, modified_suggestion)
                                        st.session_state.project = project

                                        st.session_state[f'modify_{suggestion.edit_id}'] = False
                                        st.success("✅ Custom edit applied!")
                                        st.rerun()

                                    except Exception as e:
                                        st.error(f"Failed: {e}")

                                if col2.button("Cancel", key=f"cancel_custom_{suggestion.edit_id}"):
                                    st.session_state[f'modify_{suggestion.edit_id}'] = False
                                    st.rerun()

            # Batch reports display
            if st.session_state.get('batch_edit_reports'):
                st.markdown("---")
                st.markdown("### 📊 Batch Analysis Results")

                batch_reports = st.session_state['batch_edit_reports']
                batch_mode = st.session_state.get('batch_mode', 'unknown')

                # Summary stats
                total_suggestions = sum(len(r.suggestions) for r in batch_reports)
                avg_score = sum(r.overall_score for r in batch_reports) / len(batch_reports)

                col1, col2, col3 = st.columns(3)
                col1.metric("Items Analyzed", len(batch_reports))
                col2.metric("Total Suggestions", total_suggestions)
                col3.metric("Avg Score", f"{avg_score:.1f}/10")

                # Display each report
                for idx, report in enumerate(batch_reports):
                    scope_name = report.scope.get('description', f"Item {idx + 1}")

                    with st.expander(f"Report {idx + 1}: {scope_name} - Score: {report.overall_score}/10 ({len(report.suggestions)} suggestions)", expanded=False):
                        # Strengths
                        if report.strengths:
                            st.markdown("**Strengths:**")
                            for strength in report.strengths:
                                st.success(f"• {strength}")

                        # Summary
                        st.info(report.summary)

                        # Suggestions
                        if report.suggestions:
                            st.markdown(f"**{len(report.suggestions)} Suggestions:**")
                            for sug in report.suggestions:
                                severity_icons = {
                                    "critical": "🔴",
                                    "major": "🟠",
                                    "minor": "🟡",
                                    "suggestion": "🔵"
                                }
                                icon = severity_icons.get(sug.severity, "⚪")
                                st.caption(f"{icon} {sug.severity.upper()}: {sug.description}")

                # Clear batch reports button
                if st.button("Clear Batch Results"):
                    del st.session_state['batch_edit_reports']
                    del st.session_state['batch_mode']
                    st.rerun()

            # Edit history
            if st.session_state.get('edit_history'):
                st.markdown("---")
                with st.expander("📜 Edit History", expanded=False):
                    for idx, edit in enumerate(reversed(st.session_state.edit_history[-20:])):  # Last 20
                        status = "✅ Applied" if edit['applied'] else "❌ Rejected"
                        timestamp = edit['timestamp']
                        st.caption(f"{status} - {timestamp} - {edit['suggestion'].category}")

        else:
            st.info("Please select the Line Editor to use the editing suite. Other editors are coming soon!")

elif page == "Chat":
    st.markdown('<p class="main-header">💬 Series Chat</p>', unsafe_allow_html=True)

    if 'project' not in st.session_state or not st.session_state.project:
        st.warning("⚠️ No project loaded. Create or load a project first.")
        st.info("💡 Go to **📂 Load Project** or **📁 Project Manager** to load a project, then return here.")
    else:
        project = st.session_state.project

        st.info(f"**Chatting about:** {project.series.title}")

        # Initialize chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

        # Display chat history using Streamlit's chat components
        st.markdown("---")

        if st.session_state.chat_history:
            for msg in st.session_state.chat_history:
                with st.chat_message(msg['role']):
                    st.write(msg['content'])
        else:
            st.info("👋 Start a conversation by asking a question about your series!")

        st.markdown("---")

        # Chat input
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "Ask a question about your series:",
                placeholder="e.g., What are the main conflicts in Book 2? Who are the primary antagonists? What happens in Chapter 5?",
                height=100
            )
            col1, col2 = st.columns([1, 5])
            with col1:
                submit = st.form_submit_button("Send", use_container_width=True)
            with col2:
                clear_chat = st.form_submit_button("Clear Chat", use_container_width=True)

        if clear_chat:
            st.session_state.chat_history = []
            st.rerun()

        if submit and user_input:
            # Add user message to history
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            with st.spinner("Thinking..."):
                # Build context from project
                context_parts = []

                # Series overview
                context_parts.append(f"Series: {project.series.title}")
                context_parts.append(f"Premise: {project.series.premise}")
                context_parts.append(f"Genre: {project.series.genre}")

                # Lore summary
                if project.series.lore.characters:
                    context_parts.append(f"\nCharacters ({len(project.series.lore.characters)}):")
                    for char in project.series.lore.characters[:20]:  # Limit to prevent token overflow
                        context_parts.append(f"- {char.name}: {char.role} - {char.description}")

                if project.series.lore.locations:
                    context_parts.append(f"\nLocations ({len(project.series.lore.locations)}):")
                    for loc in project.series.lore.locations[:20]:
                        context_parts.append(f"- {loc.name}: {loc.description}")

                if project.series.lore.world_elements:
                    context_parts.append(f"\nWorld Elements ({len(project.series.lore.world_elements)}):")
                    for elem in project.series.lore.world_elements[:20]:
                        context_parts.append(f"- {elem.name} ({elem.type}): {elem.description}")

                # Books summary
                if project.series.books:
                    context_parts.append(f"\nBooks ({len(project.series.books)}):")
                    for book in project.series.books:
                        context_parts.append(f"\nBook {book.book_number}: {book.title}")
                        context_parts.append(f"  Status: {book.status}")
                        context_parts.append(f"  Premise: {book.premise}")

                        if book.chapters:
                            context_parts.append(f"  Chapters ({len(book.chapters)}):")
                            for ch in book.chapters[:10]:  # Show first 10 chapters
                                ch_info = f"    Ch {ch.chapter_number}: {ch.title} - {ch.purpose}"
                                if ch.scenes:
                                    ch_info += f" ({len(ch.scenes)} scenes)"
                                context_parts.append(ch_info)
                            if len(book.chapters) > 10:
                                context_parts.append(f"    ... and {len(book.chapters) - 10} more chapters")

                context = "\n".join(context_parts)

                # Create prompt for LLM
                prompt = f"""You are a helpful assistant for a fiction writer. You have access to the writer's series information including lore, characters, locations, and story structure.

Context about the series:
{context}

User question: {user_input}

Provide a helpful, specific answer based on the series information. If the information needed to answer isn't in the context, say so."""

                # Use the pipeline's LLM to answer
                try:
                    pipeline = st.session_state.get('pipeline')
                    if pipeline:
                        # Use one of the pipeline's agents to answer
                        from langchain_openai import ChatOpenAI
                        from langchain.schema import HumanMessage, SystemMessage

                        # Create a simple LLM call
                        llm = ChatOpenAI(
                            model="google/gemini-2.5-flash-lite",
                            openai_api_key=openrouter_key,
                            openai_api_base="https://openrouter.ai/api/v1",
                            temperature=0.7
                        )

                        messages = [
                            SystemMessage(content="You are a helpful assistant for a fiction writer. Answer questions about their series based on the context provided."),
                            HumanMessage(content=prompt)
                        ]

                        response = llm.invoke(messages).content
                    else:
                        response = "Error: Pipeline not initialized. Please load or create a project first."

                    # Add assistant response to history
                    st.session_state.chat_history.append({"role": "assistant", "content": response})

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
                    st.error(error_msg)

            st.rerun()

elif page == "Settings":
    st.markdown('<p class="main-header">Pipeline Settings & Execution</p>', unsafe_allow_html=True)

    if not st.session_state.project:
        st.warning("⚠️ No project loaded. Create or load a project first.")
    else:
        project = st.session_state.project

        # STATUS/ERROR SECTION AT TOP
        status_container = st.container()
        with status_container:
            if st.session_state.running:
                st.info("⏳ Pipeline is running... Status updates below.")

        # Empty containers for status updates (will be filled during execution)
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        error_placeholder = st.empty()

        st.markdown("---")

        st.success(f"📖 Project: **{project.metadata.project_id}**")
        st.info(f"Series: {project.series.title}")

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Pipeline Stages")
            stages = [
                "1️⃣ Series Refiner",
                "2️⃣ Book Outliner",
                "3️⃣ Chapter Developer",
                "4️⃣ Scene Developer",
                "5️⃣ Beat Developer",
                "6️⃣ Prose Generator",
                "7️⃣ Quality Gates",
                "8️⃣ Final Export"
            ]
            for stage in stages:
                st.text(stage)

        with col2:
            st.markdown("### Current Status")
            st.metric("Stage", project.metadata.processing_stage)
            st.metric("Status", project.metadata.status)
            st.metric("Books", len(project.series.books))

            if project.series.books:
                total_chapters = sum(len(book.chapters) for book in project.series.books)
                st.metric("Chapters", total_chapters)

        st.markdown("---")

        if st.button("🚀 Run Full Pipeline", type="primary", disabled=st.session_state.running):
            st.session_state.running = True
            import time

            try:
                # Track start time
                start_time = time.time()

                # Update status at the top
                with progress_placeholder:
                    progress_bar = st.progress(0)
                with status_placeholder:
                    st.markdown('<div class="status-box status-running">⏳ Running pipeline... 0% - Elapsed: 0s</div>', unsafe_allow_html=True)

                # Run pipeline
                if not st.session_state.pipeline:
                    st.session_state.pipeline = FictionPipeline(
                        project_id=project.metadata.project_id,
                        output_dir="output",
                        openrouter_api_key=openrouter_key,
                        preset=preset,
                        use_lore_db=use_lore_db,
                        requirements=getattr(st.session_state.pipeline, 'requirements', {}) if st.session_state.pipeline else {}
                    )
                elif not hasattr(st.session_state.pipeline, 'requirements'):
                    st.session_state.pipeline.requirements = {}

                # Note: The pipeline.run() doesn't expose progress hooks, so we'll just show running state
                # A future enhancement would be to modify pipeline.run() to accept a callback
                final_project = st.session_state.pipeline.run(project)
                st.session_state.project = final_project

                # Calculate total runtime
                elapsed_time = time.time() - start_time
                minutes = int(elapsed_time // 60)
                seconds = int(elapsed_time % 60)
                time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

                with progress_placeholder:
                    st.progress(1.0)
                with status_placeholder:
                    st.markdown(f'<div class="status-box status-complete">✅ Pipeline complete! 100% - Total time: {time_str}</div>', unsafe_allow_html=True)

            except Exception as e:
                # Calculate elapsed time even on error
                elapsed_time = time.time() - start_time
                minutes = int(elapsed_time // 60)
                seconds = int(elapsed_time % 60)
                time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

                with status_placeholder:
                    st.markdown(f'<div class="status-box status-error">❌ Error after {time_str}: {e}</div>', unsafe_allow_html=True)
                with error_placeholder:
                    st.error(f"**Pipeline failed:** {e}")

            finally:
                st.session_state.running = False

elif page == "Agent Config":
    st.markdown('<p class="main-header">⚙️ Agent Configuration</p>', unsafe_allow_html=True)
    st.markdown("Configure models, parameters, and prompts for all pipeline agents.")
    st.markdown("---")

    # Import necessary modules
    from utils.model_config import ModelConfig, AgentModelConfig
    import inspect
    import requests

    # Function to fetch OpenRouter models
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def get_openrouter_models():
        """Fetch available models from OpenRouter API"""
        try:
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                return []

            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )

            if response.status_code == 200:
                models = response.json().get("data", [])
                # Extract model IDs and sort alphabetically
                model_ids = sorted([m.get("id", "") for m in models if m.get("id")])
                return model_ids
            else:
                return []
        except Exception as e:
            print(f"Error fetching OpenRouter models: {e}")
            return []

    # Tabs for different configuration aspects
    tab1, tab2, tab3 = st.tabs(["📊 Model Configurations", "🎨 Presets", "📝 Agent Prompts"])

    with tab1:
        st.markdown("### Model Configurations")

        # Fetch OpenRouter models (cached, no notification)
        openrouter_models = get_openrouter_models()

        # Configuration mode selector
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            config_mode = st.selectbox(
                "Configuration Mode",
                ["Use Preset", "Custom Configuration"],
                help="Choose a preset or create custom configuration"
            )

        with col2:
            if config_mode == "Use Preset":
                preset_name = st.selectbox(
                    "Select Preset",
                    ["balanced", "creative", "precise", "cost_optimized", "premium",
                     "balanced_nsfw", "creative_nsfw", "precise_nsfw", "cost_optimized_nsfw", "premium_nsfw"],
                    help="Pre-configured model settings for common use cases"
                )
            else:
                custom_name = st.text_input(
                    "Configuration Name",
                    value="my_custom_config",
                    help="Name for your custom configuration"
                )

        with col3:
            if st.button("💾 Save", help="Save configuration to session"):
                st.session_state['saved_config'] = custom_name if config_mode == "Custom Configuration" else preset_name
                st.toast("Configuration saved!")

        st.markdown("---")

        # Get configuration based on mode
        if config_mode == "Use Preset":
            st.info(f"📋 **Active Preset:** `{preset_name}`")
            preset_overrides = ModelConfig.get_presets().get(preset_name, {})
            active_config = ModelConfig.create(preset_overrides)
        else:
            st.info(f"🛠️ **Custom Configuration:** `{custom_name}`")
            # Start with defaults for custom
            active_config = ModelConfig.DEFAULTS.copy()

        st.caption("Expand each agent to view/modify its configuration")

        # Create expandable sections for each agent
        for agent_name, config in active_config.items():
            with st.expander(f"🤖 {agent_name.upper()} Agent", expanded=False):

                # Show current active configuration at top
                st.markdown("**Currently Active:**")
                current_config = {
                    "model": config.model,
                    "temperature": config.temperature,
                    "max_tokens": config.max_tokens or 2000,
                }
                if config.top_p:
                    current_config["top_p"] = config.top_p
                if config.top_k:
                    current_config["top_k"] = config.top_k
                if config.frequency_penalty:
                    current_config["frequency_penalty"] = config.frequency_penalty
                if config.presence_penalty:
                    current_config["presence_penalty"] = config.presence_penalty
                if config.repetition_penalty:
                    current_config["repetition_penalty"] = config.repetition_penalty
                if config.min_p:
                    current_config["min_p"] = config.min_p
                if config.seed:
                    current_config["seed"] = config.seed

                st.json(current_config)

                st.markdown("---")
                st.markdown("**Modify Settings:**")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Model Settings**")

                    # Use selectbox if models loaded, otherwise text input
                    if openrouter_models:
                        # Find current model in list or use first as default
                        try:
                            current_index = openrouter_models.index(config.model)
                        except (ValueError, AttributeError):
                            current_index = 0

                        model = st.selectbox(
                            "Model",
                            options=openrouter_models,
                            index=current_index,
                            key=f"{agent_name}_model",
                            help="Select from available OpenRouter models (alphabetically sorted)"
                        )
                    else:
                        model = st.text_input(
                            "Model",
                            value=config.model,
                            key=f"{agent_name}_model",
                            help="OpenRouter model name (e.g., anthropic/claude-3.5-sonnet)"
                        )

                    temperature = st.slider(
                        "Temperature",
                        min_value=0.0,
                        max_value=1.0,
                        value=config.temperature,
                        step=0.05,
                        key=f"{agent_name}_temp",
                        help="Higher = more creative, Lower = more deterministic"
                    )

                with col2:
                    st.markdown("**Token & Penalty Settings**")
                    max_tokens = st.number_input(
                        "Max Tokens",
                        min_value=500,
                        max_value=32000,
                        value=config.max_tokens or 2000,
                        step=500,
                        key=f"{agent_name}_tokens",
                        help="Maximum tokens to generate"
                    )

                    col2a, col2b = st.columns(2)
                    with col2a:
                        freq_penalty = st.number_input(
                            "Frequency Penalty",
                            min_value=0.0,
                            max_value=2.0,
                            value=config.frequency_penalty or 0.0,
                            step=0.1,
                            key=f"{agent_name}_freq",
                            help="Reduce repetition"
                        )
                    with col2b:
                        pres_penalty = st.number_input(
                            "Presence Penalty",
                            min_value=0.0,
                            max_value=2.0,
                            value=config.presence_penalty or 0.0,
                            step=0.1,
                            key=f"{agent_name}_pres",
                            help="Encourage new topics"
                        )

                # Advanced parameters
                with st.expander("⚙️ Advanced Parameters", expanded=False):
                    col3a, col3b = st.columns(2)

                    with col3a:
                        top_p = st.slider(
                            "Top P",
                            min_value=0.0,
                            max_value=1.0,
                            value=config.top_p or 1.0,
                            step=0.05,
                            key=f"{agent_name}_top_p",
                            help="Nucleus sampling - consider tokens with top_p probability mass"
                        )

                        top_k = st.number_input(
                            "Top K",
                            min_value=0,
                            max_value=100,
                            value=config.top_k or 0,
                            step=1,
                            key=f"{agent_name}_top_k",
                            help="Consider only top K tokens (0 = disabled)"
                        )

                        min_p = st.slider(
                            "Min P",
                            min_value=0.0,
                            max_value=1.0,
                            value=config.min_p or 0.0,
                            step=0.01,
                            key=f"{agent_name}_min_p",
                            help="Minimum probability threshold"
                        )

                    with col3b:
                        rep_penalty = st.slider(
                            "Repetition Penalty",
                            min_value=0.0,
                            max_value=2.0,
                            value=config.repetition_penalty or 1.0,
                            step=0.05,
                            key=f"{agent_name}_rep_pen",
                            help="Penalize repetition (1.0 = no penalty)"
                        )

                        seed = st.number_input(
                            "Seed",
                            min_value=0,
                            max_value=999999,
                            value=config.seed or 0,
                            step=1,
                            key=f"{agent_name}_seed",
                            help="Random seed for reproducibility (0 = random)"
                        )

                # Show modified preview
                st.markdown("**Modified Preview:**")
                modified_config = {
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if freq_penalty > 0:
                    modified_config["frequency_penalty"] = freq_penalty
                if pres_penalty > 0:
                    modified_config["presence_penalty"] = pres_penalty
                if top_p < 1.0:
                    modified_config["top_p"] = top_p
                if top_k > 0:
                    modified_config["top_k"] = top_k
                if rep_penalty != 1.0:
                    modified_config["repetition_penalty"] = rep_penalty
                if min_p > 0:
                    modified_config["min_p"] = min_p
                if seed > 0:
                    modified_config["seed"] = seed

                st.json(modified_config)

        st.markdown("---")
        st.info("💡 **Note:** To permanently save changes, modify `utils/model_config.py` directly. Use the Save button above to store your current selection in session.")

    with tab2:
        st.markdown("### Available Presets")
        st.caption("Pre-configured setups for common scenarios")

        presets = ModelConfig.get_presets()

        for preset_name, preset_config in presets.items():
            with st.expander(f"🎯 {preset_name.upper().replace('_', ' ')}", expanded=False):
                st.markdown(f"**Configuration for: {preset_name}**")

                if not preset_config:
                    st.info("Uses default balanced configuration")
                else:
                    for agent, settings in preset_config.items():
                        st.markdown(f"**{agent.upper()}**:")
                        for key, value in settings.items():
                            st.text(f"  • {key}: {value}")

                st.markdown("---")
                st.markdown("**Usage:**")
                st.code(f'pipeline = FictionPipeline(preset="{preset_name}", ...)', language="python")

    with tab3:
        st.markdown("### Agent Prompts & Instructions")
        st.caption("View the system prompts and capabilities of each agent")

        # Import all pipeline agent classes
        from agents.series_refiner import SeriesRefinerAgent
        from agents.book_outliner import BookOutlinerAgent
        from agents.chapter_developer import ChapterDeveloperAgent
        from agents.scene_developer import SceneDeveloperAgent
        from agents.beat_developer import BeatDeveloperAgent
        from agents.prose_generator import ProseGeneratorAgent
        from agents.lore_master import LoreMasterAgent
        from agents.qa_agent import QAAgent
        from agents.consistency_validator import ConsistencyValidatorAgent
        from agents.developmental_editor import DevelopmentalEditorAgent
        from agents.story_analyst import StoryAnalystAgent

        # Import editor suite agents
        from agents.editors.line_editor import LineEditor
        from agents.editors.scene_editor import SceneEditor
        from agents.editors.chapter_editor import ChapterEditor
        from agents.editors.book_editor import BookEditor
        from agents.editors.series_editor import SeriesEditor
        from agents.editors.copy_editor import CopyEditor

        # Mock LLM for instantiation
        class MockLLM:
            pass

        # Pipeline agents (have get_prompt() method)
        pipeline_agents = {
            "Series Refiner": SeriesRefinerAgent,
            "Book Outliner": BookOutlinerAgent,
            "Chapter Developer": ChapterDeveloperAgent,
            "Scene Developer": SceneDeveloperAgent,
            "Beat Developer": BeatDeveloperAgent,
            "Prose Generator": ProseGeneratorAgent,
            "Lore Master": LoreMasterAgent,
            "QA Agent": QAAgent,
            "Consistency Validator": ConsistencyValidatorAgent,
            "Developmental Editor": DevelopmentalEditorAgent,
            "Story Analyst": StoryAnalystAgent,
        }

        # Editing suite agents (dynamic prompts, show capabilities)
        editing_agents = {
            "Line Editor": (LineEditor, "Sentence-level editing for polish, clarity, and style"),
            "Scene Editor": (SceneEditor, "Scene-level structural and narrative editing"),
            "Chapter Editor": (ChapterEditor, "Chapter-level pacing and structure editing"),
            "Book Editor": (BookEditor, "Book-level arc and consistency editing"),
            "Series Editor": (SeriesEditor, "Series-level continuity and escalation editing"),
            "Copy Editor": (CopyEditor, "Copy editing for grammar, style, and formatting"),
        }

        # Display pipeline agents
        st.markdown("### 🔧 Pipeline Agents")
        st.caption("Core content generation agents with static prompts")

        for agent_name, agent_class in pipeline_agents.items():
            with st.expander(f"📜 {agent_name}", expanded=False):
                try:
                    temp_agent = agent_class(MockLLM())
                    prompt = temp_agent.get_prompt()

                    st.markdown(f"**System Prompt for {agent_name}:**")
                    st.text_area(
                        "Prompt",
                        value=prompt,
                        height=400,
                        key=f"prompt_pipeline_{agent_name}",
                        help="This is the system prompt sent to the LLM"
                    )

                    st.caption(f"📏 Length: {len(prompt)} characters ({len(prompt.split())} words)")

                except Exception as e:
                    st.error(f"Could not load prompt: {e}")

        st.markdown("---")

        # Display editing suite agents
        st.markdown("### ✏️ Editing Suite Agents")
        st.caption("Advanced editing agents with dynamic, context-aware prompts")

        for agent_name, (agent_class, description) in editing_agents.items():
            with st.expander(f"✏️ {agent_name}", expanded=False):
                try:
                    st.markdown(f"**{agent_name}**")
                    st.info(description)

                    # Show docstring
                    if agent_class.__doc__:
                        st.markdown("**Capabilities:**")
                        st.code(agent_class.__doc__.strip(), language="text")

                    # Show methods
                    st.markdown("**Methods:**")
                    st.markdown("- `analyze()`: Analyzes content and returns edit suggestions")
                    st.markdown("- `apply_edit()`: Applies an edit suggestion to the project")

                    st.caption("💡 These agents build prompts dynamically based on context, style guide, and scope")

                except Exception as e:
                    st.error(f"Could not load agent info: {e}")

        st.markdown("---")
        st.info("💡 **Note:** To edit prompts, modify the `get_prompt()` method in each pipeline agent's file or the `analyze()` method in each editor's file. All agent files are located in the `agents/` directory.")

elif page == "Analytics":
    st.markdown('<p class="main-header">Project Analytics</p>', unsafe_allow_html=True)

    if not st.session_state.project:
        st.warning("⚠️ No project loaded")
    else:
        project = st.session_state.project

        st.markdown(f"### {project.series.title}")

        # Word count stats
        col1, col2, col3, col4 = st.columns(4)

        total_books = len(project.series.books)
        total_chapters = sum(len(book.chapters) for book in project.series.books)
        total_scenes = sum(len(ch.scenes) for book in project.series.books for ch in book.chapters)
        total_words = sum(book.current_word_count for book in project.series.books)

        col1.metric("Books", total_books)
        col2.metric("Chapters", total_chapters)
        col3.metric("Scenes", total_scenes)
        col4.metric("Total Words", f"{total_words:,}")

        st.markdown("---")

        # Lore stats
        if project.series.lore:
            st.markdown("### 🎭 Lore Database")

            col1, col2, col3 = st.columns(3)
            col1.metric("Characters", len(project.series.lore.characters))
            col2.metric("Locations", len(project.series.lore.locations))
            col3.metric("World Elements", len(project.series.lore.world_elements))

            # Show characters
            if project.series.lore.characters:
                st.markdown("#### Characters")
                for char in project.series.lore.characters[:10]:
                    with st.expander(f"{char.name} - {char.role}"):
                        st.write(f"**Description:** {char.description}")
                        st.write(f"**Traits:** {', '.join(char.traits)}")

        # Paragraph type analysis
        if project.series.books:
            st.markdown("---")
            st.markdown("### 📝 Prose Analysis")

            para_types = {}
            dialogue_count = 0

            for book in project.series.books:
                for chapter in book.chapters:
                    for scene in chapter.scenes:
                        for beat in scene.beats:
                            if beat.prose and beat.prose.paragraphs:
                                for para in beat.prose.paragraphs:
                                    para_types[para.paragraph_type] = para_types.get(para.paragraph_type, 0) + 1
                                    dialogue_count += len(para.dialogue_lines)

            if para_types:
                st.bar_chart(para_types)
                st.metric("Total Dialogue Lines", dialogue_count)

elif page == "Export":
    st.markdown('<p class="main-header">Export & Download</p>', unsafe_allow_html=True)

    if not st.session_state.project:
        st.warning("⚠️ No project loaded")
    else:
        project = st.session_state.project

        st.markdown(f"### {project.series.title}")

        # Import export utilities
        from utils.export_formatters import (
            MarkdownExporter, EPUBExporter,
            export_project_as_markdown, export_project_as_epub
        )

        # Export Configuration
        st.markdown("#### Export Configuration")

        col_config1, col_config2 = st.columns(2)
        with col_config1:
            export_format = st.selectbox(
                "Export Format",
                ["Markdown (.md)", "EPUB (.epub)", "Both"],
                key="export_format"
            )

        with col_config2:
            author_name = st.text_input(
                "Author Name",
                value="AI Generated",
                key="export_author"
            )

        output_dir = st.text_input(
            "Output Directory",
            value="manuscripts",
            key="export_output_dir"
        )

        st.markdown("---")

        # Book Selection
        st.markdown("#### Select Books to Export")

        if not project.series.books:
            st.warning("No books in series to export")
        else:
            # Option to export all books or select specific ones
            export_all = st.checkbox("Export all books", value=True, key="export_all_books")

            if export_all:
                selected_books = list(range(len(project.series.books)))
            else:
                book_options = [f"Book {b.book_number}: {b.title}" for b in project.series.books]
                selected_book_labels = st.multiselect(
                    "Select books to export",
                    book_options,
                    default=book_options,
                    key="export_selected_books"
                )
                selected_books = [i for i, label in enumerate(book_options) if label in selected_book_labels]

            st.markdown("---")

            # Export Button
            col1, col2, col3 = st.columns([2, 1, 2])

            with col2:
                export_button = st.button("🚀 Export Books", use_container_width=True, type="primary")

            if export_button:
                if not selected_books:
                    st.error("Please select at least one book to export")
                else:
                    with st.spinner("Exporting books..."):
                        try:
                            import os
                            import time
                            os.makedirs(output_dir, exist_ok=True)

                            # Track start time
                            start_time = time.time()

                            exported_files = []

                            # Check EPUB dependency if needed
                            if export_format in ["EPUB (.epub)", "Both"]:
                                try:
                                    import ebooklib
                                except ImportError:
                                    st.error("⚠️ EPUB export requires ebooklib. Install with: pip install ebooklib")
                                    st.stop()

                            # Export each selected book
                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            for idx, book_idx in enumerate(selected_books):
                                book = project.series.books[book_idx]
                                progress = (idx + 1) / len(selected_books)
                                progress_bar.progress(progress)

                                # Calculate elapsed time
                                elapsed_time = time.time() - start_time
                                minutes = int(elapsed_time // 60)
                                seconds = int(elapsed_time % 60)
                                time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

                                # Show percentage and time
                                percentage = int(progress * 100)
                                status_text.text(f"Exporting Book {book.book_number}: {book.title}... {percentage}% - Elapsed: {time_str}")

                                # Export Markdown
                                if export_format in ["Markdown (.md)", "Both"]:
                                    md_path = MarkdownExporter.export_book(
                                        book=book,
                                        output_dir=output_dir,
                                        series_title=project.series.title
                                    )
                                    exported_files.append(md_path)

                                # Export EPUB
                                if export_format in ["EPUB (.epub)", "Both"]:
                                    epub_path = EPUBExporter.export_book(
                                        book=book,
                                        output_dir=output_dir,
                                        series_title=project.series.title,
                                        author_name=author_name
                                    )
                                    exported_files.append(epub_path)

                            # Calculate total runtime
                            total_time = time.time() - start_time
                            minutes = int(total_time // 60)
                            seconds = int(total_time % 60)
                            time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

                            progress_bar.progress(1.0)
                            status_text.text(f"Export complete! 100% - Total time: {time_str}")

                            # Show success message with file list
                            st.success(f"✅ Successfully exported {len(selected_books)} book(s) in {time_str}")

                            st.markdown("#### Exported Files:")
                            for filepath in exported_files:
                                filename = os.path.basename(filepath)
                                st.text(f"✓ {filename}")

                                # Offer download for each file
                                if os.path.exists(filepath):
                                    with open(filepath, 'rb') as f:
                                        file_data = f.read()

                                    st.download_button(
                                        label=f"Download {filename}",
                                        data=file_data,
                                        file_name=filename,
                                        mime="application/epub+zip" if filename.endswith('.epub') else "text/markdown"
                                    )

                        except Exception as e:
                            st.error(f"Export failed: {e}")
                            import traceback
                            st.code(traceback.format_exc())

        st.markdown("---")

        # JSON Export Section
        st.markdown("#### JSON Export")

        json_data = project.model_dump_json(indent=2)
        st.download_button(
            label="Download Project JSON",
            data=json_data,
            file_name=f"{project.metadata.project_id}_export.json",
            mime="application/json"
        )

        st.markdown("---")

        # Preview
        st.markdown("### 📖 Manuscript Preview")

        if project.series.books:
            book = project.series.books[0]
            st.markdown(f"## {book.title}")

            if book.chapters:
                chapter = book.chapters[0]
                st.markdown(f"### Chapter {chapter.chapter_number}: {chapter.title}")

                for scene in chapter.scenes[:1]:  # First scene only
                    for beat in scene.beats[:1]:  # First beat only
                        if beat.prose:
                            if beat.prose.paragraphs:
                                for para in beat.prose.paragraphs[:3]:  # First 3 paragraphs
                                    st.write(para.content)
                            else:
                                st.write(beat.prose.content[:500] + "...")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    Fiction Pipeline v2.0 | Powered by LangChain & OpenRouter
</div>
""", unsafe_allow_html=True)
