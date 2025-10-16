"""
Fiction Pipeline Web UI - Reflex Version
A modern web interface for the fiction generation pipeline
"""

import reflex as rx
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import existing pipeline (no code changes needed)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline import FictionPipeline, create_project_from_concept
from models.schema import FictionProject, Metadata, Series, Lore
from utils.state_manager import StateManager
from utils.model_config import ModelConfig


# Genre list for New Project page
ALL_GENRES = [
    # Standard Genres
    "Science Fiction", "Fantasy", "Urban Fantasy", "Dark Fantasy", "Epic Fantasy",
    "High Fantasy", "Low Fantasy", "Space Opera", "Cyberpunk", "Steampunk",
    "Dystopian", "Post-Apocalyptic", "Time Travel", "Alternate History",
    "Military Science Fiction", "Hard Science Fiction", "Sword and Sorcery",
    "Mystery", "Thriller", "Psychological Thriller", "Crime Fiction",
    "Detective Fiction", "Cozy Mystery", "Legal Thriller", "Spy Thriller",
    "Techno-Thriller", "Romance", "Contemporary Romance", "Paranormal Romance",
    "Romantic Suspense", "Historical Romance", "Regency Romance", "Horror",
    "Gothic Horror", "Psychological Horror", "Supernatural Horror", "Body Horror",
    "Literary Fiction", "Contemporary Fiction", "Historical Fiction",
    "Women's Fiction", "Coming of Age", "Action Adventure", "Military Fiction",
    "Western", "Pirate Adventure", "Young Adult", "Young Adult Fantasy",
    "Young Adult Science Fiction", "Young Adult Romance", "Middle Grade",
    "Humor", "Satire", "Comic Fantasy", "LitRPG", "GameLit", "Portal Fantasy",
    "Progression Fantasy", "Cultivation", "Superhero Fiction", "Magical Realism",
    # NSFW Genres (marked with 🔞)
    "🔞 Erotica", "🔞 Erotic Romance", "🔞 Erotic Fantasy",
    "🔞 Erotic Science Fiction", "🔞 Erotic Horror", "🔞 Erotic Thriller",
    "🔞 Dark Erotica", "🔞 Dark Romance", "🔞 BDSM Romance",
    "🔞 BDSM Erotica", "🔞 Paranormal Erotica", "🔞 Contemporary Erotica",
    "🔞 Historical Erotica", "🔞 Harem", "🔞 Reverse Harem",
    "🔞 Monster Romance", "🔞 Alien Romance", "🔞 Shifter Romance",
    "🔞 Vampire Romance", "🔞 Dragon Romance", "🔞 Omegaverse",
    "🔞 Gay Romance", "🔞 Lesbian Romance", "🔞 MMF Romance",
    "🔞 Menage Romance", "🔞 Fated Mates", "🔞 LitRPG Erotica",
]


