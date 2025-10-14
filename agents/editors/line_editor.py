#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Line Editor

Sentence-level editing for polish, clarity, and style
"""

import json
import re
from typing import Dict, List, Optional
from langchain.schema import HumanMessage, SystemMessage

from .base_editor import BaseEditor, EditReport, EditSuggestion
from models.schema import FictionProject


class LineEditor(BaseEditor):
    """
    Line-level editor focusing on:
    - Sentence variety and flow
    - Word choice and precision
    - Show vs tell
    - Purple prose and clichés
    - Grammar and syntax
    - Repetition
    """

    def __init__(self, llm, style_guide: Optional[str] = None):
        super().__init__(llm, "Line Editor", "line")
        self.style_guide = style_guide

    def analyze(self, project: FictionProject, book_idx: int, chapter_idx: int,
                scene_idx: int, beat_idx: Optional[int] = None,
                paragraph_idx: Optional[int] = None) -> EditReport:
        """
        Analyze prose at sentence/paragraph level

        Args:
            project: FictionProject instance
            book_idx: Book index
            chapter_idx: Chapter index
            scene_idx: Scene index
            beat_idx: Optional beat index (None = entire scene)
            paragraph_idx: Optional paragraph index (None = entire beat/scene)

        Returns:
            EditReport with line-level suggestions
        """
        book = project.series.books[book_idx]
        chapter = book.chapters[chapter_idx]
        scene = chapter.scenes[scene_idx]

        # Determine scope
        if paragraph_idx is not None and beat_idx is not None:
            # Single paragraph
            beat = scene.beats[beat_idx]
            if beat.prose and beat.prose.paragraphs:
                paragraph = beat.prose.paragraphs[paragraph_idx]
                prose_to_edit = paragraph.content
                scope_desc = f"Book {book.book_number}, Ch {chapter.chapter_number}, Scene {scene.scene_number}, Beat {beat_idx + 1}, Para {paragraph_idx + 1}"
            else:
                raise ValueError("Beat has no prose paragraphs")
        elif beat_idx is not None:
            # Entire beat
            beat = scene.beats[beat_idx]
            if beat.prose:
                if beat.prose.paragraphs:
                    prose_to_edit = "\n\n".join([p.content for p in beat.prose.paragraphs])
                else:
                    prose_to_edit = beat.prose.content
                scope_desc = f"Book {book.book_number}, Ch {chapter.chapter_number}, Scene {scene.scene_number}, Beat {beat_idx + 1}"
            else:
                raise ValueError("Beat has no prose")
        else:
            # Entire scene
            prose_parts = []
            for beat in scene.beats:
                if beat.prose:
                    if beat.prose.paragraphs:
                        prose_parts.extend([p.content for p in beat.prose.paragraphs])
                    elif beat.prose.content:
                        prose_parts.append(beat.prose.content)
            prose_to_edit = "\n\n".join(prose_parts)
            scope_desc = f"Book {book.book_number}, Ch {chapter.chapter_number}, Scene {scene.scene_number}"

        # Build context
        context = self._build_context(project, book_idx=book_idx, chapter_idx=chapter_idx, scene_idx=scene_idx)

        # Build prompt
        prompt_parts = []
        prompt_parts.append("You are an expert line editor with a keen eye for prose quality and style.")
        prompt_parts.append("")
        prompt_parts.append(context)
        prompt_parts.append("")

        if self.style_guide:
            prompt_parts.append("=== STYLE GUIDE ===")
            prompt_parts.append(self.style_guide)
            prompt_parts.append("")

        prompt_parts.append("=== PROSE TO EDIT ===")
        prompt_parts.append(prose_to_edit)
        prompt_parts.append("")
        prompt_parts.append("=== YOUR TASK ===")
        prompt_parts.append("Analyze this prose at the sentence and word level. Identify:")
        prompt_parts.append("1. Weak or imprecise word choices")
        prompt_parts.append("2. Repetitive sentence structures")
        prompt_parts.append("3. Purple prose or overwriting")
        prompt_parts.append("4. Telling instead of showing")
        prompt_parts.append("5. Clichés and overused phrases")
        prompt_parts.append("6. Grammatical issues")
        prompt_parts.append("7. Awkward phrasing")
        prompt_parts.append("8. Missed opportunities for stronger imagery")
        prompt_parts.append("")
        prompt_parts.append("For each issue, provide:")
        prompt_parts.append("- The problematic text")
        prompt_parts.append("- Why it's problematic")
        prompt_parts.append("- A specific revision")
        prompt_parts.append("- Severity: critical/major/minor/suggestion")
        prompt_parts.append("")
        prompt_parts.append("Also note 3-5 STRENGTHS in the prose.")
        prompt_parts.append("")
        prompt_parts.append("Output as JSON:")
        prompt_parts.append('''{
  "overall_score": 7.5,
  "strengths": ["Strong dialogue attribution", "Good use of sensory details"],
  "suggestions": [
    {
      "severity": "major",
      "category": "word_choice",
      "original_text": "The man walked slowly",
      "suggested_text": "The man shuffled",
      "location_hint": "paragraph 2, sentence 3",
      "rationale": "More precise verb conveys the character's exhaustion"
    }
  ],
  "summary": "Overall strong prose with good pacing. Main areas for improvement..."
}''')

        prompt = "\n".join(prompt_parts)

        # Call LLM
        messages = [
            SystemMessage(content="You are an expert line editor. Return ONLY valid JSON."),
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
                edit_id=f"line_{book_idx}_{chapter_idx}_{scene_idx}_{idx}",
                level="line",
                severity=sug.get('severity', 'suggestion'),
                category=sug.get('category', 'prose'),
                description=f"Line edit: {sug.get('rationale', 'Improvement suggested')}",
                suggestion=sug.get('suggested_text', ''),
                location={
                    'book_idx': book_idx,
                    'chapter_idx': chapter_idx,
                    'scene_idx': scene_idx,
                    'beat_idx': beat_idx,
                    'paragraph_idx': paragraph_idx,
                    'hint': sug.get('location_hint', '')
                },
                original_text=sug.get('original_text', ''),
                suggested_text=sug.get('suggested_text', ''),
                rationale=sug.get('rationale', ''),
                auto_apply=False  # Line edits should be reviewed
            ))

        edit_report = EditReport(
            editor_name="Line Editor",
            level="line",
            scope={
                'book_idx': book_idx,
                'chapter_idx': chapter_idx,
                'scene_idx': scene_idx,
                'beat_idx': beat_idx,
                'paragraph_idx': paragraph_idx,
                'description': scope_desc
            },
            overall_score=result.get('overall_score', 7.0),
            strengths=result.get('strengths', []),
            suggestions=edit_suggestions,
            summary=result.get('summary', 'Line editing complete.'),
            estimated_revision_time=self._estimate_revision_time(len(edit_suggestions))
        )

        return edit_report

    def apply_edit(self, project: FictionProject, edit_suggestion: EditSuggestion) -> FictionProject:
        """
        Apply a line edit to the project

        Args:
            project: FictionProject instance
            edit_suggestion: Edit to apply

        Returns:
            Modified project
        """
        loc = edit_suggestion.location
        book = project.series.books[loc['book_idx']]
        chapter = book.chapters[loc['chapter_idx']]
        scene = chapter.scenes[loc['scene_idx']]

        if loc.get('paragraph_idx') is not None and loc.get('beat_idx') is not None:
            # Edit specific paragraph
            beat = scene.beats[loc['beat_idx']]
            if beat.prose and beat.prose.paragraphs:
                paragraph = beat.prose.paragraphs[loc['paragraph_idx']]

                # Replace original text with suggested text
                if edit_suggestion.original_text and edit_suggestion.suggested_text:
                    paragraph.content = paragraph.content.replace(
                        edit_suggestion.original_text,
                        edit_suggestion.suggested_text
                    )
        elif loc.get('beat_idx') is not None:
            # Edit entire beat
            beat = scene.beats[loc['beat_idx']]
            if beat.prose:
                if beat.prose.paragraphs:
                    for paragraph in beat.prose.paragraphs:
                        if edit_suggestion.original_text in paragraph.content:
                            paragraph.content = paragraph.content.replace(
                                edit_suggestion.original_text,
                                edit_suggestion.suggested_text
                            )
                            break
                elif beat.prose.content:
                    beat.prose.content = beat.prose.content.replace(
                        edit_suggestion.original_text,
                        edit_suggestion.suggested_text
                    )
        else:
            # Edit entire scene - find and replace
            for beat in scene.beats:
                if beat.prose:
                    if beat.prose.paragraphs:
                        for paragraph in beat.prose.paragraphs:
                            if edit_suggestion.original_text in paragraph.content:
                                paragraph.content = paragraph.content.replace(
                                    edit_suggestion.original_text,
                                    edit_suggestion.suggested_text
                                )
                    elif beat.prose.content:
                        if edit_suggestion.original_text in beat.prose.content:
                            beat.prose.content = beat.prose.content.replace(
                                edit_suggestion.original_text,
                                edit_suggestion.suggested_text
                            )

        return project

    def _estimate_revision_time(self, num_suggestions: int) -> str:
        """Estimate time to review and apply suggestions"""
        if num_suggestions == 0:
            return "No revisions needed"
        elif num_suggestions <= 5:
            return "5-10 minutes"
        elif num_suggestions <= 15:
            return "15-30 minutes"
        elif num_suggestions <= 30:
            return "30-60 minutes"
        else:
            return "1-2 hours"

    def quick_fixes(self, project: FictionProject, book_idx: int, chapter_idx: int,
                    scene_idx: int) -> FictionProject:
        """
        Apply common quick fixes without full analysis:
        - Remove double spaces
        - Fix common typos
        - Standardize ellipses and em-dashes
        - Remove trailing whitespace

        Args:
            project: FictionProject
            book_idx, chapter_idx, scene_idx: Location

        Returns:
            Modified project
        """
        book = project.series.books[book_idx]
        chapter = book.chapters[chapter_idx]
        scene = chapter.scenes[scene_idx]

        for beat in scene.beats:
            if beat.prose:
                if beat.prose.paragraphs:
                    for paragraph in beat.prose.paragraphs:
                        paragraph.content = self._apply_quick_fixes(paragraph.content)
                elif beat.prose.content:
                    beat.prose.content = self._apply_quick_fixes(beat.prose.content)

        return project

    def _apply_quick_fixes(self, text: str) -> str:
        """Apply quick mechanical fixes to text"""
        # Remove double spaces
        text = re.sub(r'  +', ' ', text)

        # Standardize ellipses
        text = re.sub(r'\.\.\.+', '...', text)

        # Standardize em-dashes
        text = re.sub(r'--+', '—', text)

        # Remove trailing whitespace
        text = text.strip()

        # Fix common typos
        common_fixes = {
            r'\bthe the\b': 'the',
            r'\ban an\b': 'an',
            r'\ba a\b': 'a',
        }
        for pattern, replacement in common_fixes.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text
