#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chapter Editor

Chapter-level structural editing
Focus: flow, transitions, hooks
"""

import json
from typing import List, Dict, Any
from langchain.schema import HumanMessage, SystemMessage

from .base_editor import BaseEditor, EditReport, EditSuggestion
from models.schema import FictionProject


class ChapterEditor(BaseEditor):
    """
    Chapter-level editor focusing on:
    - Chapter opening hooks
    - Scene transitions
    - Chapter endings (cliffhangers, resolution)
    - Information flow
    - POV consistency
    - Tonal consistency
    """

    def __init__(self, llm):
        super().__init__(llm, "Chapter Editor", "chapter")

    def analyze(self, project: FictionProject, book_idx: int, chapter_idx: int, **kwargs) -> EditReport:
        """
        Analyze individual chapter for flow and structure

        Args:
            project: FictionProject instance
            book_idx: Book index
            chapter_idx: Chapter index

        Returns:
            EditReport with chapter-level suggestions
        """
        book = project.series.books[book_idx]
        chapter = book.chapters[chapter_idx]

        # Build context
        context_parts = []

        context_parts.append(f"=== BOOK CONTEXT ===")
        context_parts.append(f"Book {book.book_number}: {book.title}")
        context_parts.append(f"Total Chapters: {len(book.chapters)}")
        context_parts.append(f"Chapter Position: {chapter.chapter_number} of {len(book.chapters)}")
        context_parts.append("")

        context_parts.append(f"=== CHAPTER {chapter.chapter_number}: {chapter.title} ===")
        context_parts.append(f"Status: {chapter.status}")
        context_parts.append(f"Purpose: {chapter.purpose}")
        context_parts.append(f"Scenes: {len(chapter.scenes)}")
        context_parts.append("")

        # Previous chapter context (if exists)
        if chapter_idx > 0:
            prev_chapter = book.chapters[chapter_idx - 1]
            context_parts.append(f"=== PREVIOUS CHAPTER ({prev_chapter.chapter_number}): {prev_chapter.title} ===")
            context_parts.append(f"Purpose: {prev_chapter.purpose}")
            if prev_chapter.scenes:
                last_scene = prev_chapter.scenes[-1]
                context_parts.append(f"Last scene POV: {last_scene.pov_character}")
                context_parts.append(f"Last scene purpose: {last_scene.purpose}")
            context_parts.append("")

        # Next chapter context (if exists)
        if chapter_idx < len(book.chapters) - 1:
            next_chapter = book.chapters[chapter_idx + 1]
            context_parts.append(f"=== NEXT CHAPTER ({next_chapter.chapter_number}): {next_chapter.title} ===")
            context_parts.append(f"Purpose: {next_chapter.purpose}")
            context_parts.append("")

        # Scene breakdown
        context_parts.append("=== SCENES ===")
        for scene in chapter.scenes:
            beat_count = len(scene.beats)
            word_estimate = sum(
                len(beat.prose.content.split()) if beat.prose and beat.prose.content else
                sum(len(p.content.split()) for p in beat.prose.paragraphs) if beat.prose and beat.prose.paragraphs else 0
                for beat in scene.beats
            )

            context_parts.append(f"Scene {scene.scene_number}:")
            context_parts.append(f"  POV: {scene.pov_character}")
            context_parts.append(f"  Location: {scene.location}")
            context_parts.append(f"  Purpose: {scene.purpose}")
            context_parts.append(f"  Beats: {beat_count}, ~{word_estimate:,} words")

            # First beat snippet for context
            if scene.beats and scene.beats[0].prose:
                first_beat = scene.beats[0]
                if first_beat.prose.paragraphs:
                    first_text = first_beat.prose.paragraphs[0].content[:200]
                elif first_beat.prose.content:
                    first_text = first_beat.prose.content[:200]
                else:
                    first_text = "(no prose yet)"
                context_parts.append(f"  Opening: {first_text}...")

            context_parts.append("")

        context = "\n".join(context_parts)

        # Build prompt
        prompt_parts = []
        prompt_parts.append("You are an expert chapter editor specializing in narrative flow and structure.")
        prompt_parts.append("Your task is to analyze this chapter for flow, transitions, and effectiveness.")
        prompt_parts.append("")
        prompt_parts.append(context)
        prompt_parts.append("")
        prompt_parts.append("=== ANALYSIS FRAMEWORK ===")
        prompt_parts.append("Analyze the following:")
        prompt_parts.append("")
        prompt_parts.append("1. CHAPTER OPENING:")
        prompt_parts.append("   - Does it hook the reader immediately?")
        prompt_parts.append("   - Does it connect smoothly from the previous chapter?")
        prompt_parts.append("   - Is the opening scene necessary or could it be cut?")
        prompt_parts.append("   - Does it establish POV, location, and conflict quickly?")
        prompt_parts.append("")
        prompt_parts.append("2. SCENE TRANSITIONS:")
        prompt_parts.append("   - Do scenes flow naturally into each other?")
        prompt_parts.append("   - Are time/location jumps clear?")
        prompt_parts.append("   - Is POV maintained or shifted properly?")
        prompt_parts.append("   - Are transitions smooth or jarring?")
        prompt_parts.append("")
        prompt_parts.append("3. CHAPTER ENDING:")
        prompt_parts.append("   - Does it end with a hook/cliffhanger (if appropriate)?")
        prompt_parts.append("   - Does it provide satisfaction while creating anticipation?")
        prompt_parts.append("   - Does it conclude the chapter's goal effectively?")
        prompt_parts.append("   - Does it set up the next chapter?")
        prompt_parts.append("")
        prompt_parts.append("4. INFORMATION FLOW:")
        prompt_parts.append("   - Is information revealed at the right pace?")
        prompt_parts.append("   - Is there info-dumping?")
        prompt_parts.append("   - Are revelations properly set up?")
        prompt_parts.append("   - Is the reader's knowledge managed well?")
        prompt_parts.append("")
        prompt_parts.append("5. POV CONSISTENCY:")
        prompt_parts.append("   - If single POV, is it maintained?")
        prompt_parts.append("   - If multiple POV, are shifts clear and purposeful?")
        prompt_parts.append("   - Is head-hopping avoided?")
        prompt_parts.append("")
        prompt_parts.append("6. TONE & ATMOSPHERE:")
        prompt_parts.append("   - Is the tone consistent throughout?")
        prompt_parts.append("   - Does atmosphere support the story beats?")
        prompt_parts.append("   - Are emotional beats properly paced?")
        prompt_parts.append("")
        prompt_parts.append("For each issue:")
        prompt_parts.append("- Severity (critical/major/minor/suggestion)")
        prompt_parts.append("- Category (opening/transitions/ending/info_flow/pov/tone)")
        prompt_parts.append("- Description")
        prompt_parts.append("- Location (which scene)")
        prompt_parts.append("- Actionable suggestion")
        prompt_parts.append("- Rationale")
        prompt_parts.append("")
        prompt_parts.append("Identify 2-4 STRENGTHS.")
        prompt_parts.append("")
        prompt_parts.append("Output as JSON:")
        prompt_parts.append('''{
  "overall_score": 7.5,
  "strengths": [
    "Strong chapter opening hook",
    "Smooth scene transitions"
  ],
  "suggestions": [
    {
      "severity": "major",
      "category": "ending",
      "description": "Chapter ending feels flat, no hook",
      "location": "Final scene",
      "suggestion": "End with revelation about the artifact instead of travel logistics",
      "rationale": "Chapter endings should create anticipation for the next chapter"
    }
  ],
  "summary": "Good flow overall but chapter ending needs strengthening..."
}''')

        prompt = "\n".join(prompt_parts)

        # Call LLM
        messages = [
            SystemMessage(content="You are an expert chapter editor. Return ONLY valid JSON."),
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
                edit_id=f"chapter_{book_idx}_{chapter_idx}_{idx}",
                level="chapter",
                severity=sug.get('severity', 'suggestion'),
                category=sug.get('category', 'flow'),
                description=sug.get('description', ''),
                suggestion=sug.get('suggestion', ''),
                location={
                    'book_idx': book_idx,
                    'chapter_idx': chapter_idx,
                    'affected_scene': sug.get('location', 'Chapter-wide')
                },
                original_text=None,
                suggested_text=None,
                rationale=sug.get('rationale', ''),
                auto_apply=False
            ))

        edit_report = EditReport(
            editor_name="Chapter Editor",
            level="chapter",
            scope={
                'book_idx': book_idx,
                'chapter_idx': chapter_idx,
                'chapter_title': chapter.title,
                'scene_count': len(chapter.scenes)
            },
            overall_score=result.get('overall_score', 7.0),
            strengths=result.get('strengths', []),
            suggestions=edit_suggestions,
            summary=result.get('summary', 'Chapter analysis complete.'),
            estimated_revision_time=self._estimate_revision_time(len(edit_suggestions))
        )

        return edit_report

    def apply_edit(self, project: FictionProject, edit_suggestion: EditSuggestion) -> FictionProject:
        """Apply chapter-level edit"""
        print(f"Chapter Editor suggestion: {edit_suggestion.description}")
        print(f"Manual action required: {edit_suggestion.suggestion}")

        try:
            if hasattr(project.metadata, 'editorial_notes'):
                project.metadata.editorial_notes.append({
                    'editor': 'Chapter Editor',
                    'category': edit_suggestion.category,
                    'suggestion': edit_suggestion.suggestion,
                    'severity': edit_suggestion.severity,
                    'location': edit_suggestion.location
                })
        except:
            pass

        return project

    def _estimate_revision_time(self, num_suggestions: int) -> str:
        """Estimate time for chapter-level revisions"""
        if num_suggestions == 0:
            return "No revisions needed"
        elif num_suggestions <= 3:
            return "30 minutes - 1 hour"
        elif num_suggestions <= 7:
            return "1-3 hours"
        else:
            return "3-6 hours"
