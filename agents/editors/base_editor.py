#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Editor Class

Foundation for all editing agents with shared functionality
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pydantic import BaseModel


class EditSuggestion(BaseModel):
    """A single edit suggestion"""
    edit_id: str  # Unique identifier
    level: str  # "series", "book", "chapter", "scene", "line"
    severity: str  # "critical", "major", "minor", "suggestion"
    category: str  # "structure", "pacing", "dialogue", "prose", "consistency", etc.
    description: str  # What's wrong
    suggestion: str  # How to fix it
    location: Dict[str, Any]  # Where in the project (book, chapter, scene, beat, paragraph)
    original_text: Optional[str] = None  # For line-level edits
    suggested_text: Optional[str] = None  # For line-level edits
    rationale: str  # Why this change improves the work
    auto_apply: bool = False  # Can this be applied automatically?


class EditReport(BaseModel):
    """Report from an editing pass"""
    editor_name: str
    level: str  # "series", "book", "chapter", "scene", "line"
    scope: Dict[str, Any]  # What was edited (book_idx, chapter_idx, etc.)
    overall_score: float  # 0-10 quality score
    strengths: List[str]
    suggestions: List[EditSuggestion]
    summary: str
    estimated_revision_time: str  # e.g., "2-3 hours", "30 minutes"


class BaseEditor(ABC):
    """Base class for all editing agents"""

    def __init__(self, llm, editor_name: str, level: str):
        """
        Args:
            llm: Language model for analysis
            editor_name: Name of this editor (e.g., "Line Editor")
            level: Scope level (series/book/chapter/scene/line)
        """
        self.llm = llm
        self.editor_name = editor_name
        self.level = level

    @abstractmethod
    def analyze(self, project, **kwargs) -> EditReport:
        """
        Analyze the project/section and generate edit suggestions

        Args:
            project: FictionProject instance
            **kwargs: Scope parameters (book_idx, chapter_idx, etc.)

        Returns:
            EditReport with suggestions
        """
        pass

    @abstractmethod
    def apply_edit(self, project, edit_suggestion: EditSuggestion):
        """
        Apply a specific edit suggestion to the project

        Args:
            project: FictionProject instance
            edit_suggestion: The edit to apply

        Returns:
            Modified project
        """
        pass

    def auto_apply_all(self, project, edit_report: EditReport):
        """
        Automatically apply all suggestions marked as auto_apply=True

        Args:
            project: FictionProject instance
            edit_report: Report with suggestions

        Returns:
            Modified project, list of applied edits
        """
        applied_edits = []

        for suggestion in edit_report.suggestions:
            if suggestion.auto_apply:
                try:
                    project = self.apply_edit(project, suggestion)
                    applied_edits.append(suggestion)
                except Exception as e:
                    print(f"Failed to auto-apply edit {suggestion.edit_id}: {e}")

        return project, applied_edits

    def filter_suggestions(
        self,
        edit_report: EditReport,
        min_severity: Optional[str] = None,
        categories: Optional[List[str]] = None
    ) -> List[EditSuggestion]:
        """
        Filter suggestions by severity and category

        Args:
            edit_report: Report with suggestions
            min_severity: Minimum severity ("critical", "major", "minor")
            categories: List of categories to include

        Returns:
            Filtered list of suggestions
        """
        severity_rank = {"critical": 3, "major": 2, "minor": 1, "suggestion": 0}
        min_rank = severity_rank.get(min_severity, 0) if min_severity else 0

        filtered = []
        for suggestion in edit_report.suggestions:
            # Check severity
            if severity_rank.get(suggestion.severity, 0) < min_rank:
                continue

            # Check category
            if categories and suggestion.category not in categories:
                continue

            filtered.append(suggestion)

        return filtered

    def _build_context(self, project, **scope) -> str:
        """
        Build context string for the LLM based on scope

        Args:
            project: FictionProject
            **scope: book_idx, chapter_idx, scene_idx, etc.

        Returns:
            Context string
        """
        context_parts = []

        # Series context
        context_parts.append(f"=== SERIES: {project.series.title} ===")
        context_parts.append(f"Genre: {project.series.genre}")
        context_parts.append(f"Premise: {project.series.premise}")
        context_parts.append("")

        # Book context
        if 'book_idx' in scope:
            book = project.series.books[scope['book_idx']]
            context_parts.append(f"=== BOOK {book.book_number}: {book.title} ===")
            context_parts.append(f"Premise: {book.premise}")
            context_parts.append(f"Status: {book.status}")
            context_parts.append("")

        # Chapter context
        if 'chapter_idx' in scope:
            chapter = book.chapters[scope['chapter_idx']]
            context_parts.append(f"=== CHAPTER {chapter.chapter_number}: {chapter.title} ===")
            context_parts.append(f"Purpose: {chapter.purpose}")
            context_parts.append("")

        # Scene context
        if 'scene_idx' in scope:
            scene = chapter.scenes[scope['scene_idx']]
            context_parts.append(f"=== SCENE {scene.scene_number} ===")
            context_parts.append(f"Purpose: {scene.purpose}")
            context_parts.append(f"POV: {scene.pov_character}")
            context_parts.append("")

        return "\n".join(context_parts)
