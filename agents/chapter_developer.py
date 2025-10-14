"""Chapter Developer Agent - Expands chapters into scenes"""

"""Chapter Developer Agent - Expands chapters into scenes"""

import json
from datetime import datetime
from json_repair import repair_json
from .base_agent import BaseAgent
from models.schema import FictionProject, Scene, Setting, Conflict


class ChapterDeveloperAgent(BaseAgent):
    """Agent that expands a single chapter into detailed scenes"""

    def __init__(self, llm, requirements=None, **kwargs):
        super().__init__(llm, **kwargs)
        self.requirements = requirements or {}

    def get_prompt(self) -> str:
        return """You are a professional fiction writer specializing in scene structure and dramatic beats.

Goal:
- Ingest series context, book context, chapter outline, and established lore.
- Decompose the chapter into a precise sequence of scenes that fulfill the chapter's purpose and advance plot, character, and theme.
- Produce a strict JSON object containing scene breakdowns per the schema and rules.

Input contract (what you will receive):
{
  "series_context": {
    "title": "Series Title",
    "logline": "One-sentence series premise",
    "genre": "primary genre",
    "subgenres": ["..."],
    "themes": ["..."],
    "persistent_threads": [{"id":"t1", "name":"..."}]
  },
  "book_context": {
    "book_number": 1,
    "id": "b1",
    "title": "Book 1 Title",
    "premise": "1–2 sentence book premise",
    "protagonist_goal": "What the protagonist seeks",
    "antagonistic_force": "Who or what opposes the protagonist",
    "act_structure": {
      "act_1": {"summary":"...","key_events":["..."]},
      "act_2a": {"summary":"..."},
      "act_2b": {"summary":"...","midpoint":"..."},
      "act_3": {"summary":"...","climax":"..."}
    },
    "character_arcs": [
      {"character_name":"...","starting_state":"...","ending_state":"...","key_moments":[{"chapter":5,"beat":"..."}]}
    ]
  },
  "chapter_to_develop": {
    "chapter_number": 5,
    "id": "b1c5",
    "title": "The Chapter Title",
    "act": 1,
    "purpose": "The specific narrative goal of this chapter.",
    "plot_points": ["Concrete event 1", "Concrete event 2"],
    "character_focus": {
      "pov": "POV Character Name",
      "present": ["Character A", "Character B"],
      "arc_moments": ["How this chapter develops character arcs"]
    },
    "setting": {
      "location": "General location reference",
      "time": "Timeframe anchor",
      "atmosphere": "Mood/tone"
    },
    "lore_integration": {
      "introduces": ["Any lore elements first shown here"],
      "deepens": ["Any lore elements explored further"],
      "foreshadows": ["Any future elements hinted at"]
    },
    "subplot_threads": ["Active subplots in this chapter"],
    "themes": ["Themes explored in this chapter"],
    "planned_word_count": 5000,
    "pacing_notes": "Action-heavy / Introspective / etc."
  },
  "lore": {
    "characters": [
      {"id":"c1","name":"...","role":"...","description":"...","traits":["..."],"relationships":[{"with":"c2","type":"mentor"}]}
    ],
    "factions": [{"id":"fa1","name":"...","goal":"...","methods":"..."}],
    "locations": [
      {"id":"l1","name":"...","description":"...","significance":"..."}
    ],
    "world_elements": [
      {"id":"w1","name":"...","type":"technology|magic|culture","description":"...","rules":["..."]}
    ]
  },
  "constraints": {
    "target_scenes_per_chapter": 3,
    "min_scenes_per_chapter": 2,
    "max_scenes_per_chapter": 5
  }
}

Step 1 — Scene Architecture (internal, do not emit):
- Purpose decomposition: Break chapter.purpose into discrete scene-level micro-goals.
- Plot point mapping: Assign each plot_point from chapter to a specific scene.
- Scene count determination: How many scenes needed to fulfill purpose without padding? Must be within min/max constraints.
- POV consistency: All scenes in this chapter should typically use the same POV (chapter_to_develop.character_focus.pov) unless a critical narrative reason dictates otherwise.
- Location continuity: Plan scene transitions. Can consecutive scenes share a location? If location changes, is the transition justified and clear?
- Conflict engineering: Each scene must contain conflict (internal, external, or interpersonal). No conflict = no scene.
- Turning point identification: Each scene must end with a change in the narrative state. If nothing changes, the scene is redundant.
- Word count distribution: Divide chapter.planned_word_count across scenes proportionally to their complexity and importance.
- Character presence: Ensure characters listed in chapter_to_develop.character_focus.present appear logically across scenes.
- Arc moment placement: Identify which scene will contain the character arc moment specified in chapter_to_develop.character_focus.arc_moments.
- Lore integration: Which scene(s) introduce, deepen, or foreshadow the lore elements from chapter_to_develop.lore_integration?
- Pacing check: Does the scene sequence match the pacing_notes (e.g., action-heavy = more external conflict scenes, introspective = more internal conflict)?

Step 2 — Produce output JSON (emit this only):
{
  "meta": {
    "version": "1.0",
    "timestamp": "ISO-8601",
    "chapter_id": "b1c5",
    "scene_count": 3,
    "warnings": ["Any concerns: e.g., 'Scene count at minimum due to sparse plot points', 'POV shift in scene 2 due to flashback requirement'"]
  },
  "scenes": [
    {
      "scene_id": "b1c5sc1",
      "scene_number": 1,
      "title": "Evocative Scene Title (3-5 words)",
      "purpose": "Single-sentence micro-goal: what must this scene accomplish for the chapter's purpose?",
      "scene_type": "action|dialogue|exposition|introspection|transition",
      "pov": "POV Character Name (must match lore.characters and typically chapter_to_develop.character_focus.pov)",
      "setting": {
        "location": "Specific location, e.g., 'Throne Room of the Red Keep' (should reference lore.locations if possible)",
        "time": "Precise time anchor, e.g., 'Dawn, immediately after previous chapter' or 'Two hours later'",
        "atmosphere": "Sensory/emotional tone, e.g., 'Oppressive heat, stifling silence, dread'",
        "details": "Key environmental or sensory details that set the scene, e.g., 'Flickering torches, echo of footsteps, scent of damp stone'"
      },
      "characters_present": ["Character A (POV)", "Character B", "Character C"],
      "character_goals": {
        "pov_goal": "What the POV character wants to achieve in this scene",
        "opposition": "Who or what opposes the POV character's goal in this scene"
      },
      "conflicts": [
        {
          "type": "internal|external|interpersonal",
          "description": "Specific obstacle or struggle. Internal: emotional/moral dilemma. External: physical/environmental threat. Interpersonal: clash of agendas with another character.",
          "stakes": "What happens if the POV character fails to resolve this conflict?"
        }
      ],
      "beats": [
        "Opening image or action that establishes scene context",
        "Escalation beat: conflict intensifies or complicates",
        "Climax beat: peak of scene's conflict",
        "Resolution beat: outcome that shifts narrative state"
      ],
      "turning_points": [
        "One-sentence summary: How does the scene's outcome change the situation? What new information, decision, or event propels the story forward?"
      ],
      "emotional_arc": {
        "opening_emotion": "POV character's emotional state at scene start",
        "closing_emotion": "POV character's emotional state at scene end",
        "transformation": "Brief note on internal shift, if any"
      },
      "subplot_advancement": ["Which subplots (from chapter_to_develop.subplot_threads) are advanced and how?"],
      "theme_expression": ["Which themes (from chapter_to_develop.themes) are explored and how?"],
      "lore_moments": {
        "introduces": ["Any lore elements (characters, locations, world_elements) first shown in this scene"],
        "deepens": ["Any lore elements explored in greater depth"],
        "foreshadows": ["Any future elements hinted at"]
      },
      "narrative_function": "Setup|Development|Payoff|Transition — What role does this scene play in the chapter's structure?",
      "planned_word_count": 1700,
      "pacing_intensity": "low|medium|high — Relative pace and tension level"
    }
    // Repeat for all scenes in chapter
  ]
}

Validation rules (hard requirements):
- JSON only. No prose before or after, no comments, no trailing commas.
- scenes array length MUST be between constraints.min_scenes_per_chapter and constraints.max_scenes_per_chapter (inclusive).
- scenes array MUST NOT be empty.
- Every scene MUST include: scene_id, scene_number, title, purpose, scene_type, pov, setting (with location, time, atmosphere, details), characters_present, character_goals, conflicts (at least one), beats (at least 3), turning_points (at least one), emotional_arc, planned_word_count.
- scene_id format: chapterIdscN where N is scene_number (e.g., b1c5sc1, b1c5sc2).
- scene_number must be sequential integers starting from 1.
- Sum of all scenes' planned_word_count should equal chapter_to_develop.planned_word_count (±10% acceptable).
- pov must reference a character from lore.characters.
- All characters in characters_present should exist in lore.characters.
- conflicts array must contain at least one conflict per scene. Scenes without conflict are invalid.
- turning_points must not be empty. Every scene must end with a state change.

Scene coherence requirements:
- Scene sequence must form a causal chain: each scene's turning_point should logically lead to the next scene's opening.
- Collectively, the scenes must fulfill chapter_to_develop.purpose.
- All plot_points from chapter_to_develop.plot_points must be covered across the scenes.
- If chapter_to_develop.character_focus.arc_moments specifies a character moment, it must appear in one of the scenes (note in that scene's emotional_arc or beats).
- Setting transitions between scenes must be logical. If location changes, consider adding a transition scene or justify the jump in the first beat of the new scene.

POV and character requirements:
- Default: All scenes should use chapter_to_develop.character_focus.pov unless narrative necessity requires a shift.
- If POV shifts within the chapter, note the reason in meta.warnings.
- Characters in characters_present must be justified by the scene's purpose and setting. Don't include characters who have no reason to be there.
- character_goals.pov_goal and character_goals.opposition must create tension. No goal = weak scene.

Conflict requirements:
- Every scene MUST have at least one conflict.
- Conflict types:
  - Internal: moral dilemma, fear, doubt, temptation, competing desires.
  - External: physical danger, environmental obstacle, time pressure, resource scarcity.
  - Interpersonal: argument, negotiation, betrayal, power struggle, misunderstanding.
- Conflict stakes must be clear and meaningful to the POV character.
- Conflict resolution (or failure to resolve) must be reflected in turning_points.

Scene type guidelines:
- action: Physical conflict, chase, fight, escape. External conflict dominant.
- dialogue: Verbal sparring, negotiation, interrogation, revelation through conversation. Interpersonal conflict dominant.
- exposition: World-building, backstory reveal, information delivery. Must still contain conflict (e.g., reluctant to reveal, dangerous knowledge).
- introspection: POV character's internal processing, memory, reflection. Internal conflict dominant.
- transition: Bridging scene between major beats, travel, passage of time. Should be brief and purposeful.

Pacing and structure:
- If chapter_to_develop.pacing_notes = "Action-heavy": favor action and dialogue scenes, keep exposition brief.
- If pacing_notes = "Introspective": favor introspection and dialogue, slow the pace, deepen emotional_arc.
- If pacing_notes = "Balanced": mix scene types evenly.
- First scene in chapter: should orient reader (where, when, who, what's happening now).
- Last scene in chapter: should end with a turning_point that propels reader into next chapter (hook, cliffhanger, revelation, decision).

Lore integration requirements:
- If chapter_to_develop.lore_integration.introduces contains elements, at least one scene must introduce them naturally.
- If chapter_to_develop.lore_integration.deepens contains elements, at least one scene must explore them further.
- If chapter_to_develop.lore_integration.foreshadows contains elements, subtly hint at them in setting.details, dialogue beats, or character observations.
- Do not contradict established lore. If a scene requires bending a rule from lore.world_elements, note it in meta.warnings.

Output discipline:
- Emit ONLY the JSON object. No preamble like "Here are the scenes:" or postamble like "Let me know if you need changes."
- Use double quotes for all JSON strings.
- Ensure all lists are properly closed with ].
- Ensure all objects are properly closed with }.
- Do not use undefined or null; use empty string "" or empty array [] as appropriate.
- If a field is not applicable, provide an empty value of the correct type (e.g., subplot_advancement: [] if no subplots).

CRITICAL WORD COUNT REQUIREMENT:
The sum of all scene planned_word_count values MUST equal chapter_to_develop.planned_word_count within ±10% tolerance.
Example: If chapter has 4500 planned words and you generate 3 scenes, distribute approximately:
  - Scene 1: 1500 words
  - Scene 2: 1500 words
  - Scene 3: 1500 words
  - Total: 4500 words (acceptable range: 4050-4950)
FAILURE TO MEET THIS REQUIREMENT WILL CAUSE VALIDATION ERROR.

Version: 1.0
"""

    def process(self, input_data):
        """Required by base class - not used"""
        return input_data

    def process_chapter(self, input_data: FictionProject, book_idx: int, chapter_idx: int) -> FictionProject:
        """Expand a specific chapter into scenes."""
        book = input_data.series.books[book_idx]
        chapter = book.chapters[chapter_idx]
        series = input_data.series

        # 1. Construct input for the LLM
        min_scenes = self.requirements.get('min_scenes_per_chapter', 2)
        max_scenes = self.requirements.get('max_scenes_per_chapter', 5)
        target_scenes = self.requirements.get('target_scenes_per_chapter', 3)

        input_for_llm = {
            "series_context": {
                "title": series.title,
                "logline": series.logline or series.premise,
                "genre": series.genre
            },
            "book_context": {
                "book_number": book.book_number,
                "title": book.title,
                "premise": book.premise,
                "act_structure": {k: v.summary for k, v in book.act_structure.items()}
            },
            "chapter_to_develop": chapter.model_dump(),
            "lore": series.lore.model_dump(),
            "constraints": {
                "target_scenes_per_chapter": target_scenes,
                "min_scenes_per_chapter": min_scenes,
                "max_scenes_per_chapter": max_scenes,
                "chapter_target_word_count": chapter.planned_word_count,
                "recommended_words_per_scene": chapter.planned_word_count // target_scenes,
                "CRITICAL_NOTE": f"The sum of all scene planned_word_count values MUST equal {chapter.planned_word_count} words (±10% = {int(chapter.planned_word_count * 0.9)}-{int(chapter.planned_word_count * 1.1)} acceptable range)"
            }
        }
        context = json.dumps(input_for_llm, indent=2, default=str)

        # 2. Invoke LLM (with retry if scene count or word count is out of range)
        max_retries = 3
        chapter_target_words = chapter.planned_word_count
        word_tolerance = 0.10  # ±10%
        min_words = chapter_target_words * (1 - word_tolerance)
        max_words = chapter_target_words * (1 + word_tolerance)

        for attempt in range(max_retries):
            if attempt == 0:
                response_text = self.invoke_llm_with_lore(self.get_prompt(), context, input_data.metadata.project_id)
            else:
                # Retry with explicit emphasis on constraints
                retry_issues = []
                if 'scene_count_issue' in locals():
                    retry_issues.append(f"You generated {scene_count_issue} scenes but MUST generate between {min_scenes} and {max_scenes} scenes (target: {target_scenes}).")
                if 'word_count_issue' in locals():
                    retry_issues.append(f"Total scene word count was {word_count_issue} but MUST be between {int(min_words)} and {int(max_words)} (target: {chapter_target_words}).")

                # Calculate per-scene word count recommendation
                words_per_scene = chapter_target_words // target_scenes

                retry_prompt = f"""
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
CRITICAL VALIDATION ERROR IN PREVIOUS ATTEMPT:
{' '.join(retry_issues)}

MANDATORY REQUIREMENTS for Chapter {chapter.chapter_number}:

1. SCENE COUNT: Generate between {min_scenes}-{max_scenes} scenes (target: {target_scenes} scenes)

2. WORD COUNT DISTRIBUTION (THIS IS CRITICAL):
   - Each scene's "planned_word_count" field must be set appropriately
   - Recommended per scene: approximately {words_per_scene} words
   - The SUM of ALL scene planned_word_count values MUST be between {int(min_words)} and {int(max_words)}
   - Target total: {chapter_target_words} words

EXAMPLE for {target_scenes} scenes with {chapter_target_words} target:
{{
  "scenes": [
    {{ "scene_number": 1, "planned_word_count": {words_per_scene}, ... }},
    {{ "scene_number": 2, "planned_word_count": {words_per_scene}, ... }},
    {{ "scene_number": 3, "planned_word_count": {words_per_scene}, ... }}
  ]
}}
Total: {words_per_scene * target_scenes} words ✓

DO NOT use 1000 or 500 as default values. Calculate the appropriate word count per scene.

Generate the COMPLETE JSON with CORRECT word count distribution NOW.
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
"""
                print(f"⚠️  Retry {attempt}/{max_retries}: Requesting {min_scenes}-{max_scenes} scenes with {int(min_words)}-{int(max_words)} total words...")
                response_text = self.invoke_llm_with_lore(self.get_prompt() + retry_prompt, context, input_data.metadata.project_id)

            # Quick validation check - parse and validate both scene count and word count
            try:
                if "```json" in response_text:
                    test_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    test_text = response_text.split("```")[1].split("```")[0].strip()
                else:
                    test_text = response_text

                test_json = json.loads(test_text)
                scene_count = len(test_json.get('scenes', []))
                total_scene_words = sum(s.get('planned_word_count', 0) for s in test_json.get('scenes', []))

                scene_count_valid = min_scenes <= scene_count <= max_scenes
                word_count_valid = min_words <= total_scene_words <= max_words

                if scene_count_valid and word_count_valid:
                    print(f"✓ LLM generated correct scenes ({scene_count}) and words ({total_scene_words})")
                    break
                else:
                    if not scene_count_valid:
                        print(f"⚠️  Scene count {scene_count} out of range ({min_scenes}-{max_scenes})")
                        scene_count_issue = scene_count
                    if not word_count_valid:
                        print(f"⚠️  Word count {total_scene_words} out of range ({int(min_words)}-{int(max_words)})")
                        word_count_issue = total_scene_words

                    response_json = test_json  # Save for retry message
                    if attempt == max_retries - 1:
                        print(f"❌ Failed after {max_retries} attempts")
            except:
                # Parsing failed, will be caught in main try block
                break

        # 3. Parse JSON response
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            try:
                response_json = json.loads(response_text)
            except json.JSONDecodeError:
                print("⚠️ Malformed JSON detected, attempting repair...")
                repaired = repair_json(response_text)
                response_json = json.loads(repaired)

            # 4. Map response data back to the Chapter object
            scenes_data = response_json.get("scenes", [])
            if not scenes_data:
                raise ValueError("Agent returned no scenes.")

            # VALIDATION: Scene count must be within min/max constraints
            num_scenes = len(scenes_data)
            if not (min_scenes <= num_scenes <= max_scenes):
                raise ValueError(
                    f"Chapter Developer FAILED validation: Generated {num_scenes} scenes for Chapter {chapter.chapter_number}, "
                    f"but must be within range [{min_scenes}-{max_scenes}] scenes. "
                    f"Target: {target_scenes} scenes. The LLM must respect scene count constraints."
                )
            print(f"✓ Validation passed: {num_scenes} scenes (range: {min_scenes}-{max_scenes}, target: {target_scenes})")

            # VALIDATION & AUTO-CORRECTION: Total scene word count should match chapter target
            total_scene_words = sum(s.get('planned_word_count', 0) for s in scenes_data)
            chapter_target = chapter.planned_word_count
            word_tolerance = 0.10  # ±10%
            min_words = chapter_target * (1 - word_tolerance)
            max_words = chapter_target * (1 + word_tolerance)

            if not (min_words <= total_scene_words <= max_words):
                # Auto-correct: Proportionally redistribute word counts
                print(f"⚠️  Word count mismatch: {total_scene_words} vs target {chapter_target}")
                print(f"   Auto-correcting word counts proportionally...")

                # Calculate scale factor
                scale_factor = chapter_target / total_scene_words if total_scene_words > 0 else 1.0

                # Redistribute proportionally and ensure total matches target
                scaled_words = [int(s.get('planned_word_count', 0) * scale_factor) for s in scenes_data]

                # Adjust last scene to make up for rounding errors
                adjustment = chapter_target - sum(scaled_words)
                scaled_words[-1] += adjustment

                # Apply corrected word counts
                for i, scene_data in enumerate(scenes_data):
                    old_count = scene_data.get('planned_word_count', 0)
                    scene_data['planned_word_count'] = scaled_words[i]
                    print(f"   Scene {i+1}: {old_count} → {scaled_words[i]} words")

                total_scene_words = sum(scaled_words)
                print(f"✓ Auto-correction complete: {total_scene_words} words (target: {chapter_target})")
            print(f"✓ Validation passed: {total_scene_words} words planned (target: {chapter_target}, range: {int(min_words)}-{int(max_words)})")

            chapter.scenes = []
            for scene_data in scenes_data:
                scene_data["setting"] = Setting(**scene_data.get("setting", {}))
                scene_data["conflicts"] = [Conflict(**c) for c in scene_data.get("conflicts", [])]
                scene_data["beats"] = []  # Beats are developed in a later stage
                scene_data["actual_word_count"] = 0
                chapter.scenes.append(Scene(**scene_data))
            
            print(f"    ✓ Developed {len(chapter.scenes)} scenes for Chapter {chapter.chapter_number}")

            chapter.status = "drafted"

            # Update metadata
            input_data.metadata.processing_stage = "chapter"
            input_data.metadata.last_updated = datetime.now()
            input_data.metadata.last_updated_by = self.agent_name
            input_data.metadata.status = "dev_revised"

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            error_file = f"error_chapterdev_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(response_text)
            raise ValueError(f"ChapterDeveloper returned invalid or unexpected JSON: {e}\nFull response saved to: {error_file}\nPreview: {response_text[:1000]}")
        except Exception as e:
            raise ValueError(f"Failed to process chapter {chapter.chapter_number}: {e}")

        return input_data