class State(rx.State):
    """Main application state"""

    # Authentication
    username: str = ""
    password: str = ""
    is_authenticated: bool = False
    auth_error: str = ""

    # API Configuration
    openrouter_key: str = os.getenv("OPENROUTER_API_KEY", "")
    pinecone_key: str = os.getenv("PINECONE_API_KEY", "")
    use_lore_db: bool = True

    # Model Configuration
    preset: str = "premium_nsfw"
    presets: List[str] = [
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
    ]

    # Project State
    project: Dict[str, Any] = {}
    project_loaded: bool = False
    running: bool = False
    logs: List[str] = []
    auto_loaded: bool = False

    # Navigation
    current_page: str = "home"

    # New Project Form
    new_concept: str = ""
    new_project_id: str = ""
    new_title: str = ""
    new_premise: str = ""
    new_genres: List[str] = ["Fantasy"]
    new_target_audience: str = "adult"
    new_num_books: int = 1
    new_target_word_count: int = 100000
    new_chapters_min: int = 20
    new_chapters_max: int = 26
    new_style_guide: str = ""

    # Step-by-Step State
    current_stage: str = "series"
    stage_running: bool = False

    # Chat State
    chat_messages: List[Dict[str, str]] = []
    chat_input: str = ""

    # Export State
    export_format: str = "markdown"

    # Available projects list
    available_projects: List[str] = []

    # Agent Config State
    editing_agent: str = ""  # Which agent is being edited
    show_agent_details: Dict[str, bool] = {}  # Track which agents are expanded

    def set_username(self, value: str):
        """Set username"""
        self.username = value

    def set_password(self, value: str):
        """Set password"""
        self.password = value

    def check_authentication(self):
        """Check if user credentials are valid"""
        # For now, simple auth - can be enhanced
        if self.username == "admin" and self.password == "admin":
            self.is_authenticated = True
            self.auth_error = ""
            self.auto_load_project()
        else:
            self.is_authenticated = False
            self.auth_error = "Invalid username or password"

    def logout(self):
        """Logout user"""
        self.is_authenticated = False
        self.username = ""
        self.password = ""

    def auto_load_project(self):
        """Auto-load the most recent project"""
        if self.auto_loaded or self.project_loaded:
            return

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
                    self.project = project_data
                    self.project_loaded = True
                    self.logs.append(f"Auto-loaded project: {latest_file}")
                except Exception as e:
                    self.logs.append(f"Failed to auto-load project: {str(e)}")

        self.auto_loaded = True

    def set_page(self, page: str):
        """Navigate to a different page"""
        self.current_page = page

    def update_preset(self, value: str):
        """Update model preset"""
        self.preset = value

    def toggle_lore_db(self):
        """Toggle lore database"""
        self.use_lore_db = not self.use_lore_db

    def set_new_project_id(self, value: str):
        """Set new project ID"""
        self.new_project_id = value

    def set_new_concept(self, value: str):
        """Set new concept"""
        self.new_concept = value

    def set_new_title(self, value: str):
        """Set new title"""
        self.new_title = value

    def set_new_premise(self, value: str):
        """Set new premise"""
        self.new_premise = value

    def set_new_genres(self, value: List[str]):
        """Set new genres"""
        self.new_genres = value

    def set_new_target_audience(self, value: str):
        """Set new target audience"""
        self.new_target_audience = value

    def set_new_num_books(self, value: str):
        """Set new num books"""
        self.new_num_books = int(value)

    def set_new_target_word_count(self, value: str):
        """Set new target word count"""
        self.new_target_word_count = int(value)

    def set_new_chapters_min(self, value: str):
        """Set new chapters min"""
        self.new_chapters_min = int(value)

    def set_new_chapters_max(self, value: str):
        """Set new chapters max"""
        self.new_chapters_max = int(value)

    def set_new_style_guide(self, value: str):
        """Set new style guide"""
        self.new_style_guide = value

    def create_new_project(self):
        """Create a new project from form fields"""
        if not self.new_title or not self.new_premise:
            self.logs.append("Error: Title and Premise are required")
            return

        if not self.openrouter_key:
            self.logs.append("Error: OpenRouter API Key required")
            return

        try:
            # Generate project_id from title
            import re
            slug = self.new_title.lower()
            slug = re.sub(r'[^\w\s-]', '', slug)
            slug = re.sub(r'[-\s]+', '_', slug)
            slug = slug.strip('_')
            date_str = datetime.now().strftime('%Y%m%d')
            project_id = f"{slug}_{date_str}"

            # Create genre string from selection
            genre = " / ".join(self.new_genres) if self.new_genres else "Fantasy"

            # Create project
            project_obj = FictionProject(
                metadata=Metadata(
                    last_updated=datetime.now(),
                    last_updated_by="WebUI",
                    processing_stage="series",
                    status="draft",
                    project_id=project_id,
                    iteration=1
                ),
                series=Series(
                    title=self.new_title,
                    premise=self.new_premise,
                    genre=genre,
                    target_audience=self.new_target_audience,
                    themes=[],
                    persistent_threads=[],
                    lore=Lore(),
                    books=[],
                    style_guide=self.new_style_guide
                )
            )

            # Store requirements in project metadata
            chapters_range_str = f"{self.new_chapters_min}-{self.new_chapters_max}"
            project_obj.metadata.project_id = f"{project_id}__{self.new_num_books}books_{chapters_range_str}ch_{self.new_target_word_count}w"

            # Save state
            state_manager = StateManager("output")
            state_manager.save_state(project_obj, "initial")

            # Update state
            self.project = project_obj.model_dump()
            self.project_loaded = True

            self.logs.append(f"Created new project: {project_id}")
            self.logs.append(f"Saved to: output/{project_obj.metadata.project_id}_state.json")
            self.current_page = "step_by_step"
        except Exception as e:
            self.logs.append(f"Error creating project: {str(e)}")

    def load_project(self, filename: str):
        """Load a project from file"""
        try:
            file_path = os.path.join("output", filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            self.project = project_data
            self.project_loaded = True
            self.logs.append(f"Loaded project: {filename}")
            self.current_page = "project_manager"
        except Exception as e:
            self.logs.append(f"Error loading project: {str(e)}")

    def load_available_projects(self):
        """Load list of available project files"""
        output_dir = "output"
        if not os.path.exists(output_dir):
            self.available_projects = []
            return
        self.available_projects = [f for f in os.listdir(output_dir) if f.endswith("_state.json")]

    @rx.var
    def project_id(self) -> str:
        """Get project ID from loaded project"""
        if not self.project_loaded or not self.project:
            return "No project loaded"
        return self.project.get("metadata", {}).get("project_id", "Unknown")

    @rx.var
    def project_status(self) -> str:
        """Get project status"""
        if not self.project_loaded or not self.project:
            return "No project loaded"
        return self.project.get("metadata", {}).get("status", "Unknown")

    @rx.var
    def project_stage(self) -> str:
        """Get processing stage"""
        if not self.project_loaded or not self.project:
            return "Unknown"
        return self.project.get("metadata", {}).get("processing_stage", "Unknown")

    @rx.var
    def project_last_updated(self) -> str:
        """Get last updated timestamp"""
        if not self.project_loaded or not self.project:
            return "Unknown"
        return str(self.project.get("metadata", {}).get("last_updated", "Unknown"))

    @rx.var
    def series_title(self) -> str:
        """Get series title"""
        if not self.project_loaded or not self.project:
            return "Unknown"
        return self.project.get("series", {}).get("title", "Unknown")

    @rx.var
    def series_genre(self) -> str:
        """Get series genre"""
        if not self.project_loaded or not self.project:
            return "Unknown"
        return self.project.get("series", {}).get("genre", "Unknown")

    @rx.var
    def series_books_count(self) -> int:
        """Get number of books"""
        if not self.project_loaded or not self.project:
            return 0
        return len(self.project.get("series", {}).get("books", []))


# Shared Components

def navbar() -> rx.Component:
    """Top navigation bar"""
    return rx.box(
        rx.hstack(
            rx.heading("Fiction Pipeline", size="7"),
            rx.spacer(),
            rx.button(
                "Logout",
                on_click=State.logout,
                variant="soft",
                color_scheme="gray"
            ),
            padding="1rem",
            width="100%",
        ),
        bg=rx.color("accent", 3),
        width="100%",
    )


def sidebar() -> rx.Component:
    """Side navigation menu"""
    return rx.box(
        rx.vstack(
            rx.heading("Navigation", size="5", margin_bottom="1rem"),

            # Navigation buttons
            rx.button("Home", on_click=lambda: State.set_page("home"), width="100%", variant="soft"),
            rx.button("New Project", on_click=lambda: State.set_page("new_project"), width="100%", variant="soft"),
            rx.button("Load Project", on_click=lambda: State.set_page("load_project"), width="100%", variant="soft"),
            rx.button("Project Manager", on_click=lambda: State.set_page("project_manager"), width="100%", variant="soft"),
            rx.button("Stage Viewer", on_click=lambda: State.set_page("stage_viewer"), width="100%", variant="soft"),
            rx.button("Step-by-Step", on_click=lambda: State.set_page("step_by_step"), width="100%", variant="soft"),
            rx.button("Prose Reader", on_click=lambda: State.set_page("prose_reader"), width="100%", variant="soft"),
            rx.button("Editing Suite", on_click=lambda: State.set_page("editing_suite"), width="100%", variant="soft"),
            rx.button("Chat", on_click=lambda: State.set_page("chat"), width="100%", variant="soft"),
            rx.button("Settings", on_click=lambda: State.set_page("settings"), width="100%", variant="soft"),
            rx.button("Agent Config", on_click=lambda: State.set_page("agent_config"), width="100%", variant="soft"),
            rx.button("Analytics", on_click=lambda: State.set_page("analytics"), width="100%", variant="soft"),
            rx.button("Export", on_click=lambda: State.set_page("export"), width="100%", variant="soft"),

            rx.divider(margin_y="1rem"),

            # API Configuration
            rx.heading("API Configuration", size="4", margin_bottom="0.5rem"),
            rx.cond(
                State.openrouter_key != "",
                rx.text("OpenRouter: ✓", size="2", color="green"),
                rx.text("OpenRouter: ✗", size="2", color="red"),
            ),
            rx.cond(
                State.pinecone_key != "",
                rx.text("Pinecone: ✓", size="2", color="green"),
                rx.text("Pinecone: ✗", size="2", color="red"),
            ),

            rx.divider(margin_y="1rem"),

            # Model Configuration
            rx.heading("Model Config", size="4", margin_bottom="0.5rem"),
            rx.select(
                State.presets,
                value=State.preset,
                on_change=State.update_preset,
                width="100%",
            ),
            rx.checkbox(
                "Enable Lore DB",
                checked=State.use_lore_db,
                on_change=State.toggle_lore_db,
            ),

            spacing="2",
            width="100%",
        ),
        padding="1rem",
        width="250px",
        height="100vh",
        bg=rx.color("gray", 2),
        overflow_y="auto",
    )


# Page Components

def home_page() -> rx.Component:
    """Home page"""
    return rx.vstack(
        rx.heading("Welcome to Fiction Pipeline", size="8"),
        rx.text(
            "A complete fiction generation pipeline from concept to manuscript",
            size="5",
            margin_bottom="2rem",
        ),

        rx.card(
            rx.vstack(
                rx.heading("Quick Start", size="6"),
                rx.text("1. Create a new project or load an existing one", margin_top="1rem"),
                rx.text("2. Configure your model preferences in the sidebar"),
                rx.text("3. Run the pipeline or use step-by-step mode"),
                rx.text("4. Export your completed manuscript"),
                spacing="2",
                align_items="start",
            ),
            width="100%",
            max_width="600px",
        ),

        rx.cond(
            State.project_loaded,
            rx.card(
                rx.vstack(
                    rx.heading("Current Project", size="6"),
                    rx.text("Project ID: ", State.project_id),
                    rx.text("Status: ", State.project_status),
                    rx.button(
                        "Open Project Manager",
                        on_click=lambda: State.set_page("project_manager"),
                        margin_top="1rem",
                    ),
                    spacing="2",
                    align_items="start",
                ),
                width="100%",
                max_width="600px",
                margin_top="2rem",
            ),
        ),

        spacing="4",
        align_items="center",
        padding="2rem",
        width="100%",
    )


def new_project_page() -> rx.Component:
    """New project page"""
    return rx.vstack(
        rx.heading("Create New Project", size="7"),

        rx.card(
            rx.vstack(
                rx.heading("Series Information", size="5"),

                # Two-column layout for basic info
                rx.hstack(
                    # Left column
                    rx.vstack(
                        rx.text("Series Title", weight="bold"),
                        rx.input(
                            placeholder="The Quantum Heist",
                            value=State.new_title,
                            on_change=State.set_new_title,
                            width="100%",
                        ),

                        rx.text("Genre(s)", weight="bold", margin_top="1rem"),
                        rx.text("Select one or blend multiple", size="2", color="gray"),
                        rx.select(
                            ALL_GENRES,
                            placeholder="Select genres",
                            default_value="Fantasy",
                            on_change=lambda val: State.set_new_genres([val]),
                            width="100%",
                        ),
                        rx.text("🔞 = Mature/NSFW content", size="1", color="gray"),

                        spacing="2",
                        width="100%",
                        align_items="start",
                    ),

                    # Right column
                    rx.vstack(
                        rx.text("Target Audience", weight="bold"),
                        rx.select(
                            ["adult", "young adult", "middle grade"],
                            value=State.new_target_audience,
                            on_change=State.set_new_target_audience,
                            width="100%",
                        ),

                        rx.text("Number of Books", weight="bold", margin_top="1rem"),
                        rx.input(
                            type="number",
                            value=str(State.new_num_books),
                            on_change=State.set_new_num_books,
                            min=1,
                            max=25,
                            width="100%",
                        ),

                        rx.text("Target Word Count per Book", weight="bold", margin_top="1rem"),
                        rx.input(
                            type="number",
                            value=str(State.new_target_word_count),
                            on_change=State.set_new_target_word_count,
                            min=50000,
                            max=200000,
                            step=10000,
                            width="100%",
                        ),

                        spacing="2",
                        width="100%",
                        align_items="start",
                    ),

                    spacing="4",
                    width="100%",
                    align_items="start",
                ),

                # Chapters per book range
                rx.text("Chapters per Book (range)", weight="bold", margin_top="1rem"),
                rx.hstack(
                    rx.vstack(
                        rx.text("Min", size="2", weight="bold"),
                        rx.input(
                            type="number",
                            value=str(State.new_chapters_min),
                            on_change=State.set_new_chapters_min,
                            min=5,
                            max=50,
                            width="100%",
                        ),
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Max", size="2", weight="bold"),
                        rx.input(
                            type="number",
                            value=str(State.new_chapters_max),
                            on_change=State.set_new_chapters_max,
                            min=5,
                            max=50,
                            width="100%",
                        ),
                        width="100%",
                    ),
                    spacing="2",
                    width="100%",
                ),

                # Premise
                rx.text("Series Premise", weight="bold", margin_top="1rem"),
                rx.text_area(
                    placeholder="A team of specialists must steal an impossible artifact from a time-locked vault.",
                    value=State.new_premise,
                    on_change=State.set_new_premise,
                    width="100%",
                    height="100px",
                ),

                spacing="3",
                align_items="start",
                width="100%",
            ),
            width="100%",
            max_width="1000px",
        ),

        # Style Guide Section
        rx.card(
            rx.vstack(
                rx.heading("Prose Style Guide (Optional)", size="5"),
                rx.text("Define the prose style for your series", size="3", color="gray"),

                rx.text_area(
                    placeholder="""Paste your style guide here, or type directly.

Examples:
- Write in the style of Brandon Sanderson with clear magic system explanations
- Use short, punchy sentences for action scenes
- Include vivid sensory details, especially smell and touch
- Favor showing over telling
- Character dialogue should be sharp and witty
- Avoid adverbs in dialogue tags

Leave blank to use default prose generation.""",
                    value=State.new_style_guide,
                    on_change=State.set_new_style_guide,
                    width="100%",
                    height="200px",
                ),

                rx.cond(
                    State.new_style_guide != "",
                    rx.text(
                        f"Word count: {len(State.new_style_guide.split())} words • {len(State.new_style_guide)} characters",
                        size="2",
                        color="gray"
                    ),
                ),

                spacing="3",
                align_items="start",
                width="100%",
            ),
            width="100%",
            max_width="1000px",
            margin_top="1rem",
        ),

        # Create button
        rx.button(
            "Create Project",
            on_click=State.create_new_project,
            size="3",
            width="100%",
            max_width="1000px",
        ),

        spacing="4",
        padding="2rem",
        width="100%",
        align_items="start",
    )


def load_project_page() -> rx.Component:
    """Load project page"""
    return rx.vstack(
        rx.heading("Load Project", size="7"),

        rx.card(
            rx.vstack(
                rx.heading("Available Projects", size="5"),
                rx.button("Refresh Project List", on_click=State.load_available_projects, margin_bottom="1rem"),

                rx.cond(
                    State.available_projects.length() > 0,
                    rx.vstack(
                        rx.foreach(
                            State.available_projects,
                            lambda p: rx.button(
                                p,
                                on_click=lambda: State.load_project(p),
                                width="100%",
                                variant="soft",
                            ),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.text("No projects found. Create a new project to get started or click Refresh."),
                ),

                spacing="3",
                align_items="start",
                width="100%",
            ),
            width="100%",
            max_width="800px",
        ),

        on_mount=State.load_available_projects,
        spacing="4",
        padding="2rem",
        width="100%",
        align_items="start",
    )


def project_manager_page() -> rx.Component:
    """Project manager page"""
    return rx.vstack(
        rx.heading("Project Manager", size="7"),

        rx.cond(
            State.project_loaded,
            rx.vstack(
                rx.card(
                    rx.vstack(
                        rx.heading("Project Information", size="5"),
                        rx.text("Project ID: ", State.project_id),
                        rx.text("Status: ", State.project_status),
                        rx.text("Stage: ", State.project_stage),
                        rx.text("Last Updated: ", State.project_last_updated),
                        spacing="2",
                        align_items="start",
                    ),
                    width="100%",
                ),

                rx.card(
                    rx.vstack(
                        rx.heading("Series Information", size="5"),
                        rx.text("Title: ", State.series_title),
                        rx.text("Genre: ", State.series_genre),
                        rx.text("Books: ", State.series_books_count),
                        spacing="2",
                        align_items="start",
                    ),
                    width="100%",
                    margin_top="1rem",
                ),

                spacing="3",
                width="100%",
                max_width="800px",
            ),
            rx.text("No project loaded. Create or load a project first."),
        ),

        spacing="4",
        padding="2rem",
        width="100%",
        align_items="start",
    )


def settings_page() -> rx.Component:
    """Settings page"""
    return rx.vstack(
        rx.heading("Settings", size="7"),

        rx.card(
            rx.vstack(
                rx.heading("API Keys", size="5"),
                rx.text("Configure your API keys here", size="3", color="gray"),

                rx.vstack(
                    rx.text("OpenRouter API Key", weight="bold"),
                    rx.input(
                        type="password",
                        placeholder="sk-...",
                        value=State.openrouter_key,
                        width="100%",
                    ),

                    rx.text("Pinecone API Key", weight="bold", margin_top="1rem"),
                    rx.input(
                        type="password",
                        placeholder="...",
                        value=State.pinecone_key,
                        width="100%",
                    ),

                    spacing="2",
                    width="100%",
                ),

                spacing="3",
                align_items="start",
                width="100%",
            ),
            width="100%",
            max_width="800px",
        ),

        spacing="4",
        padding="2rem",
        width="100%",
        align_items="start",
    )


def stage_viewer_page() -> rx.Component:
    """Stage viewer page"""
    return rx.vstack(
        rx.heading("Stage Viewer", size="7"),

        rx.cond(
            State.project_loaded,
            rx.vstack(
                # Project overview
                rx.card(
                    rx.vstack(
                        rx.heading("Project Overview", size="5"),
                        rx.hstack(
                            rx.vstack(
                                rx.text("Series: ", State.series_title, weight="bold"),
                                rx.text("Stage: ", State.project_stage),
                                align_items="start",
                            ),
                            rx.vstack(
                                rx.text("Status: ", State.project_status),
                                rx.text("Books: ", State.series_books_count),
                                align_items="start",
                            ),
                            spacing="4",
                        ),
                        spacing="2",
                        align_items="start",
                    ),
                    width="100%",
                ),

                # Stage selector
                rx.text("Select Stage to View", weight="bold", margin_top="1rem"),
                rx.select(
                    ["Series Outline", "Lore Database", "Book Outlines", "Chapter Outlines", "Scene Outlines", "Beat Development", "Prose Content", "QA Reports"],
                    placeholder="Select a stage",
                    width="100%",
                ),

                rx.divider(),

                rx.text("Stage content will be displayed here", color="gray"),

                spacing="3",
                width="100%",
                max_width="1000px",
            ),
            rx.text("No project loaded. Create or load a project first."),
        ),

        spacing="4",
        padding="2rem",
        width="100%",
        align_items="start",
    )


def prose_reader_page() -> rx.Component:
    """Prose reader page"""
    return rx.vstack(
        rx.heading("Prose Reader", size="7"),

        rx.cond(
            State.project_loaded,
            rx.vstack(
                rx.text("Reading: ", State.series_title, weight="bold"),

                rx.card(
                    rx.vstack(
                        rx.text("Book Selection", weight="bold"),
                        rx.select(
                            ["Book 1"],  # TODO: Make dynamic
                            placeholder="Select a book",
                            width="100%",
                        ),

                        rx.text("Chapter Selection", weight="bold", margin_top="1rem"),
                        rx.select(
                            ["All Chapters"],  # TODO: Make dynamic
                            placeholder="Select a chapter",
                            width="100%",
                        ),

                        rx.divider(),

                        rx.hstack(
                            rx.checkbox("Show Chapter Titles"),
                            rx.checkbox("Show Scene Breaks"),
                            spacing="4",
                        ),

                        rx.divider(),

                        rx.heading("Prose Content", size="5"),
                        rx.text("Generated prose will appear here once scenes are generated.", color="gray"),

                        spacing="3",
                        align_items="start",
                        width="100%",
                    ),
                    width="100%",
                ),

                spacing="3",
                width="100%",
                max_width="1000px",
            ),
            rx.text("No project loaded. Create or load a project first."),
        ),

        spacing="4",
        padding="2rem",
        width="100%",
        align_items="start",
    )


def analytics_page() -> rx.Component:
    """Analytics page"""
    return rx.vstack(
        rx.heading("Project Analytics", size="7"),

        rx.cond(
            State.project_loaded,
            rx.vstack(
                rx.heading(State.series_title, size="6"),

                # Stats overview
                rx.card(
                    rx.vstack(
                        rx.heading("Overview", size="5"),
                        rx.hstack(
                            rx.vstack(
                                rx.text("Books", weight="bold"),
                                rx.text(State.series_books_count, size="6"),
                                align_items="center",
                            ),
                            rx.vstack(
                                rx.text("Chapters", weight="bold"),
                                rx.text("0", size="6"),  # TODO: Calculate
                                align_items="center",
                            ),
                            rx.vstack(
                                rx.text("Scenes", weight="bold"),
                                rx.text("0", size="6"),  # TODO: Calculate
                                align_items="center",
                            ),
                            rx.vstack(
                                rx.text("Total Words", weight="bold"),
                                rx.text("0", size="6"),  # TODO: Calculate
                                align_items="center",
                            ),
                            spacing="4",
                            justify="between",
                            width="100%",
                        ),
                        spacing="3",
                        align_items="start",
                    ),
                    width="100%",
                ),

                # Lore stats
                rx.card(
                    rx.vstack(
                        rx.heading("Lore Database", size="5"),
                        rx.hstack(
                            rx.vstack(
                                rx.text("Characters", weight="bold"),
                                rx.text("0", size="4"),  # TODO: Calculate
                                align_items="center",
                            ),
                            rx.vstack(
                                rx.text("Locations", weight="bold"),
                                rx.text("0", size="4"),  # TODO: Calculate
                                align_items="center",
                            ),
                            rx.vstack(
                                rx.text("World Elements", weight="bold"),
                                rx.text("0", size="4"),  # TODO: Calculate
                                align_items="center",
                            ),
                            spacing="4",
                            justify="between",
                            width="100%",
                        ),
                        spacing="3",
                        align_items="start",
                    ),
                    width="100%",
                    margin_top="1rem",
                ),

                spacing="3",
                width="100%",
                max_width="1000px",
            ),
            rx.text("No project loaded. Create or load a project first."),
        ),

        spacing="4",
        padding="2rem",
        width="100%",
        align_items="start",
    )


def export_page() -> rx.Component:
    """Export page"""
    return rx.vstack(
        rx.heading("Export Project", size="7"),

        rx.cond(
            State.project_loaded,
            rx.vstack(
                rx.text("Export: ", State.series_title, weight="bold"),

                rx.card(
                    rx.vstack(
                        rx.heading("Export Options", size="5"),

                        rx.text("Select Format", weight="bold"),
                        rx.radio_group(
                            ["Markdown", "Plain Text", "JSON", "EPUB (Coming Soon)"],
                            default_value="Markdown",
                        ),

                        rx.text("Select Content", weight="bold", margin_top="1rem"),
                        rx.checkbox("Include Series Outline"),
                        rx.checkbox("Include Lore Database"),
                        rx.checkbox("Include All Prose", default_checked=True),
                        rx.checkbox("Include QA Reports"),

                        rx.divider(),

                        rx.button(
                            "Export Project",
                            size="3",
                            width="100%",
                        ),

                        spacing="3",
                        align_items="start",
                        width="100%",
                    ),
                    width="100%",
                ),

                spacing="3",
                width="100%",
                max_width="800px",
            ),
            rx.text("No project loaded. Create or load a project first."),
        ),

        spacing="4",
        padding="2rem",
        width="100%",
        align_items="start",
    )


def chat_page() -> rx.Component:
    """Chat page"""
    return rx.vstack(
        rx.heading("Series Chat", size="7"),

        rx.cond(
            State.project_loaded,
            rx.vstack(
                rx.text("Chatting about: ", State.series_title, weight="bold"),

                rx.card(
                    rx.vstack(
                        rx.heading("Chat Interface", size="5"),
                        rx.text("Ask questions about your series, characters, plot, etc.", color="gray"),

                        rx.divider(),

                        # Chat history placeholder
                        rx.box(
                            rx.text("Chat history will appear here", color="gray", size="2"),
                            height="300px",
                            width="100%",
                            padding="1rem",
                            border="1px solid",
                            border_color=rx.color("gray", 6),
                            border_radius="0.5rem",
                        ),

                        # Chat input
                        rx.text_area(
                            placeholder="Ask a question about your series...",
                            height="100px",
                            width="100%",
                        ),

                        rx.hstack(
                            rx.button("Send", size="3"),
                            rx.button("Clear Chat", size="3", variant="soft"),
                            spacing="2",
                        ),

                        spacing="3",
                        align_items="start",
                        width="100%",
                    ),
                    width="100%",
                ),

                spacing="3",
                width="100%",
                max_width="1000px",
            ),
            rx.text("No project loaded. Create or load a project first."),
        ),

        spacing="4",
        padding="2rem",
        width="100%",
        align_items="start",
    )


def editing_suite_page() -> rx.Component:
    """Editing suite page"""
    return rx.vstack(
        rx.heading("Editing Suite", size="7"),

        rx.cond(
            State.project_loaded,
            rx.vstack(
                rx.text("Editing: ", State.series_title, weight="bold"),

                rx.card(
                    rx.vstack(
                        rx.heading("Select Editor", size="5"),

                        rx.select(
                            [
                                "Line Editor (Sentence-level)",
                                "Scene Editor (Coming soon)",
                                "Chapter Editor (Coming soon)",
                                "Book Editor (Coming soon)",
                                "Series Editor (Coming soon)",
                            ],
                            placeholder="Select editor type",
                            width="100%",
                        ),

                        rx.divider(),

                        rx.text("Line Editor Configuration", weight="bold"),
                        rx.text("Select the scope of content to edit:", size="2"),

                        rx.hstack(
                            rx.select(["Book 1"], placeholder="Select Book", width="100%"),
                            rx.select(["Chapter 1"], placeholder="Select Chapter", width="100%"),
                            rx.select(["Scene 1"], placeholder="Select Scene", width="100%"),
                            spacing="2",
                            width="100%",
                        ),

                        rx.divider(),

                        rx.button("Analyze This Scene", size="3", width="100%"),

                        spacing="3",
                        align_items="start",
                        width="100%",
                    ),
                    width="100%",
                ),

                spacing="3",
                width="100%",
                max_width="1000px",
            ),
            rx.text("No project loaded. Create or load a project first."),
        ),

        spacing="4",
        padding="2rem",
        width="100%",
        align_items="start",
    )


def step_by_step_page() -> rx.Component:
    """Step-by-step agent execution page"""
    return rx.vstack(
        rx.heading("Step-by-Step Agent Execution", size="7"),

        rx.cond(
            State.project_loaded,
            rx.vstack(
                rx.text("Project: ", State.series_title, " | Stage: ", State.project_stage, " | Status: ", State.project_status, weight="bold"),

                # Progress overview
                rx.card(
                    rx.vstack(
                        rx.heading("Progress Overview", size="5"),
                        rx.hstack(
                            rx.vstack(
                                rx.text("Books", weight="bold"),
                                rx.text(State.series_books_count, size="4"),
                                align_items="center",
                            ),
                            rx.vstack(
                                rx.text("Chapters", weight="bold"),
                                rx.text("0", size="4"),
                                align_items="center",
                            ),
                            rx.vstack(
                                rx.text("Scenes", weight="bold"),
                                rx.text("0", size="4"),
                                align_items="center",
                            ),
                            rx.vstack(
                                rx.text("Lore Items", weight="bold"),
                                rx.text("0", size="4"),
                                align_items="center",
                            ),
                            spacing="4",
                            justify="between",
                            width="100%",
                        ),
                        spacing="2",
                        align_items="start",
                    ),
                    width="100%",
                ),

                # Agent pipeline
                rx.card(
                    rx.vstack(
                        rx.heading("Available Agents", size="5"),
                        rx.text("Run agents one at a time to control the generation process", size="3", color="gray"),

                        rx.divider(),

                        # Agent list - ALL 7 agents
                        rx.vstack(
                            # Series Refiner
                            rx.card(
                                rx.hstack(
                                    rx.vstack(
                                        rx.text("Series Refiner", weight="bold"),
                                        rx.text("Expands series concept into detailed outline with lore and book premises", size="2", color="gray"),
                                        align_items="start",
                                    ),
                                    rx.button("Run", size="2"),
                                    justify="between",
                                    width="100%",
                                ),
                                width="100%",
                            ),
                            # Book Outliner
                            rx.card(
                                rx.hstack(
                                    rx.vstack(
                                        rx.text("Book Outliner", weight="bold"),
                                        rx.text("Creates 3-act structure, character arcs, and chapter outlines", size="2", color="gray"),
                                        align_items="start",
                                    ),
                                    rx.button("Run", size="2", disabled=True),
                                    justify="between",
                                    width="100%",
                                ),
                                width="100%",
                            ),
                            # Chapter Developer
                            rx.card(
                                rx.hstack(
                                    rx.vstack(
                                        rx.text("Chapter Developer", weight="bold"),
                                        rx.text("Breaks chapters into detailed scenes with narrative structure", size="2", color="gray"),
                                        align_items="start",
                                    ),
                                    rx.button("Run", size="2", disabled=True),
                                    justify="between",
                                    width="100%",
                                ),
                                width="100%",
                            ),
                            # Scene Developer
                            rx.card(
                                rx.hstack(
                                    rx.vstack(
                                        rx.text("Scene Developer", weight="bold"),
                                        rx.text("Develops scenes into story beats with timing and pacing", size="2", color="gray"),
                                        align_items="start",
                                    ),
                                    rx.button("Run", size="2", disabled=True),
                                    justify="between",
                                    width="100%",
                                ),
                                width="100%",
                            ),
                            # Prose Generator
                            rx.card(
                                rx.hstack(
                                    rx.vstack(
                                        rx.text("Prose Generator", weight="bold"),
                                        rx.text("Generates actual prose from beats using style guide", size="2", color="gray"),
                                        align_items="start",
                                    ),
                                    rx.button("Run", size="2", disabled=True),
                                    justify="between",
                                    width="100%",
                                ),
                                width="100%",
                            ),
                            # QA Agent
                            rx.card(
                                rx.hstack(
                                    rx.vstack(
                                        rx.text("QA Agent", weight="bold"),
                                        rx.text("Quality assurance and validation of generated content", size="2", color="gray"),
                                        align_items="start",
                                    ),
                                    rx.button("Run", size="2"),
                                    justify="between",
                                    width="100%",
                                ),
                                width="100%",
                            ),
                            # Lore Master
                            rx.card(
                                rx.hstack(
                                    rx.vstack(
                                        rx.text("Lore Master", weight="bold"),
                                        rx.text("Validates lore consistency and detects new lore elements", size="2", color="gray"),
                                        align_items="start",
                                    ),
                                    rx.button("Run", size="2"),
                                    justify="between",
                                    width="100%",
                                ),
                                width="100%",
                            ),
                            spacing="2",
                            width="100%",
                        ),

                        spacing="3",
                        align_items="start",
                        width="100%",
                    ),
                    width="100%",
                    margin_top="1rem",
                ),

                # Auto QA toggle
                rx.card(
                    rx.vstack(
                        rx.checkbox(
                            "Enable Auto Quality Gates",
                            default_checked=True,
                        ),
                        rx.text("Automatically run QA + Lore validation after each content generation agent", size="2", color="gray"),
                        spacing="2",
                        align_items="start",
                    ),
                    width="100%",
                    margin_top="1rem",
                ),

                spacing="3",
                width="100%",
                max_width="1000px",
            ),
            rx.text("No project loaded. Create or load a project first."),
        ),

        spacing="4",
        padding="2rem",
        width="100%",
        align_items="start",
    )


def agent_config_page() -> rx.Component:
    """Agent configuration page"""

    # Define agent configurations
    agents = [
        {
            "name": "Series Refiner",
            "key": "series",
            "badge": "Core",
            "badge_color": "green",
            "model": "anthropic/claude-3.5-sonnet",
            "temp": 0.7,
            "max_tokens": 4000,
            "description": "Expands series concept into detailed outline with lore"
        },
        {
            "name": "Book Outliner",
            "key": "book",
            "badge": "Core",
            "badge_color": "green",
            "model": "anthropic/claude-3.5-sonnet",
            "temp": 0.7,
            "max_tokens": 4000,
            "description": "Creates 3-act structure and chapter outlines"
        },
        {
            "name": "Chapter Developer",
            "key": "chapter",
            "badge": "Core",
            "badge_color": "green",
            "model": "anthropic/claude-3.5-sonnet",
            "temp": 0.7,
            "max_tokens": 4000,
            "description": "Breaks chapters into detailed scenes"
        },
        {
            "name": "Scene Developer",
            "key": "scene",
            "badge": "Core",
            "badge_color": "green",
            "model": "anthropic/claude-3.5-sonnet",
            "temp": 0.7,
            "max_tokens": 4000,
            "description": "Develops scenes into story beats"
        },
        {
            "name": "Prose Generator",
            "key": "prose",
            "badge": "Content",
            "badge_color": "blue",
            "model": "Based on preset",
            "temp": 0.8,
            "max_tokens": 2000,
            "description": "Generates actual prose from beats"
        },
        {
            "name": "QA Agent",
            "key": "qa",
            "badge": "Quality",
            "badge_color": "orange",
            "model": "anthropic/claude-3.5-sonnet",
            "temp": 0.3,
            "max_tokens": 2000,
            "description": "Quality assurance and validation"
        },
        {
            "name": "Lore Master",
            "key": "lore",
            "badge": "Quality",
            "badge_color": "orange",
            "model": "anthropic/claude-3.5-sonnet",
            "temp": 0.3,
            "max_tokens": 2000,
            "description": "Validates lore consistency"
        },
    ]

    return rx.vstack(
        rx.heading("Agent Configuration", size="7"),
        rx.text("Configure models, parameters, and prompts for all pipeline agents", size="3", color="gray"),

        # Preset selector
        rx.card(
            rx.vstack(
                rx.heading("Model Preset", size="5"),
                rx.text("Select a preset configuration for all agents", size="3", color="gray"),

                rx.divider(),

                rx.hstack(
                    rx.text("Current Preset:", weight="bold"),
                    rx.badge(State.preset, color_scheme="blue", size="3"),
                    spacing="2",
                ),

                rx.select(
                    State.presets,
                    value=State.preset,
                    on_change=State.update_preset,
                    width="100%",
                ),

                spacing="3",
                align_items="start",
                width="100%",
            ),
            width="100%",
            max_width="1000px",
        ),

        # Pipeline Agents Configuration
        rx.card(
            rx.vstack(
                rx.heading("Pipeline Agents", size="5"),
                rx.text("Click any agent to view/edit configuration", size="3", color="gray"),

                rx.divider(),

                # Generate agent accordions
                rx.accordion.root(
                    *[
                        rx.accordion.item(
                            header=rx.hstack(
                                rx.text(agent["name"], weight="bold", size="4"),
                                rx.badge(agent["badge"], color_scheme=agent["badge_color"]),
                                spacing="2",
                            ),
                            content=rx.vstack(
                                rx.text("Current Configuration:", weight="bold", margin_top="0.5rem"),
                                rx.vstack(
                                    rx.hstack(
                                        rx.text("Model:", weight="bold", size="2"),
                                        rx.text(agent["model"], size="2", color="gray"),
                                        spacing="2",
                                    ),
                                    rx.hstack(
                                        rx.text("Temperature:", weight="bold", size="2"),
                                        rx.text(str(agent["temp"]), size="2", color="gray"),
                                        spacing="2",
                                    ),
                                    rx.hstack(
                                        rx.text("Max Tokens:", weight="bold", size="2"),
                                        rx.text(str(agent["max_tokens"]), size="2", color="gray"),
                                        spacing="2",
                                    ),
                                    rx.hstack(
                                        rx.text("Description:", weight="bold", size="2"),
                                        rx.text(agent["description"], size="2", color="gray"),
                                        spacing="2",
                                    ),
                                    spacing="1",
                                    align_items="start",
                                    padding="0.5rem",
                                    border_radius="0.5rem",
                                    bg=rx.color("gray", 2),
                                    width="100%",
                                ),

                                rx.divider(),

                                rx.text("Edit Configuration:", weight="bold", margin_top="0.5rem"),
                                rx.vstack(
                                    rx.text("Model", size="2", weight="bold"),
                                    rx.input(
                                        placeholder="e.g., anthropic/claude-3.5-sonnet",
                                        default_value=agent["model"],
                                        width="100%",
                                    ),

                                    rx.hstack(
                                        rx.vstack(
                                            rx.text("Temperature", size="2", weight="bold"),
                                            rx.input(
                                                type="number",
                                                placeholder="0.7",
                                                default_value=str(agent["temp"]),
                                                width="100%",
                                                step=0.1,
                                                min=0,
                                                max=2,
                                            ),
                                            width="100%",
                                        ),
                                        rx.vstack(
                                            rx.text("Max Tokens", size="2", weight="bold"),
                                            rx.input(
                                                type="number",
                                                placeholder="4000",
                                                default_value=str(agent["max_tokens"]),
                                                width="100%",
                                                step=100,
                                            ),
                                            width="100%",
                                        ),
                                        spacing="2",
                                        width="100%",
                                    ),

                                    rx.button(
                                        "Save Configuration",
                                        size="2",
                                        width="100%",
                                        margin_top="0.5rem",
                                    ),

                                    spacing="2",
                                    align_items="start",
                                    width="100%",
                                ),

                                spacing="2",
                                align_items="start",
                                width="100%",
                            ),
                            value=agent["key"],
                        )
                        for agent in agents
                    ],
                    collapsible=True,
                    width="100%",
                    variant="ghost",
                ),

                spacing="3",
                align_items="start",
                width="100%",
            ),
            width="100%",
            max_width="1000px",
            margin_top="1rem",
        ),

        # Editing Suite Agents
        rx.card(
            rx.vstack(
                rx.heading("Editing Suite Agents", size="5"),
                rx.text("Models for post-generation editing and refinement", size="3", color="gray"),

                rx.divider(),

                rx.accordion.root(
                    rx.accordion.item(
                        header=rx.hstack(
                            rx.text("Line Editor", weight="bold", size="4"),
                            rx.badge("Editor", color_scheme="purple"),
                            spacing="2",
                        ),
                        content=rx.vstack(
                            rx.text("Model: Based on preset configuration", size="2", color="gray"),
                            rx.text("Temperature: 0.7 | Max Tokens: 2000", size="2", color="gray"),
                            rx.text("Sentence-level editing and refinement", size="2", color="gray"),
                            spacing="1",
                            align_items="start",
                        ),
                        value="line_editor",
                    ),
                    rx.accordion.item(
                        header=rx.hstack(
                            rx.text("Advanced Editors", weight="bold", size="4"),
                            rx.badge("Coming Soon", color_scheme="gray"),
                            spacing="2",
                        ),
                        content=rx.text(
                            "Scene, Chapter, Book, and Series level editors coming soon",
                            size="2",
                            color="gray"
                        ),
                        value="advanced_editors",
                    ),
                    collapsible=True,
                    width="100%",
                    variant="ghost",
                ),

                spacing="3",
                align_items="start",
                width="100%",
            ),
            width="100%",
            max_width="1000px",
            margin_top="1rem",
        ),

        rx.callout(
            "Changes to agent configurations will be saved to your custom preset. Built-in presets cannot be modified.",
            icon="info",
            size="2",
            width="100%",
            max_width="1000px",
            margin_top="1rem",
        ),

        spacing="4",
        padding="2rem",
        width="100%",
        align_items="start",
    )


# Main Layout

def main_layout() -> rx.Component:
    """Main application layout with sidebar"""
    return rx.hstack(
        sidebar(),
        rx.vstack(
            navbar(),
            rx.box(
                rx.cond(
                    State.current_page == "home",
                    home_page(),
                    rx.cond(
                        State.current_page == "new_project",
                        new_project_page(),
                        rx.cond(
                            State.current_page == "load_project",
                            load_project_page(),
                            rx.cond(
                                State.current_page == "project_manager",
                                project_manager_page(),
                                rx.cond(
                                    State.current_page == "settings",
                                    settings_page(),
                                    rx.cond(
                                        State.current_page == "stage_viewer",
                                        stage_viewer_page(),
                                        rx.cond(
                                            State.current_page == "step_by_step",
                                            step_by_step_page(),
                                            rx.cond(
                                                State.current_page == "prose_reader",
                                                prose_reader_page(),
                                                rx.cond(
                                                    State.current_page == "editing_suite",
                                                    editing_suite_page(),
                                                    rx.cond(
                                                        State.current_page == "chat",
                                                        chat_page(),
                                                        rx.cond(
                                                            State.current_page == "agent_config",
                                                            agent_config_page(),
                                                            rx.cond(
                                                                State.current_page == "analytics",
                                                                analytics_page(),
                                                                rx.cond(
                                                                    State.current_page == "export",
                                                                    export_page(),
                                                                    home_page(),
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
                width="100%",
                height="100%",
                overflow_y="auto",
            ),
            width="100%",
            height="100vh",
            spacing="0",
        ),
        width="100%",
        height="100vh",
        spacing="0",
        align_items="start",
    )


# Authentication Page

def login_page() -> rx.Component:
    """Login page"""
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("Fiction Pipeline Login", size="7"),
                rx.text("Please log in to continue", size="4", color="gray"),

                rx.form(
                    rx.vstack(
                        rx.input(
                            placeholder="Username",
                            value=State.username,
                            on_change=State.set_username,
                            width="100%",
                        ),
                        rx.input(
                            type="password",
                            placeholder="Password",
                            value=State.password,
                            on_change=State.set_password,
                            width="100%",
                        ),
                        rx.button(
                            "Login",
                            on_click=State.check_authentication,
                            width="100%",
                            size="3",
                        ),
                        rx.cond(
                            State.auth_error != "",
                            rx.text(State.auth_error, color="red", size="2"),
                        ),
                        spacing="3",
                        width="100%",
                    ),
                ),

                spacing="4",
                align_items="center",
                width="100%",
            ),
            max_width="400px",
            padding="2rem",
        ),
        height="100vh",
        width="100%",
    )


# Main App

def index() -> rx.Component:
    """Main app entry point"""
    return rx.cond(
        State.is_authenticated,
        main_layout(),
        login_page(),
    )


app = rx.App()
app.add_page(index)
