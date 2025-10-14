#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scene Editor

Scene-level tactical editing
Focus: tension, dialogue, emotional impact
"""

import json
from typing import List, Dict, Any
from langchain.schema import HumanMessage, SystemMessage

from .base_editor import BaseEditor, EditReport, EditSuggestion
from models.schema import FictionProject


class SceneEditor(BaseEditor):
    """
    Scene-level editor focusing on:
    - Scene goals (does it advance plot/character?)
    - Tension and conflict
    - Dialogue quality and realism
    - Action clarity
    - Emotional impact
    - Sensory details
    """

    def __init__(self, llm):
        super().__init__(llm, "Scene Editor", "scene")

    def analyze(self, project: FictionProject, book_idx: int, chapter_idx: int, scene_idx: int, **kwargs) -> EditReport:
        """
        Analyze individual scene for effectiveness

        Args:
            project: FictionProject instance
            book_idx: Book index
            chapter_idx: Chapter index
            scene_idx: Scene index

        Returns:
            EditReport with scene-level suggestions
        """
        book = project.series.books[book_idx]
        chapter = book.chapters[chapter_idx]
        scene = chapter.scenes[scene_idx]

        # Build context
        context_parts = []

        context_parts.append(f"=== CONTEXT ===")
        context_parts.append(f"Book {book.book_number}: {book.title}")
        context_parts.append(f"Chapter {chapter.chapter_number}: {chapter.title}")
        context_parts.append(f"Scene {scene.scene_number} of {len(chapter.scenes)}")
        context_parts.append("")

        context_parts.append(f"=== SCENE {scene.scene_number} ===")
        context_parts.append(f"POV: {scene.pov_character}")
        context_parts.append(f"Location: {scene.location}")
        context_parts.append(f"Purpose: {scene.purpose}")
        context_parts.append(f"Beats: {len(scene.beats)}")
        context_parts.append("")

        # Extract prose from beats
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
            context_parts.append("(No prose generated yet)")
        else:
            context_parts.append("=== SCENE PROSE ===")
            # Show first 2000 chars
            if len(scene_prose) > 2000:
                context_parts.append(scene_prose[:2000] + "\n\n[...truncated for analysis...]")
            else:
                context_parts.append(scene_prose)

        context = "\n".join(context_parts)

        # Build prompt
        prompt_parts = []
        prompt_parts.append("You are an expert scene editor specializing in dramatic effectiveness and emotional impact.")
        prompt_parts.append("Your task is to analyze this scene for its effectiveness in advancing story and character.")
        prompt_parts.append("")
        prompt_parts.append(context)
        prompt_parts.append("")
        prompt_parts.append("=== ANALYSIS FRAMEWORK ===")
        prompt_parts.append("Analyze the following:")
        prompt_parts.append("")
        prompt_parts.append("1. SCENE PURPOSE:")
        prompt_parts.append("   - Does the scene have a clear goal?")
        prompt_parts.append("   - Does it advance plot, character, or both?")
        prompt_parts.append("   - Is the scene necessary or could it be cut/combined?")
        prompt_parts.append("   - Is there wasted space or meandering?")
        prompt_parts.append("")
        prompt_parts.append("2. CONFLICT & TENSION:")
        prompt_parts.append("   - Is there sufficient conflict?")
        prompt_parts.append("   - Does tension build throughout?")
        prompt_parts.append("   - Are stakes clear?")
        prompt_parts.append("   - Is there dramatic opposition?")
        prompt_parts.append("")
        prompt_parts.append("3. DIALOGUE:")
        prompt_parts.append("   - Does dialogue sound natural?")
        prompt_parts.append("   - Does each character have distinct voice?")
        prompt_parts.append("   - Does dialogue reveal character/advance plot?")
        prompt_parts.append("   - Is there too much/too little dialogue?")
        prompt_parts.append("   - Are dialogue tags appropriate?")
        prompt_parts.append("")
        prompt_parts.append("4. ACTION & CLARITY:")
        prompt_parts.append("   - Are actions clear and easy to visualize?")
        prompt_parts.append("   - Is choreography logical?")
        prompt_parts.append("   - Are cause-and-effect clear?")
        prompt_parts.append("   - Is pacing appropriate for the action?")
        prompt_parts.append("")
        prompt_parts.append("5. EMOTIONAL IMPACT:")
        prompt_parts.append("   - Does the scene evoke the intended emotions?")
        prompt_parts.append("   - Are emotional beats properly placed?")
        prompt_parts.append("   - Is emotional progression clear?")
        prompt_parts.append("   - Does the reader connect with characters?")
        prompt_parts.append("")
        prompt_parts.append("6. SENSORY DETAILS:")
        prompt_parts.append("   - Are there vivid sensory descriptions?")
        prompt_parts.append("   - Is the setting brought to life?")
        prompt_parts.append("   - Are all five senses engaged (when appropriate)?")
        prompt_parts.append("   - Is atmosphere effectively created?")
        prompt_parts.append("")
        prompt_parts.append("For each issue:")
        prompt_parts.append("- Severity (critical/major/minor/suggestion)")
        prompt_parts.append("- Category (purpose/conflict/dialogue/action/emotion/sensory)")
        prompt_parts.append("- Description")
        prompt_parts.append("- Location (which part of scene)")
        prompt_parts.append("- Actionable suggestion")
        prompt_parts.append("- Rationale")
        prompt_parts.append("")
        prompt_parts.append("Identify 2-3 STRENGTHS.")
        prompt_parts.append("")
        prompt_parts.append("Output as JSON:")
        prompt_parts.append('''{
  "overall_score": 7.0,
  "strengths": [
    "Strong dialogue with distinct character voices",
    "Good sensory details create atmosphere"
  ],
  "suggestions": [
    {
      "severity": "major",
      "category": "conflict",
      "description": "Scene lacks sufficient tension",
      "location": "Middle section",
      "suggestion": "Add opposition from secondary character, raise stakes by introducing time pressure",
      "rationale": "Scenes need dramatic tension to maintain reader engagement"
    }
  ],
  "summary": "Scene has good dialogue but needs stronger conflict..."
}''')

        prompt = "\n".join(prompt_parts)

        # Call LLM
        messages = [
            SystemMessage(content="You are an expert scene editor. Return ONLY valid JSON."),
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
                edit_id=f"scene_{book_idx}_{chapter_idx}_{scene_idx}_{idx}",
                level="scene",
                severity=sug.get('severity', 'suggestion'),
                category=sug.get('category', 'effectiveness'),
                description=sug.get('description', ''),
                suggestion=sug.get('suggestion', ''),
                location={
                    'book_idx': book_idx,
                    'chapter_idx': chapter_idx,
                    'scene_idx': scene_idx,
                    'part': sug.get('location', 'Scene-wide')
                },
                original_text=None,
                suggested_text=None,
                rationale=sug.get('rationale', ''),
                auto_apply=False
            ))

        edit_report = EditReport(
            editor_name="Scene Editor",
            level="scene",
            scope={
                'book_idx': book_idx,
                'chapter_idx': chapter_idx,
                'scene_idx': scene_idx,
                'pov': scene.pov_character,
                'beat_count': len(scene.beats)
            },
            overall_score=result.get('overall_score', 7.0),
            strengths=result.get('strengths', []),
            suggestions=edit_suggestions,
            summary=result.get('summary', 'Scene analysis complete.'),
            estimated_revision_time=self._estimate_revision_time(len(edit_suggestions))
        )

        return edit_report

    def apply_edit(self, project: FictionProject, edit_suggestion: EditSuggestion) -> FictionProject:
        """Apply scene-level edit"""
        print(f"Scene Editor suggestion: {edit_suggestion.description}")
        print(f"Manual action required: {edit_suggestion.suggestion}")

        try:
            if hasattr(project.metadata, 'editorial_notes'):
                project.metadata.editorial_notes.append({
                    'editor': 'Scene Editor',
                    'category': edit_suggestion.category,
                    'suggestion': edit_suggestion.suggestion,
                    'severity': edit_suggestion.severity,
                    'location': edit_suggestion.location
                })
        except:
            pass

        return project

    def _estimate_revision_time(self, num_suggestions: int) -> str:
        """Estimate time for scene-level revisions"""
        if num_suggestions == 0:
            return "No revisions needed"
        elif num_suggestions <= 3:
            return "20-40 minutes"
        elif num_suggestions <= 7:
            return "45 minutes - 1.5 hours"
        else:
            return "2-3 hours"
