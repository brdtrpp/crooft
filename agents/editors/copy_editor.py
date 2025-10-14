#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copy Editor

Final polish for publication
Focus: grammar, spelling, punctuation, formatting
"""

import json
import re
from typing import List, Dict, Any
from langchain.schema import HumanMessage, SystemMessage

from .base_editor import BaseEditor, EditReport, EditSuggestion
from models.schema import FictionProject


class CopyEditor(BaseEditor):
    """
    Copy editor focusing on:
    - Spelling
    - Grammar
    - Punctuation
    - Formatting consistency
    - Style guide compliance
    """

    def __init__(self, llm, style_guide: str = None):
        super().__init__(llm, "Copy Editor", "line")
        self.style_guide = style_guide

    def analyze(self, project: FictionProject, book_idx: int, chapter_idx: int, scene_idx: int, **kwargs) -> EditReport:
        """
        Perform final copy editing pass

        Args:
            project: FictionProject instance
            book_idx: Book index
            chapter_idx: Chapter index
            scene_idx: Scene index

        Returns:
            EditReport with copy editing suggestions
        """
        book = project.series.books[book_idx]
        chapter = book.chapters[chapter_idx]
        scene = chapter.scenes[scene_idx]

        # Extract prose
        prose_parts = []
        for beat in scene.beats:
            if beat.prose:
                if beat.prose.paragraphs:
                    for para in beat.prose.paragraphs:
                        prose_parts.append(para.content)
                elif beat.prose.content:
                    prose_parts.append(beat.prose.content)

        scene_prose = "\n\n".join(prose_parts)

        if not scene_prose:
            # Return empty report
            return EditReport(
                editor_name="Copy Editor",
                level="line",
                scope={'book_idx': book_idx, 'chapter_idx': chapter_idx, 'scene_idx': scene_idx},
                overall_score=10.0,
                strengths=[],
                suggestions=[],
                summary="No prose to edit.",
                estimated_revision_time="N/A"
            )

        # Build context
        context_parts = []
        context_parts.append(f"=== COPY EDITING ===")
        context_parts.append(f"Book {book.book_number}, Chapter {chapter.chapter_number}, Scene {scene.scene_number}")
        context_parts.append("")

        if self.style_guide:
            context_parts.append("=== STYLE GUIDE ===")
            context_parts.append(self.style_guide)
            context_parts.append("")

        context_parts.append("=== PROSE ===")
        context_parts.append(scene_prose)

        context = "\n".join(context_parts)

        # Build prompt
        prompt_parts = []
        prompt_parts.append("You are an expert copy editor performing final publication-ready review.")
        prompt_parts.append("Your task is to identify mechanical errors and formatting inconsistencies.")
        prompt_parts.append("")
        prompt_parts.append(context)
        prompt_parts.append("")
        prompt_parts.append("=== COPY EDITING CHECKLIST ===")
        prompt_parts.append("Check for:")
        prompt_parts.append("")
        prompt_parts.append("1. SPELLING:")
        prompt_parts.append("   - Misspelled words")
        prompt_parts.append("   - Typos and transpositions")
        prompt_parts.append("   - Homophones (there/their/they're, etc.)")
        prompt_parts.append("")
        prompt_parts.append("2. GRAMMAR:")
        prompt_parts.append("   - Subject-verb agreement")
        prompt_parts.append("   - Tense consistency")
        prompt_parts.append("   - Pronoun agreement")
        prompt_parts.append("   - Sentence fragments (unless intentional)")
        prompt_parts.append("   - Run-on sentences")
        prompt_parts.append("")
        prompt_parts.append("3. PUNCTUATION:")
        prompt_parts.append("   - Missing or extra commas")
        prompt_parts.append("   - Incorrect apostrophes")
        prompt_parts.append("   - Quotation mark placement")
        prompt_parts.append("   - Em-dash vs en-dash usage")
        prompt_parts.append("   - Ellipses formatting")
        prompt_parts.append("   - Period placement with quotes")
        prompt_parts.append("")
        prompt_parts.append("4. FORMATTING:")
        prompt_parts.append("   - Consistent dialogue formatting")
        prompt_parts.append("   - Paragraph breaks")
        prompt_parts.append("   - Capitalization consistency")
        prompt_parts.append("   - Number formatting (spelled out vs numerals)")
        prompt_parts.append("")
        prompt_parts.append("5. STYLE:")
        prompt_parts.append("   - Consistent voice and tense")
        prompt_parts.append("   - Style guide compliance (if provided)")
        prompt_parts.append("   - Consistency in character names/terms")
        prompt_parts.append("")
        prompt_parts.append("For each error found:")
        prompt_parts.append("- Severity (critical/major/minor)")
        prompt_parts.append("- Category (spelling/grammar/punctuation/formatting/style)")
        prompt_parts.append("- Original text (exact quote)")
        prompt_parts.append("- Corrected text")
        prompt_parts.append("- Brief explanation")
        prompt_parts.append("")
        prompt_parts.append("NOTE: Only flag actual errors, not stylistic preferences.")
        prompt_parts.append("Be conservative - when in doubt, don't flag it.")
        prompt_parts.append("")
        prompt_parts.append("Output as JSON:")
        prompt_parts.append('''{
  "overall_score": 9.0,
  "suggestions": [
    {
      "severity": "minor",
      "category": "punctuation",
      "original_text": "He said 'no'.",
      "suggested_text": "He said, 'No.'",
      "location_hint": "paragraph 3",
      "rationale": "Missing comma before dialogue, capitalize first word of dialogue"
    }
  ],
  "summary": "Generally clean copy with minor punctuation issues..."
}''')

        prompt = "\n".join(prompt_parts)

        # Call LLM
        messages = [
            SystemMessage(content="You are an expert copy editor. Return ONLY valid JSON. Be conservative - only flag actual errors."),
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
                edit_id=f"copy_{book_idx}_{chapter_idx}_{scene_idx}_{idx}",
                level="line",
                severity=sug.get('severity', 'minor'),
                category=sug.get('category', 'mechanical'),
                description=f"Copy edit: {sug.get('rationale', 'Correction needed')}",
                suggestion=sug.get('suggested_text', ''),
                location={
                    'book_idx': book_idx,
                    'chapter_idx': chapter_idx,
                    'scene_idx': scene_idx,
                    'hint': sug.get('location_hint', '')
                },
                original_text=sug.get('original_text', ''),
                suggested_text=sug.get('suggested_text', ''),
                rationale=sug.get('rationale', ''),
                auto_apply=sug.get('severity') == 'minor'  # Auto-apply minor corrections
            ))

        # Determine strengths based on lack of errors
        strengths = []
        if len(edit_suggestions) == 0:
            strengths = ["Perfect copy - no mechanical errors found"]
        elif len(edit_suggestions) <= 2:
            strengths = ["Very clean copy with minimal errors"]
        elif len(edit_suggestions) <= 5:
            strengths = ["Generally clean copy"]

        edit_report = EditReport(
            editor_name="Copy Editor",
            level="line",
            scope={
                'book_idx': book_idx,
                'chapter_idx': chapter_idx,
                'scene_idx': scene_idx,
                'description': f"Book {book_idx+1}, Ch {chapter_idx+1}, Scene {scene_idx+1}"
            },
            overall_score=result.get('overall_score', 9.0),
            strengths=strengths,
            suggestions=edit_suggestions,
            summary=result.get('summary', 'Copy editing complete.'),
            estimated_revision_time=self._estimate_revision_time(len(edit_suggestions))
        )

        return edit_report

    def apply_edit(self, project: FictionProject, edit_suggestion: EditSuggestion) -> FictionProject:
        """
        Apply copy edit to project

        Similar to LineEditor.apply_edit but for mechanical corrections
        """
        loc = edit_suggestion.location
        book = project.series.books[loc['book_idx']]
        chapter = book.chapters[loc['chapter_idx']]
        scene = chapter.scenes[loc['scene_idx']]

        # Apply to all beats in scene
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
        """Estimate time for copy editing corrections"""
        if num_suggestions == 0:
            return "No corrections needed"
        elif num_suggestions <= 5:
            return "5-10 minutes"
        elif num_suggestions <= 15:
            return "10-20 minutes"
        else:
            return "20-40 minutes"

    def auto_apply_common_fixes(self, project: FictionProject, book_idx: int, chapter_idx: int, scene_idx: int) -> FictionProject:
        """
        Auto-apply common mechanical fixes without LLM analysis

        Includes:
        - Double spaces
        - Straight quotes to curly quotes
        - Ellipses standardization
        - Em-dash standardization
        - Common typos
        """
        book = project.series.books[book_idx]
        chapter = book.chapters[chapter_idx]
        scene = chapter.scenes[scene_idx]

        for beat in scene.beats:
            if beat.prose:
                if beat.prose.paragraphs:
                    for paragraph in beat.prose.paragraphs:
                        paragraph.content = self._apply_mechanical_fixes(paragraph.content)
                elif beat.prose.content:
                    beat.prose.content = self._apply_mechanical_fixes(beat.prose.content)

        return project

    def _apply_mechanical_fixes(self, text: str) -> str:
        """Apply standard mechanical fixes to text"""
        # Remove double spaces
        text = re.sub(r'  +', ' ', text)

        # Standardize ellipses
        text = re.sub(r'\.\.\.+', '…', text)  # Use actual ellipsis character
        text = re.sub(r'\. \. \.', '…', text)

        # Standardize em-dashes
        text = re.sub(r'--+', '—', text)
        text = re.sub(r' - ', ' — ', text)  # Space-dash-space to em-dash with spaces

        # Convert straight quotes to curly quotes (basic)
        # Opening double quote
        text = re.sub(r'(?<!\w)"(?=\w)', '"', text)
        # Closing double quote
        text = re.sub(r'(?<=\w)"(?!\w)', '"', text)
        # Opening single quote
        text = re.sub(r"(?<!\w)'(?=\w)", ''', text)
        # Closing single quote / apostrophe
        text = re.sub(r"(?<=\w)'(?!\w)", ''', text)

        # Fix common typos
        common_fixes = {
            r'\bthe the\b': 'the',
            r'\ban an\b': 'an',
            r'\ba a\b': 'a',
            r'\bteh\b': 'the',
            r'\badn\b': 'and',
        }
        for pattern, replacement in common_fixes.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Remove trailing whitespace
        text = text.strip()

        return text
