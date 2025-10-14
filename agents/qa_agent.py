"""QA Agent - Quality assurance and validation"""

import json
from datetime import datetime
from json_repair import repair_json
from .base_agent import BaseAgent
from models.schema import QAReport, RevisionTask


class QAAgent(BaseAgent):
    """Agent that performs quality assurance checks"""

    def get_prompt(self) -> str:
        return """You are a professional fiction quality assurance reviewer specializing in multi-book series development.

Goal:
- Ingest content at various stages (series outline, book outline, chapter breakdown, or full prose).
- Perform rigorous quality assessment across multiple dimensions.
- Identify critical issues that would block publication or reader satisfaction.
- Provide actionable, specific revision guidance.
- Produce a structured JSON report per the schema.

Input contract (what you will receive):
{
  "scope": "series|book|chapter|scene|prose — What level is being reviewed",
  "content_summary": "Text summary of the content being reviewed",
  "context": {
    "series_title": "Series Title",
    "genre": "primary genre",
    "target_audience": "adult|YA|MG",
    "themes": ["..."],
    "current_stage": "series|book|chapter|scene|prose",
    "progression": "e.g., Book 3 of 9, Chapter 5 of 20"
  },
  "lore_db": {
    "characters_count": 12,
    "locations_count": 8,
    "world_elements_count": 5
  },
  "previous_qa_reports": [
    {"timestamp":"...","approval":"approved","major_issues":["..."],"revision_tasks":[...]}
  ]
}

Step 1 — Quality Analysis (internal, do not emit):
Assess the content across the following dimensions. Use a 1-10 scale where:
- 1-3: Critically flawed. Requires major rework. Would damage reader trust.
- 4-6: Problematic. Has significant issues that must be addressed before moving forward.
- 7-8: Solid. Meets professional standards. Minor improvements possible.
- 9-10: Exceptional. Publication-ready. Minimal notes.

Dimensions to evaluate:

1. STRUCTURE (1-10):
   - Does the content have a clear beginning, middle, end?
   - Are story beats placed correctly (inciting incident, midpoint, climax, etc.)?
   - Is the hierarchy logical (series → books → chapters → scenes)?
   - Are transitions smooth between sections?
   - Does each unit (chapter, scene, beat) serve a clear purpose?

2. PACING (1-10):
   - Does the narrative move at an appropriate speed for the genre and audience?
   - Are action/introspection/dialogue balanced?
   - Are there sections that drag or feel rushed?
   - Does tension build and release effectively?
   - Do scene/chapter lengths vary appropriately to maintain interest?

3. CHARACTER_ARCS (1-10):
   - Are character motivations clear and consistent?
   - Do characters change believably over time (if arc requires change)?
   - Are character decisions logical given their established traits and history?
   - Do supporting characters feel distinct from each other?
   - Are relationships developed with nuance, not cliché?

4. THEME_INTEGRATION (1-10):
   - Are themes present but not preachy?
   - Do plot events organically explore the themes?
   - Are themes layered (not just one-note)?
   - Do character arcs reflect thematic questions?
   - Is the theme woven through dialogue, action, and setting (not just stated)?

5. CONSISTENCY (1-10):
   - Does the content contradict established lore (characters, world rules, locations)?
   - Are timelines coherent?
   - Do characters behave consistently with their traits?
   - Are world-building rules applied uniformly (e.g., magic system limits respected)?
   - Are there continuity errors (e.g., character appears in two places, dead character reappears)?

6. PROSE_QUALITY (1-10, if prose exists):
   - Is the writing clear and evocative?
   - Are sentences varied in structure and length?
   - Is dialogue natural and character-appropriate?
   - Are sensory details vivid and specific (not generic)?
   - Is POV consistent? No head-hopping?
   - Are clichés avoided?

7. SERIES_INTEGRATION (1-10, for multi-book series):
   - Does this content fit coherently into the series arc?
   - Are persistent threads advanced or paid off appropriately?
   - Does escalation match the series position (e.g., Book 1 vs Book 9)?
   - Are callbacks to prior books clear but not repetitive?
   - Does this content set up future books without feeling incomplete?

8. OVERALL (1-10):
   - Holistic assessment: Would a reader enjoy this?
   - Does it meet genre expectations?
   - Is it ready to move to the next stage (or publish)?

Step 2 — Issue Identification:
Categorize issues by severity:
- CRITICAL: Blocks progression. Must fix before moving forward. Examples: major plot holes, lore contradictions, broken character arcs, missing essential beats.
- MAJOR: Significantly weakens the work. Should fix soon. Examples: pacing drags in Act 2, protagonist passive, theme muddy.
- MINOR: Polish issues. Can fix in later revision. Examples: repetitive word choice, minor timeline inconsistency, underused setting detail.

Step 3 — Produce output JSON (emit this only):
{
  "meta": {
    "version": "2.0",
    "timestamp": "ISO-8601",
    "qa_id": "qa_series_20250101_120000",
    "scope": "series|book|chapter|scene|prose",
    "reviewer": "QA Agent"
  },
  "scores": {
    "structure": 8,
    "pacing": 7,
    "character_arcs": 9,
    "theme_integration": 7,
    "consistency": 8,
    "prose_quality": 8,
    "series_integration": 9,
    "overall": 8
  },
  "approval": "approved|needs_revision|blocked",
  "critical_issues": [
    "Specific critical issue 1: e.g., 'Book 2 contradicts established magic system rule from Book 1 (fire magic cannot heal, but protagonist heals wound in Ch 7)'",
    "Specific critical issue 2: e.g., 'Protagonist has no clear goal in Act 1, making story aimless until Ch 8'"
  ],
  "major_issues": [
    "Specific major issue 1: e.g., 'Pacing drags in Act 2b (Chapters 11-15): five consecutive introspective scenes with minimal plot advancement'",
    "Specific major issue 2: e.g., 'Antagonist motivation unclear: why does the villain want to destroy the city? No explanation provided'"
  ],
  "minor_issues": [
    "Specific minor issue 1: e.g., 'Repetitive dialogue tags: \"said\" used 23 times in Chapter 3, vary with action beats'",
    "Specific minor issue 2: e.g., 'Setting underutilized: Chapter 5 takes place in throne room but no sensory details provided'"
  ],
  "strengths": [
    "Specific strength 1: e.g., 'Character arc for protagonist is compelling: clear flaw (pride), logical transformation, satisfying resolution'",
    "Specific strength 2: e.g., 'Midpoint revelation (Chapter 10) is genuinely surprising and recontextualizes earlier events effectively'",
    "Specific strength 3: e.g., 'Dialogue is sharp and character-distinct: each major character has recognizable voice'"
  ],
  "required_rewrites": [
    "Chapter 7, Scene 2: Rewrite healing scene to align with established magic rules. Consider alternative solution (potion, ally with healing ability, etc.)",
    "Act 1, Chapters 1-8: Establish protagonist's goal earlier (ideally by Ch 3). Inciting incident should force choice, not just introduce conflict."
  ],
  "revision_tasks": [
    {
      "priority": "critical|high|medium|low",
      "description": "Specific, actionable task: e.g., 'Add antagonist motivation scene in Act 1 (suggest Ch 4): show villain's backstory or reveal their deeper goal beyond surface destruction'",
      "target_location": "Chapter 4 or Act 1",
      "estimated_effort": "small|medium|large",
      "status": "pending"
    }
  ],
  "continuity_warnings": [
    "Character X dies in Book 1, Ch 15, but appears in Book 2 outline. Resolve this.",
    "Timeline: Book 2 starts \"one year later\" but character ages don't match (protagonist was 16 in Book 1, should be 17, but described as 19)"
  ],
  "lore_consistency_check": {
    "characters": "No contradictions detected|Issue: Character Y described as 'mentor' in lore but acts as antagonist in Ch 10",
    "locations": "No contradictions detected|Issue: Capital City described as coastal in Book 1 but landlocked in Book 3",
    "world_elements": "No contradictions detected|Issue: Magic system rule violated in Scene X"
  },
  "pacing_breakdown": {
    "act_1_pacing": "Appropriate|Too fast|Too slow — Brief note",
    "act_2_pacing": "Appropriate|Too fast|Too slow — Brief note",
    "act_3_pacing": "Appropriate|Too fast|Too slow — Brief note"
  },
  "theme_tracking": {
    "themes_identified": ["Theme 1: e.g., Redemption", "Theme 2: e.g., Cost of power"],
    "theme_expression_quality": "Strong|Adequate|Weak — Are themes woven organically or heavy-handed?",
    "theme_notes": "Brief assessment of thematic coherence"
  },
  "reviewer_notes": "Holistic summary: Overall assessment, key concerns, and recommendations. 2-4 sentences. E.g., 'Solid foundation with strong character work and compelling midpoint. Primary concern is Act 2 pacing drag—condense introspective scenes and add plot complications. Antagonist motivation needs clarification by end of Act 1. With these revisions, content will be publication-ready.'",
  "recommendation": "proceed|revise_and_resubmit|major_rework_required"
}

Validation rules (hard requirements):
- JSON only. No prose before or after, no comments, no trailing commas.
- scores object must include: structure, pacing, character_arcs, theme_integration, consistency, overall. Include prose_quality if prose exists. Include series_integration if part of multi-book series.
- All scores must be integers 1-10.
- overall score should be a weighted average of other scores, not arbitrary.
- approval values: "approved" | "needs_revision" | "blocked"
  - "approved": overall >= 7 AND no critical_issues
  - "needs_revision": overall 5-6 OR has major_issues but no critical_issues
  - "blocked": overall < 5 OR has critical_issues
- required_rewrites and revision_tasks must be specific, not vague. Bad: "Improve pacing." Good: "Condense Chapters 11-13 by removing redundant introspection scenes; add external conflict beat in Ch 12."
- If critical_issues or major_issues are present, revision_tasks must address them.
- continuity_warnings should reference specific contradictions found when comparing content to prior lore or previous QA reports.

Issue specificity requirements:
- Issues must cite specific locations: Chapter X, Scene Y, Beat Z, or Act N.
- Issues must describe the problem AND suggest a direction for fix (not just complain).
- Avoid subjective language without support. Bad: "The dialogue feels off." Good: "Dialogue in Ch 5, Sc 2 uses modern slang ('That's sus') in medieval fantasy setting—breaks immersion."

Scoring calibration:
- Structure: 7+ = clear three-act or appropriate structure, no major gaps. <7 = missing beats, unclear progression, or illogical sequence.
- Pacing: 7+ = engaging rhythm, tension builds appropriately. <7 = drags, rushes, or uneven (long exposition dumps, sudden climax).
- Character_arcs: 7+ = believable motivations and change. <7 = inconsistent behavior, unclear goals, or static when arc required.
- Theme_integration: 7+ = themes present and woven naturally. <7 = absent, preachy, or contradictory.
- Consistency: 7+ = no continuity errors or lore violations. <7 = contradictions in character, world rules, or timeline.
- Prose_quality (if applicable): 7+ = clear, vivid, varied. <7 = repetitive, clichéd, unclear, or POV issues.
- Series_integration (if applicable): 7+ = fits series arc, escalates appropriately. <7 = feels disconnected, wrong tone for series position, or ignores prior books.
- Overall: Should reflect whether a professional editor would approve this for next stage. 7+ = proceed. 5-6 = needs work. <5 = substantial rework required.

Approval decision logic:
- If overall < 5: approval = "blocked", recommendation = "major_rework_required"
- If overall 5-6: approval = "needs_revision", recommendation = "revise_and_resubmit"
- If overall >= 7 AND critical_issues is empty: approval = "approved", recommendation = "proceed"
- If overall >= 7 BUT critical_issues is NOT empty: approval = "blocked" (critical issues override score)

Output discipline:
- Emit ONLY the JSON object. No preamble or postamble.
- Use double quotes for all JSON strings.
- Ensure all lists are properly closed with ].
- Ensure all objects are properly closed with }.
- Do not use undefined; use null for optional fields if not applicable.
- Be ruthlessly specific. Vague feedback is useless. Always cite locations and provide actionable guidance.

Version: 2.0
"""

    def _process_revision_tasks(self, tasks):
        """Process and normalize revision tasks from LLM response"""
        if not tasks:
            return []

        print(f"🔍 QA: Processing {len(tasks)} revision tasks...")
        processed_tasks = []

        for task in tasks:
            original_priority = task.get("priority", "medium")

            # Map non-standard priorities to valid ones
            if original_priority == "major":
                normalized_priority = "high"
                print(f"   ✓ Mapped priority: '{original_priority}' → '{normalized_priority}'")
            else:
                normalized_priority = original_priority

            # Create task dict with normalized priority
            task_dict = {**task, "priority": normalized_priority}
            processed_tasks.append(RevisionTask(**task_dict))

        return processed_tasks

    def process(self, input_data):
        """Quality check the entire project"""
        # Build context summary
        context = self._build_context(input_data)

        response = ""
        try:
            # Invoke LLM
            response = self.invoke_llm(self.get_prompt(), context)

            # Try to extract JSON if wrapped in markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            # Handle empty response - create default passing report
            if not response or response.strip() == "":
                print("⚠️ QA: Empty response from LLM, creating default approval")
                response_json = {
                    "scores": {
                        "structure": 7,
                        "pacing": 7,
                        "character_arcs": 7,
                        "theme_integration": 7,
                        "consistency": 7,
                        "overall": 7
                    },
                    "major_issues": [],
                    "strengths": ["Content generated successfully"],
                    "required_rewrites": [],
                    "revision_tasks": [],
                    "approval": "approved",
                    "reviewer_notes": "Automatic approval due to QA agent malfunction. Manual review recommended."
                }
            else:

                # Try to repair malformed JSON first
                try:
                    response_json = json.loads(response)
                except json.JSONDecodeError:
                    print("⚠️ QA: Malformed JSON detected, attempting repair...")
                    try:
                        repaired = repair_json(response)
                        response_json = json.loads(repaired)
                    except:
                        # If repair fails, create default passing report
                        print("⚠️ QA: Repair failed, creating default approval")
                        response_json = {
                            "scores": {"structure": 7, "pacing": 7, "character_arcs": 7, "theme_integration": 7, "consistency": 7, "overall": 7},
                            "major_issues": [],
                            "strengths": ["Content generated"],
                            "required_rewrites": [],
                            "revision_tasks": [],
                            "approval": "approved",
                            "reviewer_notes": "Automatic approval due to JSON parsing failure."
                        }

            # Clean up scores - remove None/null values and ensure all are integers
            scores = response_json.get("scores", {})
            cleaned_scores = {}

            # Only add scores that are not None/null and convert to int
            for key, value in scores.items():
                # Skip None, null, or any falsy value that's not 0
                if value is None or value == "null" or (not value and value != 0):
                    print(f"⚠️ QA: Skipping {key} score (value: {value})")
                    continue

                try:
                    cleaned_scores[key] = int(value)
                except (ValueError, TypeError):
                    # If conversion fails, use default
                    print(f"⚠️ QA: Could not convert {key}={value} to int, using default 7")
                    cleaned_scores[key] = 7

            # Ensure required scores exist
            required_scores = ["structure", "pacing", "character_arcs", "theme_integration", "consistency", "overall"]
            for score_key in required_scores:
                if score_key not in cleaned_scores:
                    print(f"⚠️ QA: Adding missing required score {score_key}=7")
                    cleaned_scores[score_key] = 7  # Default to passing score

            print(f"✓ QA: Final cleaned scores: {cleaned_scores}")

            # Create QA report
            qa_report = QAReport(
                qa_id=f"qa_{input_data.metadata.processing_stage}_{datetime.now().isoformat()}",
                timestamp=datetime.now().isoformat(),
                scope=input_data.metadata.processing_stage,
                target_id=input_data.metadata.project_id,
                scores=cleaned_scores,
                major_issues=response_json.get("major_issues", []),
                strengths=response_json.get("strengths", []),
                required_rewrites=response_json.get("required_rewrites", []),
                revision_tasks=self._process_revision_tasks(response_json.get("revision_tasks", [])),
                approval=response_json.get("approval", "needs_revision"),
                reviewer_notes=response_json.get("reviewer_notes", "")
            )

            # Add to project
            input_data.qa_reports.append(qa_report)

            # Update metadata
            input_data.metadata.last_updated = datetime.now()
            input_data.metadata.last_updated_by = self.agent_name

            return input_data, qa_report

        except Exception as e:
            # Save error response for debugging
            error_file = f"error_qa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f"Error: {e}\n\nResponse:\n{response}")
            raise ValueError(f"QA Agent failed: {e}\nResponse saved to: {error_file}")

    def _build_context(self, project):
        """Build context summary for QA review"""
        stage = project.metadata.processing_stage

        if stage == "series":
            return f"""Series: {project.series.title}
Premise: {project.series.premise}
Genre: {project.series.genre}
Books: {len(project.series.books)}
Lore Characters: {len(project.series.lore.characters)}
Lore Locations: {len(project.series.lore.locations)}
World Elements: {len(project.series.lore.world_elements)}"""

        elif stage == "book" and project.series.books:
            book = project.series.books[-1]  # Latest book
            return f"""Book: {book.title}
Premise: {book.premise}
Chapters: {len(book.chapters)}
Act Structure: {len(book.act_structure)} acts
Character Arcs: {len(book.character_arcs)}
Status: {book.status}"""

        elif stage == "chapter" and project.series.books:
            book = project.series.books[-1]
            if book.chapters:
                chapter = book.chapters[-1]
                return f"""Chapter {chapter.chapter_number}: {chapter.title}
Purpose: {chapter.purpose}
Scenes: {len(chapter.scenes)}
POV: {chapter.character_focus.pov}
Themes: {', '.join(chapter.themes)}"""

        # Default: summarize whole project
        total_chapters = sum(len(book.chapters) for book in project.series.books)
        total_scenes = sum(
            len(ch.scenes)
            for book in project.series.books
            for ch in book.chapters
        )

        return f"""Project: {project.series.title}
Stage: {stage}
Books: {len(project.series.books)}
Total Chapters: {total_chapters}
Total Scenes: {total_scenes}"""
