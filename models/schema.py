"""
Pydantic models for fiction generation pipeline.
Defines the complete data structure for series, books, chapters, scenes, beats, and prose.
"""

from pydantic import BaseModel, Field, model_serializer, field_validator
from typing import List, Optional, Literal, Dict, Any, Union
from datetime import datetime


class Metadata(BaseModel):
    """Project metadata for tracking and versioning"""
    schema_version: str = "1.0"
    last_updated: datetime
    last_updated_by: str
    processing_stage: Literal["series", "book", "chapter", "scene", "beat", "prose", "qa", "editorial"]
    status: Literal["draft", "in_review", "approved", "needs_revision", "dev_revised", "line_edited"]
    project_id: str
    iteration: int = 1


# Legacy class kept for backward compatibility but NOT used in Character.relationships
# Character.relationships uses List[Union[str, Dict[str, Any]]] instead
class Relationship(BaseModel):
    """DEPRECATED: Character relationship - use dict instead

    This class is kept for backward compatibility with old JSON files only.
    New code should use plain dicts: {"name": "...", "type": "..."}
    """
    name: str
    type: str

    @model_serializer
    def ser_model(self) -> Dict[str, Any]:
        """Custom serializer that always returns a simple dict"""
        return {"name": self.name, "type": self.type}

class Character(BaseModel):
    """Character lore entry"""
    name: str
    role: str
    description: str
    traits: List[str] = []
    relationships: List[Union[str, Dict[str, Any]]] = []  # Accepts str or dict

    @field_validator('relationships', mode='before')
    @classmethod
    def convert_relationships(cls, v):
        """Convert any Relationship objects to dicts"""
        if not isinstance(v, list):
            return v

        result = []
        for item in v:
            if isinstance(item, (str, dict)):
                result.append(item)
            elif hasattr(item, 'name') and hasattr(item, 'type'):
                # Relationship object or similar
                result.append({"name": item.name, "type": item.type})
            elif hasattr(item, 'model_dump'):
                # Pydantic v2 object
                result.append(item.model_dump())
            elif hasattr(item, 'dict'):
                # Pydantic v1 object
                result.append(item.dict())
            else:
                result.append(str(item))
        return result


class Location(BaseModel):
    """Location lore entry"""
    name: str
    description: str
    significance: str


class WorldElement(BaseModel):
    """World-building element (technology, magic, species, faction, etc.)"""
    name: str
    type: str  # Common types: technology, magic, species, faction, law, organization, phenomenon, principle, etc.
    description: str
    rules: List[str] = []


class Lore(BaseModel):
    """Complete lore database for the series"""
    characters: List[Character] = []
    locations: List[Location] = []
    world_elements: List[WorldElement] = []


class ActStructure(BaseModel):
    """Three-act structure breakdown for a book"""
    percentage: int
    word_target: int
    summary: str
    key_events: List[str] = []
    ending_hook: str
    midpoint: Optional[str] = None  # Act 2 only
    climax: Optional[str] = None     # Act 3 only
    resolution: Optional[str] = None # Act 3 only


class CharacterArc(BaseModel):
    """Character transformation arc across a book"""
    character_name: str
    starting_state: str
    ending_state: str
    transformation: str
    key_moments: List[str] = []


class Conflict(BaseModel):
    """Conflict within a scene"""
    type: str  # Type of conflict (internal, external, interpersonal, etc.)
    description: str


class Setting(BaseModel):
    """Setting information for chapter/scene"""
    location: str = ""
    time: str = ""
    atmosphere: str = ""
    primary_location: Optional[str] = None
    time_period: Optional[str] = None


class DialogueLine(BaseModel):
    """A single line of dialogue with speaker attribution"""
    speaker: str  # Character name
    dialogue: str  # What they say
    action: Optional[str] = None  # Dialogue tag or action beat ("she whispered", "he slammed the door")
    internal_thought: Optional[str] = None  # If POV character, their thoughts


class Paragraph(BaseModel):
    """A single paragraph with content type tracking"""
    paragraph_number: int
    paragraph_type: Literal["narrative", "dialogue", "mixed", "description", "action", "internal_monologue"]
    content: str  # Full paragraph text
    dialogue_lines: List[DialogueLine] = []  # Populated if paragraph_type is "dialogue" or "mixed"
    pov_character: Optional[str] = None  # If internal_monologue or POV-specific content
    word_count: int = 0


class Prose(BaseModel):
    """Generated prose content for a beat"""
    draft_version: int = 1
    content: str = ""  # Full prose text (kept for backward compatibility)
    paragraphs: List[Paragraph] = []  # Structured paragraph breakdown
    word_count: int = 0
    generated_timestamp: str = ""
    status: Literal["draft", "revised", "final"] = "draft"


class Beat(BaseModel):
    """Story beat - smallest unit of narrative"""
    beat_number: int
    description: str
    emotional_tone: str
    character_actions: List[str] = []
    dialogue_summary: str = ""
    prose: Optional[Prose] = None


