#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Series Editor

Macro-level editing across the entire series
Focus: consistency, theme development, arc payoffs
"""

import json
from typing import List, Dict, Any
from langchain.schema import HumanMessage, SystemMessage

from .base_editor import BaseEditor, EditReport, EditSuggestion
from models.schema import FictionProject


class SeriesEditor(BaseEditor):
    """
    Series-level editor focusing on:
    - Series-wide character arc consistency
    - Theme development and payoff
    - Plot thread continuity
    - World-building consistency
    - Foreshadowing setup/payoff
    - Series pacing and escalation
    """

    def __init__(self, llm):
        super().__init__(llm, "Series Editor", "series")

    def analyze(self, project: FictionProject, **kwargs) -> EditReport:
        """
        Analyze entire series for macro-level issues

        Args:
            project: FictionProject instance

        Returns:
            EditReport with series-level suggestions
        """
        # Build comprehensive series context
        context_parts = []

        context_parts.append(f"=== SERIES: {project.series.title} ===")
        context_parts.append(f"Genre: {project.series.genre}")
        context_parts.append(f"Target Audience: {project.series.target_audience}")
        context_parts.append(f"Premise: {project.series.premise}")
        context_parts.append("")

        # Themes
        if project.series.themes:
            context_parts.append("Themes:")
            for theme in project.series.themes:
                context_parts.append(f"  - {theme}")
            context_parts.append("")

        # Persistent threads
        if project.series.persistent_threads:
            context_parts.append("Persistent Plot Threads:")
            for thread in project.series.persistent_threads:
                context_parts.append(f"  - {thread}")
            context_parts.append("")

        # Books overview
        context_parts.append(f"=== BOOKS ({len(project.series.books)}) ===")
        for book in project.series.books:
            context_parts.append(f"\nBook {book.book_number}: {book.title}")
            context_parts.append(f"  Status: {book.status}")
            context_parts.append(f"  Premise: {book.premise}")
            context_parts.append(f"  Chapters: {len(book.chapters)}")
            context_parts.append(f"  Word Count: {book.current_word_count:,}")

            if book.character_arcs:
                context_parts.append("  Character Arcs:")
                for arc in book.character_arcs[:5]:  # First 5
                    context_parts.append(f"    - {arc.character_name}: {arc.arc_type}")

            if book.plot_threads:
                context_parts.append("  Plot Threads:")
                for thread in book.plot_threads[:5]:  # First 5
                    status = "✓" if thread.get('resolved', False) else "○"
                    context_parts.append(f"    {status} {thread.get('description', 'N/A')}")

        context_parts.append("")

        # Lore summary
        context_parts.append("=== LORE ===")
        context_parts.append(f"Characters: {len(project.series.lore.characters)}")
        if project.series.lore.characters:
            context_parts.append("  Key Characters:")
            for char in project.series.lore.characters[:10]:
                context_parts.append(f"    - {char.name} ({char.role}): {char.description[:100]}")

        context_parts.append(f"\nLocations: {len(project.series.lore.locations)}")
        if project.series.lore.locations:
            context_parts.append("  Key Locations:")
            for loc in project.series.lore.locations[:10]:
                context_parts.append(f"    - {loc.name}: {loc.description[:100]}")

        context_parts.append(f"\nWorld Elements: {len(project.series.lore.world_elements)}")
        if project.series.lore.world_elements:
            context_parts.append("  Key Elements:")
            for elem in project.series.lore.world_elements[:10]:
                context_parts.append(f"    - {elem.name} ({elem.type}): {elem.description[:100]}")

        context = "\n".join(context_parts)

        # Build prompt
        prompt_parts = []
        prompt_parts.append("You are an expert developmental editor specializing in series-level analysis.")
        prompt_parts.append("Your task is to analyze this entire fiction series for macro-level issues.")
        prompt_parts.append("")
        prompt_parts.append(context)
        prompt_parts.append("")
        prompt_parts.append("=== ANALYSIS FRAMEWORK ===")
        prompt_parts.append("Analyze the following aspects across the entire series:")
        prompt_parts.append("")
        prompt_parts.append("1. CHARACTER ARCS:")
        prompt_parts.append("   - Are character arcs consistent across books?")
        prompt_parts.append("   - Do major characters show growth?")
        prompt_parts.append("   - Are character motivations maintained?")
        prompt_parts.append("   - Are there contradictions in character behavior?")
        prompt_parts.append("")
        prompt_parts.append("2. PLOT THREADS:")
        prompt_parts.append("   - Are all setup plot threads resolved or carried forward?")
        prompt_parts.append("   - Is there proper foreshadowing and payoff?")
        prompt_parts.append("   - Are there dangling plot threads?")
        prompt_parts.append("   - Does each book contribute to the series arc?")
        prompt_parts.append("")
        prompt_parts.append("3. THEMES:")
        prompt_parts.append("   - Are themes developed consistently?")
        prompt_parts.append("   - Do themes deepen across books?")
        prompt_parts.append("   - Are themes properly explored and resolved?")
        prompt_parts.append("")
        prompt_parts.append("4. WORLD-BUILDING:")
        prompt_parts.append("   - Is lore consistent across books?")
        prompt_parts.append("   - Are there contradictions in world rules?")
        prompt_parts.append("   - Does the world feel cohesive?")
        prompt_parts.append("")
        prompt_parts.append("5. PACING:")
        prompt_parts.append("   - Does the series escalate properly?")
        prompt_parts.append("   - Are stakes raised appropriately?")
        prompt_parts.append("   - Is there proper balance of action/reflection?")
        prompt_parts.append("")
        prompt_parts.append("6. SERIES STRUCTURE:")
        prompt_parts.append("   - Does each book have a complete arc?")
        prompt_parts.append("   - Is there a clear series climax building?")
        prompt_parts.append("   - Are books properly connected?")
        prompt_parts.append("")
        prompt_parts.append("For each issue, provide:")
        prompt_parts.append("- Severity (critical/major/minor/suggestion)")
        prompt_parts.append("- Category (character_arc/plot_thread/theme/world_building/pacing/structure)")
        prompt_parts.append("- Specific description of the problem")
        prompt_parts.append("- Location (which book(s) affected)")
        prompt_parts.append("- Actionable suggestion for fixing")
        prompt_parts.append("- Rationale for why this matters")
        prompt_parts.append("")
        prompt_parts.append("Also identify 3-5 STRENGTHS of the series.")
        prompt_parts.append("")
        prompt_parts.append("Output as JSON:")
        prompt_parts.append('''{
  "overall_score": 8.0,
  "strengths": [
    "Strong character development across series",
    "Excellent world-building consistency"
  ],
  "suggestions": [
    {
      "severity": "major",
      "category": "plot_thread",
      "description": "The artifact from Book 1 is never resolved",
      "location": "Books 1-3",
      "suggestion": "Add resolution in Book 3 climax or establish it as ongoing thread",
      "rationale": "Unresolved plot threads frustrate readers and damage series coherence"
    }
  ],
  "summary": "Overall strong series with good character arcs. Main issues..."
}''')

        prompt = "\n".join(prompt_parts)

        # Call LLM
        messages = [
            SystemMessage(content="You are an expert series editor. Return ONLY valid JSON."),
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
                edit_id=f"series_{idx}",
                level="series",
                severity=sug.get('severity', 'suggestion'),
                category=sug.get('category', 'structure'),
                description=sug.get('description', ''),
                suggestion=sug.get('suggestion', ''),
                location={
                    'scope': 'series',
                    'affected_books': sug.get('location', 'Series-wide')
                },
                original_text=None,
                suggested_text=None,
                rationale=sug.get('rationale', ''),
                auto_apply=False  # Series-level edits need manual review
            ))

        edit_report = EditReport(
            editor_name="Series Editor",
            level="series",
            scope={'scope': 'entire_series', 'book_count': len(project.series.books)},
            overall_score=result.get('overall_score', 7.0),
            strengths=result.get('strengths', []),
            suggestions=edit_suggestions,
            summary=result.get('summary', 'Series analysis complete.'),
            estimated_revision_time=self._estimate_revision_time(len(edit_suggestions))
        )

        return edit_report

    def apply_edit(self, project: FictionProject, edit_suggestion: EditSuggestion) -> FictionProject:
        """
        Apply series-level edit

        Note: Series-level edits are typically guidance rather than direct text changes.
        They require manual implementation by the writer or other agents.
        """
        # Series-level edits are advisory - log them but don't auto-apply
        print(f"Series Editor suggestion: {edit_suggestion.description}")
        print(f"Manual action required: {edit_suggestion.suggestion}")

        # Could add to project metadata as action items
        if not hasattr(project.metadata, 'editorial_notes'):
            project.metadata.editorial_notes = []

        # Add note to metadata (if the field exists)
        try:
            if hasattr(project.metadata, 'editorial_notes'):
                project.metadata.editorial_notes.append({
                    'editor': 'Series Editor',
                    'category': edit_suggestion.category,
                    'suggestion': edit_suggestion.suggestion,
                    'severity': edit_suggestion.severity
                })
        except:
            pass

        return project

    def _estimate_revision_time(self, num_suggestions: int) -> str:
        """Estimate time for series-level revisions"""
        if num_suggestions == 0:
            return "No revisions needed"
        elif num_suggestions <= 3:
            return "2-4 hours"
        elif num_suggestions <= 7:
            return "1-2 days"
        else:
            return "3-5 days"
