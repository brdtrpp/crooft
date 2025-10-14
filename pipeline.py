"""
Fiction Pipeline Orchestrator
Manages the complete workflow from series concept to finished manuscript
"""

import os
from datetime import datetime
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from models.schema import FictionProject, Metadata, Series, Lore
from agents import (
    SeriesRefinerAgent,
    BookOutlinerAgent,
    ChapterDeveloperAgent,
    SceneDeveloperAgent,
    BeatDeveloperAgent,
    ProseGeneratorAgent,
    QAAgent,
    LoreMasterAgent
)
from utils.state_manager import StateManager
from utils.lore_store import LoreVectorStore
from utils.model_config import ModelConfig, AgentModelConfig

# Load environment variables
load_dotenv()


class FictionPipeline:
    """Main pipeline orchestrator for fiction generation"""

    def __init__(
        self,
        project_id: str,
        output_dir: str = "output",
        openrouter_api_key: str = None,
        use_lore_db: bool = True,
        model_config: dict = None,
        preset: str = None,
        requirements: dict = None
    ):
        """
        Initialize the fiction pipeline

        IMPORTANT: Quality gates (QA + Lore validation) are ALWAYS enabled and MANDATORY.
        The pipeline will HALT if content fails quality checks after max_retries.
        Bad content is NEVER skipped.

        Args:
            project_id: Unique identifier for this project
            output_dir: Directory for output files
            openrouter_api_key: OpenRouter API key (or use env var)
            use_lore_db: Enable Pinecone lore database (requires PINECONE_API_KEY)
            model_config: Custom model configurations per agent
                Example: {"prose": {"model": "anthropic/claude-3-opus", "temperature": 0.9}}
            preset: Use preset configuration ("balanced", "creative", "precise", "cost_optimized", "premium")
        """
        self.project_id = project_id
        self.output_dir = output_dir
        self.state_manager = StateManager(output_dir)
        self.requirements = requirements or {}

        # Initialize lore vector store (optional)
        self.lore_store = None
        if use_lore_db:
            # Sanitize project_id for use as namespace (lowercase alphanumeric + hyphens/underscores)
            sanitized_id = project_id.lower().replace(' ', '-')
            # Remove any invalid characters (Pinecone namespaces allow alphanumeric, hyphens, underscores)
            sanitized_id = ''.join(c for c in sanitized_id if c.isalnum() or c in '-_')
            # Use shared index with project-specific namespace
            self.lore_store = LoreVectorStore(index_name="fiction-lore", namespace=sanitized_id)

            # Verify lore store is actually enabled
            if not self.lore_store.enabled:
                print("\n⚠️  WARNING: Lore vector database is DISABLED")
                print("    Reason: Missing PINECONE_API_KEY or initialization failed")
                print("    Impact: Lore consistency checks will use in-memory data only")
                print("    To enable: Set PINECONE_API_KEY environment variable\n")
        else:
            print("\n📝 Note: Lore vector database disabled (use_lore_db=False)")
            print("   Lore will be stored in JSON checkpoints only\n")

        # Get API key
        api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OpenRouter API key required (set OPENROUTER_API_KEY env var)")

        # Load model configurations
        if preset:
            print(f"📋 Using preset: {preset}")
            preset_config = ModelConfig.get_presets().get(preset, {})
            self.model_configs = ModelConfig.create(preset_config)
        else:
            self.model_configs = ModelConfig.create(model_config)

        # Print configuration
        print(f"\n🤖 Model Configuration:")
        for agent, config in self.model_configs.items():
            print(f"  {agent:12} → {config.model:40} (temp={config.temperature})")

        # Initialize LLMs for each agent
        self.llms = {}
        for agent, config in self.model_configs.items():
            self.llms[agent] = self._init_llm(api_key, config)

        # Initialize agents with their configured LLMs and lore store
        self.agents = {
            "series": SeriesRefinerAgent(self.llms["series"], lore_store=self.lore_store, requirements=self.requirements),
            "book": BookOutlinerAgent(self.llms["book"], book_number=1, lore_store=self.lore_store, requirements=self.requirements),
            "chapter": ChapterDeveloperAgent(self.llms["chapter"], lore_store=self.lore_store),
            "scene": SceneDeveloperAgent(self.llms["scene"], lore_store=self.lore_store),
            "beat": BeatDeveloperAgent(self.llms["beat"], lore_store=self.lore_store),
            "prose": ProseGeneratorAgent(self.llms["prose"], lore_store=self.lore_store),
            "qa": QAAgent(self.llms["qa"], lore_store=self.lore_store),
            "lore": LoreMasterAgent(self.llms["lore"], lore_store=self.lore_store)
        }

    def _init_llm(self, api_key: str, config: AgentModelConfig):
        """Initialize LLM with OpenRouter and config"""
        llm_kwargs = {
            "model_name": config.model,
            "temperature": config.temperature,
            "openai_api_key": api_key,
            "openai_api_base": "https://openrouter.ai/api/v1",
            "default_headers": {
                "HTTP-Referer": "http://localhost",
                "X-Title": "Fiction Generation Pipeline"
            }
        }

        # Add optional parameters
        if config.max_tokens:
            llm_kwargs["max_tokens"] = config.max_tokens
        if config.top_p:
            llm_kwargs["model_kwargs"] = llm_kwargs.get("model_kwargs", {})
            llm_kwargs["model_kwargs"]["top_p"] = config.top_p
        if config.frequency_penalty:
            llm_kwargs["model_kwargs"] = llm_kwargs.get("model_kwargs", {})
            llm_kwargs["model_kwargs"]["frequency_penalty"] = config.frequency_penalty
        if config.presence_penalty:
            llm_kwargs["model_kwargs"] = llm_kwargs.get("model_kwargs", {})
            llm_kwargs["model_kwargs"]["presence_penalty"] = config.presence_penalty

        return ChatOpenAI(**llm_kwargs)

    def _auto_add_lore(self, project: FictionProject, new_lore_items: list) -> int:
        """
        Automatically add detected lore to the project

        Args:
            project: Current project
            new_lore_items: List of new lore items from Lore Master

        Returns:
            Number of items added
        """
        from models.schema import Character, Location, WorldElement

        added = 0
        for item in new_lore_items:
            if not item.get('should_add', False):
                continue

            lore_type = item.get('type', '').lower()
            name = item.get('name', '')
            description = item.get('description', '')

            try:
                if lore_type == 'character':
                    # Check if already exists
                    if not any(c.name.lower() == name.lower() for c in project.series.lore.characters):
                        new_char = Character(
                            name=name,
                            role=item.get('role', 'supporting'),
                            description=description,
                            traits=item.get('traits', []),
                            relationships=[]
                        )
                        project.series.lore.characters.append(new_char)
                        added += 1
                        print(f"      ✓ Added character: {name}")

                elif lore_type == 'location':
                    # Check if already exists
                    if not any(l.name.lower() == name.lower() for l in project.series.lore.locations):
                        new_loc = Location(
                            name=name,
                            description=description,
                            significance=item.get('significance', 'Mentioned in story')
                        )
                        project.series.lore.locations.append(new_loc)
                        added += 1
                        print(f"      ✓ Added location: {name}")

                elif lore_type in ['world_element', 'technology', 'magic', 'species', 'faction', 'organization']:
                    # Check if already exists
                    if not any(e.name.lower() == name.lower() for e in project.series.lore.world_elements):
                        new_elem = WorldElement(
                            name=name,
                            type=lore_type if lore_type != 'world_element' else item.get('subtype', 'other'),
                            description=description,
                            rules=item.get('rules', [])
                        )
                        project.series.lore.world_elements.append(new_elem)
                        added += 1
                        print(f"      ✓ Added world element: {name}")

            except Exception as e:
                print(f"      ⚠️  Failed to add {lore_type} '{name}': {e}")

        return added

    def quality_gate(self, project: FictionProject, stage_name: str, max_retries: int = 3) -> FictionProject:
        """
        Run QA + Lore validation with retry logic

        Args:
            project: Current project state
            stage_name: Name of stage for logging
            max_retries: Maximum retry attempts

        Returns:
            Validated project
        """
        for attempt in range(max_retries):
            print(f"  [Quality Gate] QA Review (attempt {attempt + 1}/{max_retries})...")

            # QA Review
            project, qa_report = self.agents["qa"].process(project)

            print(f"    QA Score: {qa_report.scores.get('overall', 0)}/10")
            print(f"    Approval: {qa_report.approval}")

            # Display detailed QA feedback
            if qa_report.major_issues:
                print(f"    Major Issues ({len(qa_report.major_issues)}):")
                for issue in qa_report.major_issues[:3]:  # Show first 3
                    print(f"      • {issue}")
            if qa_report.strengths:
                print(f"    Strengths ({len(qa_report.strengths)}):")
                for strength in qa_report.strengths[:2]:  # Show first 2
                    print(f"      • {strength}")

            if qa_report.approval == "approved":
                print(f"    ✓ QA Passed")

                # Lore Master Review
                print(f"  [Quality Gate] Lore Validation...")
                project, lore_result = self.agents["lore"].process(project)

                print(f"    Lore Score: {lore_result['score']}/10")
                print(f"    Approval: {lore_result['approval']}")

                # Display lore violations if any
                if lore_result.get('violations'):
                    print(f"    Violations ({len(lore_result['violations'])}):")
                    for violation in lore_result['violations'][:3]:  # Show first 3
                        print(f"      • [{violation.get('severity', 'unknown').upper()}] {violation.get('violation', 'N/A')}")

                # Display new lore detected
                if lore_result.get('new_lore'):
                    print(f"    New Lore Detected ({len(lore_result['new_lore'])}):")
                    for new_item in lore_result['new_lore'][:3]:  # Show first 3
                        print(f"      • [{new_item.get('type', 'unknown')}] {new_item.get('name', 'N/A')}")

                if lore_result['approval'] == "approved":
                    print(f"    ✓ Lore Passed")

                    # Auto-add new lore if detected and should_add is true
                    if lore_result.get('new_lore') and self.lore_store and self.lore_store.enabled:
                        added_count = self._auto_add_lore(project, lore_result['new_lore'])
                        if added_count > 0:
                            print(f"    → Auto-added {added_count} new lore entries to database")
                            # Re-store lore with new additions
                            self.lore_store.store_all_lore(project)

                    print(f"  [Quality Gate] ✓ APPROVED")
                    return project
                else:
                    print(f"    ✗ Lore Failed: {lore_result['notes']}")
                    if attempt < max_retries - 1:
                        print(f"    → Retrying with lore feedback...")
            else:
                print(f"    ✗ QA Failed")
                if qa_report.revision_tasks:
                    print(f"    Revision Tasks ({len(qa_report.revision_tasks)}):")
                    for task in qa_report.revision_tasks[:3]:  # Show first 3
                        print(f"      • [{task.priority.upper()}] {task.description}")
                if attempt < max_retries - 1:
                    print(f"    → Retrying (attempt {attempt + 2}/{max_retries})...")

        # Max retries exceeded - HALT, do not proceed with bad content
        print(f"\n{'=' * 60}")
        print(f"❌ QUALITY GATE FAILED - PIPELINE HALTED")
        print(f"{'=' * 60}")
        print(f"Stage: {stage_name}")
        print(f"Attempts: {max_retries}")
        print(f"\nLast QA Report:")
        print(f"  Overall Score: {qa_report.scores.get('overall', 0)}/10")
        print(f"  Major Issues: {len(qa_report.major_issues)}")
        for issue in qa_report.major_issues:
            print(f"    • {issue}")
        print(f"\n  Revision Tasks: {len(qa_report.revision_tasks)}")
        for task in qa_report.revision_tasks:
            print(f"    • [{task.priority.upper()}] {task.description}")
        print(f"\n  Reviewer Notes: {qa_report.reviewer_notes}")
        print(f"\n{'=' * 60}")
        print(f"OPTIONS:")
        print(f"1. Review output/{self.project_id}/state.json")
        print(f"2. Check QA reports in the JSON file")
        print(f"3. Increase max_retries or improve prompts")
        print(f"4. Manual editing required")
        print(f"{'=' * 60}\n")

        # HALT - raise error to prevent proceeding
        raise RuntimeError(
            f"Quality gate failed after {max_retries} attempts. "
            f"Content does not meet quality standards. Manual intervention required. "
            f"See above for details."
        )

    def run(self, initial_project: FictionProject) -> FictionProject:
        """
        Run the complete pipeline

        Args:
            initial_project: Initial project with series concept

        Returns:
            Completed FictionProject
        """
        project = initial_project

        print("\n" + "=" * 60)
        print("FICTION GENERATION PIPELINE")
        print("=" * 60)

        # Stage 1: Series Refiner
        print("\n[1/6] Running Series Refiner...")
        project = self.agents["series"].process(project)
        self.state_manager.save_state(project, "1_series_refined")

        # Store lore in vector database
        if self.lore_store and self.lore_store.enabled:
            print("  [Lore] Storing lore in vector database...")
            self.lore_store.store_all_lore(project)

        project = self.quality_gate(project, "series")

        # Stage 2: Book Outliner (for each book)
        print("\n[2/6] Running Book Outliner...")
        for book_idx, book in enumerate(project.series.books):
            print(f"  Processing Book {book.book_number}: {book.title}...")
            self.agents["book"].book_number = book.book_number
            project = self.agents["book"].process(project)
            self.state_manager.save_state(project, f"2_book_{book.book_number}_outlined")
            project = self.quality_gate(project, f"book_{book.book_number}")

        # Stage 3: Chapter Developer (for each chapter in each book)
        print("\n[3/6] Running Chapter Developer...")
        for book in project.series.books:
            for chapter_idx in range(len(book.chapters)):
                chapter = book.chapters[chapter_idx]
                print(f"  Processing Chapter {chapter.chapter_number} of Book {book.book_number}...")
                project = self.agents["chapter"].process_chapter(project, book.book_number - 1, chapter_idx)
                self.state_manager.save_state(project, f"3_book{book.book_number}_ch{chapter.chapter_number}")

        # Stage 4: Scene Developer (for each scene in each chapter)
        print("\n[4/6] Running Scene Developer...")
        for book_idx, book in enumerate(project.series.books):
            for chapter_idx, chapter in enumerate(book.chapters):
                for scene_idx in range(len(chapter.scenes)):
                    scene = chapter.scenes[scene_idx]
                    print(f"  Processing Scene {scene.scene_number} (Ch{chapter.chapter_number}, Book{book.book_number})...")
                    project = self.agents["scene"].process_scene(project, book_idx, chapter_idx, scene_idx)
                    self.state_manager.save_state(
                        project,
                        f"4_b{book.book_number}_ch{chapter.chapter_number}_sc{scene.scene_number}"
                    )

        # Stage 5: Beat Developer (for each beat in each scene)
        print("\n[5/6] Running Beat Developer...")
        for book_idx, book in enumerate(project.series.books):
            for chapter_idx, chapter in enumerate(book.chapters):
                for scene_idx, scene in enumerate(chapter.scenes):
                    print(f"  Processing Beats for Scene {scene.scene_number}...")
                    project = self.agents["beat"].process_scene_beats(project, book_idx, chapter_idx, scene_idx)
                    self.state_manager.save_state(
                        project,
                        f"5_b{book.book_number}_ch{chapter.chapter_number}_sc{scene.scene_number}_beats"
                    )

        # Stage 6: Prose Generator (for each beat)
        print("\n[6/6] Running Prose Generator...")
        for book_idx, book in enumerate(project.series.books):
            for chapter_idx, chapter in enumerate(book.chapters):
                for scene_idx, scene in enumerate(chapter.scenes):
                    for beat_idx in range(len(scene.beats)):
                        beat = scene.beats[beat_idx]
                        print(f"  Generating prose for Beat {beat.beat_number}...")
                        project = self.agents["prose"].process_beat(
                            project, book_idx, chapter_idx, scene_idx, beat_idx
                        )
                    # Save after each scene's prose is complete
                    self.state_manager.save_state(
                        project,
                        f"6_b{book.book_number}_ch{chapter.chapter_number}_sc{scene.scene_number}_prose"
                    )

        # Final Quality Gate
        print("\n[Final] Running Final Quality Review...")
        project = self.quality_gate(project, "final")
        self.state_manager.save_state(project, "final")

        print("\n" + "=" * 60)
        print("✓ PIPELINE COMPLETE!")
        print(f"✓ Project ID: {project.metadata.project_id}")
        print(f"✓ Total Books: {len(project.series.books)}")
        if project.series.books:
            total_chapters = sum(len(book.chapters) for book in project.series.books)
            total_scenes = sum(
                len(chapter.scenes)
                for book in project.series.books
                for chapter in book.chapters
            )
            print(f"✓ Total Chapters: {total_chapters}")
            print(f"✓ Total Scenes: {total_scenes}")
        print(f"✓ Final state saved to: {self.output_dir}/{project.metadata.project_id}_state.json")
        print("=" * 60)

        return project

    def export_manuscript(self, project: FictionProject, output_dir: str = "manuscripts"):
        """
        Export final manuscript as markdown

        Args:
            project: Completed FictionProject
            output_dir: Directory for manuscript files
        """
        os.makedirs(output_dir, exist_ok=True)

        # Build manuscript
        lines = []
        lines.append(f"# {project.series.title}\n")
        lines.append(f"*{project.series.premise}*\n\n")
        lines.append("---\n\n")

        for book in project.series.books:
            lines.append(f"\n# {book.title}\n\n")

            for chapter in book.chapters:
                lines.append(f"\n## Chapter {chapter.chapter_number}: {chapter.title}\n\n")

                for scene in chapter.scenes:
                    # Collect prose from all beats in scene
                    for beat in scene.beats:
                        if beat.prose and beat.prose.paragraphs:
                            # Use structured paragraph data if available
                            for paragraph in beat.prose.paragraphs:
                                lines.append(paragraph.content)
                                lines.append("\n\n")
                        elif beat.prose and beat.prose.content:
                            # Fallback to full content if paragraphs not structured
                            lines.append(beat.prose.content)
                            lines.append("\n\n")

                    lines.append("\n")  # Scene break

        # Write manuscript
        manuscript_path = os.path.join(output_dir, f"{project.metadata.project_id}_manuscript.md")
        with open(manuscript_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✓ Manuscript exported to: {manuscript_path}")

        # Also save final JSON
        final_json_path = os.path.join(output_dir, f"{project.metadata.project_id}_final.json")
        self.state_manager.save_state(project, "final")
        print(f"✓ Final JSON saved to: {final_json_path}")


def create_project_from_concept(concept: str, project_id: str) -> FictionProject:
    """
    Helper function to create initial FictionProject from a concept string

    Args:
        concept: Series concept (format: "Title\\nPremise\\nGenre")
        project_id: Project identifier

    Returns:
        Initial FictionProject
    """
    lines = concept.strip().split('\n')
    title = lines[0] if len(lines) > 0 else "Untitled Series"
    premise = lines[1] if len(lines) > 1 else "A story to be told."
    genre = lines[2] if len(lines) > 2 else "fiction"

    return FictionProject(
        metadata=Metadata(
            last_updated=datetime.now(),
            last_updated_by="Initializer",
            processing_stage="series",
            status="draft",
            project_id=project_id,
            iteration=1
        ),
        series=Series(
            title=title,
            premise=premise,
            genre=genre,
            target_audience="adult",
            themes=[],
            persistent_threads=[],
            lore=Lore(),
            books=[],
            raw_text=concept
        )
    )