class Scene(BaseModel):
    """Scene within a chapter"""
    scene_id: str
    scene_number: int
    title: str = ""
    purpose: str
    scene_type: str  # Type of scene (action, dialogue, exposition, etc.)
    pov: str
    setting: Setting
    characters_present: List[str] = []
    conflicts: List[Conflict] = []
    turning_points: List[str] = []
    subplot_advancement: List[str] = []
    theme_expression: List[str] = []
    planned_word_count: int = 0
    actual_word_count: int = 0
    beats: List[Beat] = []


class CharacterFocus(BaseModel):
    """Character focus for a chapter"""
    pov: str
    present: List[str] = []
    arc_moments: List[str] = []


class Chapter(BaseModel):
    """Chapter within a book"""
    chapter_number: int
    title: str = ""
    act: int
    purpose: str
    plot_points: List[str] = []
    character_focus: CharacterFocus
    setting: Setting
    subplot_threads: List[str] = []
    themes: List[str] = []
    planned_word_count: int = 0
    actual_word_count: int = 0
    status: Literal["planned", "drafted", "revised", "final"] = "planned"
    scenes: List[Scene] = []


class Book(BaseModel):
    """Individual book in the series"""
    book_number: int
    id: Optional[str] = None
    title: str = ""
    premise: str
    protagonist_goal: Optional[str] = None
    antagonistic_force: Optional[str] = None
    unique_hook: Optional[str] = None
    major_turns: Dict[str, str] = {}
    themes: List[str] = []
    continuity_tags: Dict[str, List[str]] = {}
    target_word_count: int = 100000
    status: Literal["planned", "outlined", "drafted", "complete"] = "planned"
    risks: List[str] = []
    open_questions: List[str] = []
    current_word_count: int = 0
    act_structure: Dict[str, ActStructure] = {}
    character_arcs: List[CharacterArc] = []
    chapters: List[Chapter] = []


class Series(BaseModel):
    """Complete series structure"""
    id: Optional[str] = None
    title: str
    logline: Optional[str] = None
    premise: str
    genre: str
    subgenres: List[str] = []
    target_audience: str
    themes: List[str] = []
    universe_principles: List[Dict[str, Any]] = []
    assumptions: List[str] = []
    risks: List[str] = []
    open_questions: List[str] = []
    persistent_threads: List[Dict[str, Any]] = []
    lore: Lore
    escalation_model: Dict[str, Any] = {}
    books: List[Book] = []
    raw_text: Optional[str] = None
    feedback: Optional[List[Dict[str, Any]]] = None
    style_guide: Optional[str] = None  # Prose style guide for the series


class RevisionTask(BaseModel):
    """Revision task from QA or editorial review"""
    priority: Literal["critical", "high", "medium", "low"]
    description: str
    status: Literal["pending", "completed"] = "pending"


class QAReport(BaseModel):
    """Quality assurance report"""
    qa_id: str
    timestamp: str
    scope: Literal["series", "book", "chapter", "scene", "beat"]
    target_id: str
    scores: Dict[str, int]  # structure, pacing, character_arcs, theme_integration, consistency, overall
    major_issues: List[str] = []
    strengths: List[str] = []
    required_rewrites: List[str] = []
    revision_tasks: List[RevisionTask] = []
    approval: Literal["approved", "needs_revision", "blocked"]
    reviewer_notes: str = ""


class RevisionHistory(BaseModel):
    """Revision history entry"""
    timestamp: str
    agent: str
    scope: str
    changes_summary: str
    reason: str


class DevelopmentalIssue(BaseModel):
    """Developmental editing issue"""
    issue_type: Literal["plot_hole", "character_break", "lore_conflict",
                        "pacing", "theme_drift", "structure"]
    severity: Literal["critical", "major", "minor"]
    location: str  # book.chapter.scene.beat
    description: str
    suggested_fix: str
    status: Literal["open", "fixed", "deferred"] = "open"


class ConsistencyIssue(BaseModel):
    """Consistency/continuity issue"""
    issue_type: Literal["lore_violation", "timeline_conflict",
                        "character_inconsistency", "setting_error", "logic_gap"]
    severity: Literal["critical", "major", "minor"]
    location: str
    description: str
    conflicting_references: List[str] = []
    resolution: str = ""
    status: Literal["open", "fixed", "deferred"] = "open"


class EditorialReport(BaseModel):
    """Editorial review report"""
    report_id: str
    timestamp: str
    phase: Literal["developmental", "consistency", "line_editing", "final_qa"]
    reviewer_agent: str
    scope: str

    # Developmental
    developmental_issues: List[DevelopmentalIssue] = []

    # Consistency
    consistency_issues: List[ConsistencyIssue] = []

    # Line editing
    line_edit_changes: int = 0
    line_edit_summary: str = ""

    # Overall
    overall_score: int  # 1-10
    approval: Literal["approved", "needs_revision", "needs_rewrite"]
    reviewer_notes: str = ""
    next_steps: List[str] = []


class FictionProject(BaseModel):
    """Root schema for the entire project"""
    metadata: Metadata
    series: Series
    qa_reports: List[QAReport] = []
    revision_history: List[RevisionHistory] = []
    editorial_reports: List[EditorialReport] = []
    editorial_status: Literal["draft", "dev_editing", "line_editing",
                              "final_qa", "approved"] = "draft"
