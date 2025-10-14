#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Book Editor

Book-level developmental editing
Focus: structure, pacing, character arcs within book
"""

import json
from typing import List, Dict, Any
from langchain.schema import HumanMessage, SystemMessage

from .base_editor import BaseEditor, EditReport, EditSuggestion
from models.schema import FictionProject


class BookEditor(BaseEditor):
    """
    Book-level editor focusing on:
    - 3-act structure integrity
    - Book pacing and rhythm
    - Character arc completion within book
    - Plot coherence
    - Chapter balance
    - Climax effectiveness
    """

    def __init__(self, llm):
        super().__init__(llm, "Book Editor", "book")

    def analyze(self, project: FictionProject, book_idx: int, **kwargs) -> EditReport:
        """
        Analyze individual book for structural issues

        Args:
            project: FictionProject instance
            book_idx: Index of book to analyze

        Returns:
            EditReport with book-level suggestions
        """
        book = project.series.books[book_idx]

        # Build book context
        context_parts = []

        context_parts.append(f"=== SERIES CONTEXT ===")
        context_parts.append(f"Series: {project.series.title}")
        context_parts.append(f"Total Books: {len(project.series.books)}")
        context_parts.append(f"Book Position: {book.book_number} of {len(project.series.books)}")
        context_parts.append("")

        context_parts.append(f"=== BOOK {book.book_number}: {book.title} ===")
        context_parts.append(f"Status: {book.status}")
        context_parts.append(f"Premise: {book.premise}")
        context_parts.append(f"Target Word Count: {book.target_word_count:,}")
        context_parts.append(f"Current Word Count: {book.current_word_count:,}")
        context_parts.append(f"Chapters: {len(book.chapters)}")
        context_parts.append("")

        # Structure analysis
        if book.three_act_structure:
            context_parts.append("=== THREE-ACT STRUCTURE ===")
            context_parts.append(f"Act 1: Chapters {book.three_act_structure.get('act1_chapters', 'N/A')}")
            context_parts.append(f"  Setup: {book.three_act_structure.get('act1_description', 'N/A')}")
            context_parts.append(f"Act 2: Chapters {book.three_act_structure.get('act2_chapters', 'N/A')}")
            context_parts.append(f"  Conflict: {book.three_act_structure.get('act2_description', 'N/A')}")
            context_parts.append(f"Act 3: Chapters {book.three_act_structure.get('act3_chapters', 'N/A')}")
            context_parts.append(f"  Resolution: {book.three_act_structure.get('act3_description', 'N/A')}")
            context_parts.append("")

        # Character arcs
        if book.character_arcs:
            context_parts.append("=== CHARACTER ARCS ===")
            for arc in book.character_arcs:
                context_parts.append(f"{arc.character_name}:")
                context_parts.append(f"  Type: {arc.arc_type}")
                context_parts.append(f"  Start: {arc.starting_state}")
                context_parts.append(f"  End: {arc.ending_state}")
                context_parts.append(f"  Transformation: {arc.transformation}")
            context_parts.append("")

        # Plot threads
        if book.plot_threads:
            context_parts.append("=== PLOT THREADS ===")
            for thread in book.plot_threads:
                status = "✓ Resolved" if thread.get('resolved', False) else "○ Ongoing"
                context_parts.append(f"{status}: {thread.get('description', 'N/A')}")
            context_parts.append("")

        # Chapter breakdown
        context_parts.append("=== CHAPTERS ===")
        for chapter in book.chapters[:20]:  # First 20 chapters
            word_estimate = sum(
                len(beat.prose.content.split()) if beat.prose and beat.prose.content else 0
                for scene in chapter.scenes
                for beat in scene.beats
            )
            context_parts.append(f"Ch {chapter.chapter_number}: {chapter.title}")
            context_parts.append(f"  Purpose: {chapter.purpose}")
            context_parts.append(f"  Scenes: {len(chapter.scenes)}, ~{word_estimate:,} words")

        if len(book.chapters) > 20:
            context_parts.append(f"... and {len(book.chapters) - 20} more chapters")

        context = "\n".join(context_parts)

        # Build prompt
        prompt_parts = []
        prompt_parts.append("You are an expert developmental editor specializing in book-level analysis.")
        prompt_parts.append("Your task is to analyze this book for structural and developmental issues.")
        prompt_parts.append("")
        prompt_parts.append(context)
        prompt_parts.append("")
        prompt_parts.append("=== ANALYSIS FRAMEWORK ===")
        prompt_parts.append("Analyze the following aspects:")
        prompt_parts.append("")
        prompt_parts.append("1. THREE-ACT STRUCTURE:")
        prompt_parts.append("   - Is there a clear setup, confrontation, and resolution?")
        prompt_parts.append("   - Are the act breaks properly placed?")
        prompt_parts.append("   - Is the inciting incident strong enough?")
        prompt_parts.append("   - Does the midpoint provide a proper pivot?")
        prompt_parts.append("   - Is the climax satisfying?")
        prompt_parts.append("")
        prompt_parts.append("2. PACING:")
        prompt_parts.append("   - Is the pacing appropriate for the genre?")
        prompt_parts.append("   - Are there slow sections that need tightening?")
        prompt_parts.append("   - Are there rushed sections that need expansion?")
        prompt_parts.append("   - Is there proper balance of action/reflection?")
        prompt_parts.append("   - Do chapters end with appropriate hooks?")
        prompt_parts.append("")
        prompt_parts.append("3. CHARACTER ARCS:")
        prompt_parts.append("   - Does each major character have a complete arc?")
        prompt_parts.append("   - Are transformations believable and earned?")
        prompt_parts.append("   - Is there proper character development throughout?")
        prompt_parts.append("   - Are motivations clear and consistent?")
        prompt_parts.append("")
        prompt_parts.append("4. PLOT COHERENCE:")
        prompt_parts.append("   - Does the plot flow logically?")
        prompt_parts.append("   - Are plot threads properly woven together?")
        prompt_parts.append("   - Are there plot holes or inconsistencies?")
        prompt_parts.append("   - Is cause-and-effect clear?")
        prompt_parts.append("")
        prompt_parts.append("5. CHAPTER BALANCE:")
        prompt_parts.append("   - Are chapters relatively balanced in length?")
        prompt_parts.append("   - Does each chapter advance the story?")
        prompt_parts.append("   - Are there unnecessary chapters?")
        prompt_parts.append("   - Are there missing chapters/gaps?")
        prompt_parts.append("")
        prompt_parts.append("6. CLIMAX & RESOLUTION:")
        prompt_parts.append("   - Is the climax properly built up?")
        prompt_parts.append("   - Does the climax deliver on promises made?")
        prompt_parts.append("   - Is the resolution satisfying?")
        prompt_parts.append("   - Are loose ends properly tied up?")
        prompt_parts.append("")
        prompt_parts.append("For each issue, provide:")
        prompt_parts.append("- Severity (critical/major/minor/suggestion)")
        prompt_parts.append("- Category (structure/pacing/character_arc/plot/chapter_balance/climax)")
        prompt_parts.append("- Specific description")
        prompt_parts.append("- Location (which chapters)")
        prompt_parts.append("- Actionable suggestion")
        prompt_parts.append("- Rationale")
        prompt_parts.append("")
        prompt_parts.append("Also identify 3-5 STRENGTHS.")
        prompt_parts.append("")
        prompt_parts.append("Output as JSON:")
        prompt_parts.append('''{
  "overall_score": 7.5,
  "strengths": [
    "Strong three-act structure",
    "Well-paced action sequences"
  ],
  "suggestions": [
    {
      "severity": "major",
      "category": "pacing",
      "description": "Act 2 sags in the middle",
      "location": "Chapters 8-12",
      "suggestion": "Tighten chapters 8-12, cut or combine weaker scenes, add midpoint twist earlier",
      "rationale": "Middle sections need momentum to maintain reader engagement"
    }
  ],
  "summary": "Solid structure with good character arcs. Main issue is pacing..."
}''')

        prompt = "\n".join(prompt_parts)

        # Call LLM
        messages = [
            SystemMessage(content="You are an expert book editor. Return ONLY valid JSON."),
            HumanMessage(content=prompt)
        ]

        response = self.llm.invoke(messages).content

        # Parse response
        response_text = response.strip()
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
        else:
            result = json.loads(response_text)

        # Convert to EditReport
        edit_suggestions = []
        for idx, sug in enumerate(result.get('suggestions', [])):
            edit_suggestions.append(EditSuggestion(
                edit_id=f"book_{book_idx}_{idx}",
                level="book",
                severity=sug.get('severity', 'suggestion'),
                category=sug.get('category', 'structure'),
                description=sug.get('description', ''),
                suggestion=sug.get('suggestion', ''),
                location={
                    'book_idx': book_idx,
                    'affected_chapters': sug.get('location', 'Book-wide')
                },
                original_text=None,
                suggested_text=None,
                rationale=sug.get('rationale', ''),
                auto_apply=False
            ))

        edit_report = EditReport(
            editor_name="Book Editor",
            level="book",
            scope={
                'book_idx': book_idx,
                'book_title': book.title,
                'chapter_count': len(book.chapters)
            },
            overall_score=result.get('overall_score', 7.0),
            strengths=result.get('strengths', []),
            suggestions=edit_suggestions,
            summary=result.get('summary', 'Book analysis complete.'),
            estimated_revision_time=self._estimate_revision_time(len(edit_suggestions))
        )

        return edit_report

    def apply_edit(self, project: FictionProject, edit_suggestion: EditSuggestion) -> FictionProject:
        """
        Apply book-level edit

        Note: Book-level edits are typically structural guidance.
        """
        print(f"Book Editor suggestion: {edit_suggestion.description}")
        print(f"Manual action required: {edit_suggestion.suggestion}")

        # Log to metadata
        try:
            if hasattr(project.metadata, 'editorial_notes'):
                project.metadata.editorial_notes.append({
                    'editor': 'Book Editor',
                    'category': edit_suggestion.category,
                    'suggestion': edit_suggestion.suggestion,
                    'severity': edit_suggestion.severity,
                    'location': edit_suggestion.location
                })
        except:
            pass

        return project

    def _estimate_revision_time(self, num_suggestions: int) -> str:
        """Estimate time for book-level revisions"""
        if num_suggestions == 0:
            return "No revisions needed"
        elif num_suggestions <= 3:
            return "4-8 hours"
        elif num_suggestions <= 7:
            return "1-3 days"
        else:
            return "3-7 days"
