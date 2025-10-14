"""Prose Generator Agent - Converts beats into narrative prose"""

import json
from datetime import datetime
from .base_agent import BaseAgent
from models.schema import Prose, Paragraph, DialogueLine

# Try to import json_repair for malformed JSON handling
try:
    from json_repair import repair_json
    HAS_JSON_REPAIR = True
except ImportError:
    HAS_JSON_REPAIR = False


class ProseGeneratorAgent(BaseAgent):
    """Agent that generates prose from beats"""

    def get_prompt(self) -> str:
        return """You are a professional fiction writer specializing in narrative prose, dialogue craft, and POV consistency.

Goal:
- Ingest a beat specification (description, emotional tone, actions, dialogue summary) and context (scene, chapter, book, series).
- Generate publication-quality narrative prose that brings the beat to life.
- Produce structured JSON with full prose text and paragraph-level breakdown per the schema.

Input contract (what you will receive):
{
  "series_context": {
    "title": "Series Title",
    "genre": "primary genre",
    "themes": ["..."]
  },
  "book_context": {
    "book_number": 1,
    "title": "Book 1 Title"
  },
  "chapter_context": {
    "chapter_number": 5,
    "title": "Chapter Title"
  },
  "scene_context": {
    "scene_number": 2,
    "title": "Scene Title",
    "pov": "POV Character Name",
    "setting": {
      "location": "Specific location",
      "time": "Time anchor",
      "atmosphere": "Mood/tone"
    },
    "characters_present": ["Character A", "Character B"]
  },
  "beat_to_write": {
    "beat_number": 3,
    "description": "What happens in this beat",
    "emotional_tone": "Joy|Fear|Anger|Sadness|Anticipation|Surprise|etc.",
    "character_actions": ["Action 1", "Action 2"],
    "dialogue_summary": "Brief summary of what is said or 'None' if no dialogue",
    "sensory_details": ["Sight", "Sound", "Smell", "Touch", "Taste"]
  },
  "previous_context": "Last 200 words of previous beat for continuity (or empty string if first beat)",
  "target_word_count": 350
}

Step 1 — Prose Construction (internal, do not emit):
- POV discipline: Write from scene_context.pov perspective. Use close third-person or first-person as appropriate. Filter all observations, descriptions, and judgments through the POV character's lens.
- Sensory grounding: Incorporate beat_to_write.sensory_details naturally. Show, don't tell. Ground the reader in the physical environment.
- Emotional layering: Convey beat_to_write.emotional_tone through:
  - POV character's physical reactions (heart racing, hands trembling, etc.)
  - Internal thoughts and judgments
  - Dialogue subtext and tone
  - Environmental description colored by emotion
- Action clarity: Translate beat_to_write.character_actions into clear, vivid action sequences. Avoid vague verbs. Be specific.
- Dialogue craft: If beat_to_write.dialogue_summary indicates conversation:
  - Write natural, character-appropriate dialogue.
  - Use dialogue tags and action beats to show emotion and movement.
  - Avoid exposition dumps in dialogue; reveal through subtext and conflict.
  - If POV character speaks, include internal thoughts before/after key lines.
- Paragraph rhythm: Vary paragraph length for pacing. Short paragraphs for action/tension. Longer for introspection/description.
- Continuity: If previous_context is provided, ensure smooth transition. Don't repeat information. Build forward.
- Word count target: Aim for target_word_count ±50 words. If beat is simple, don't pad. If complex, don't rush.

Step 2 — Produce output JSON (emit this only):
{
  "meta": {
    "version": "2.0",
    "timestamp": "ISO-8601",
    "beat_id": "b1c5sc2bt3",
    "warnings": ["Any concerns: e.g., 'Minimal sensory details provided', 'Dialogue summary vague, improvised specifics'"]
  },
  "full_prose": "Complete prose text with all paragraphs combined into a single continuous narrative. Use proper paragraph breaks (double newline). Include all dialogue with proper quotation marks and attribution.",
  "paragraphs": [
    {
      "paragraph_number": 1,
      "paragraph_type": "narrative|dialogue|mixed|description|action|internal_monologue",
      "content": "The full paragraph text exactly as it appears in full_prose. Include all dialogue with quotes and attribution.",
      "dialogue_lines": [
        {
          "speaker": "Character Name",
          "dialogue": "What they say (without quotes)",
          "action": "Dialogue tag or action beat, e.g., 'she whispered' or 'he turned away'",
          "internal_thought": "If POV character, their thoughts during/after this line (optional, or null)"
        }
      ],
      "pov_character": "POV Character Name if this paragraph contains their internal thoughts, else null",
      "word_count": 45,
      "primary_emotion": "Dominant emotion conveyed in this paragraph",
      "narrative_function": "Setup|Action|Dialogue|Introspection|Transition — What this paragraph does"
    }
  ],
  "word_count": 350,
  "tone_assessment": "Brief note: Does the prose match the emotional_tone and atmosphere?",
  "pov_consistency": "Brief note: Any POV slips or head-hopping issues?"
}

Validation rules (hard requirements):
- JSON only. No prose before or after, no comments, no trailing commas.
- full_prose must be non-empty and contain all paragraph content.
- paragraphs array must match the paragraph structure of full_prose exactly.
- paragraph_number must be sequential integers starting from 1.
- Each paragraph.content must be an exact substring of full_prose (accounting for paragraph breaks).
- If paragraph contains dialogue, dialogue_lines must extract all speaking lines.
- word_count (top-level) must equal sum of all paragraphs[].word_count (±2 words acceptable for rounding).
- word_count should be within target_word_count ±50 words.

Paragraph type definitions:
- narrative: Pure description or action with no dialogue. Establishes setting, describes events, shows physical movement.
- dialogue: Primarily conversation. May include action beats, but dialogue is dominant.
- mixed: Roughly equal blend of description/action and dialogue within the same paragraph.
- description: Focused on setting, environment, or character appearance. Minimal action.
- action: Physical movement, conflict, or events. Fast-paced, verb-driven.
- internal_monologue: POV character's thoughts, memories, or internal processing. No external action or dialogue.

POV discipline requirements:
- If scene_context.pov is third-person (e.g., "Kael"), write in close third: "Kael felt", "He noticed", "To him, the room seemed...".
- If scene_context.pov is first-person (e.g., "I"), write in first: "I felt", "I noticed", "The room seemed...".
- Do NOT describe what other characters think or feel unless the POV character infers it from external cues (facial expressions, body language, tone).
- All sensory details must be filtered through the POV character's perception.
- Internal thoughts (internal_monologue paragraphs or internal_thought fields) must belong to the POV character only.

Dialogue craft requirements:
- Use action beats for attribution when possible to show character movement and emotion: "She slammed the door. 'I'm done.'"
- Avoid repetitive dialogue tags. Vary between said/asked and action beats.
- If dialogue_summary says "None", do not invent dialogue. Focus on narration, action, or internal thought.
- If dialogue_summary is vague (e.g., "They argue"), invent specific dialogue consistent with character motivations and scene context.
- Dialogue must sound natural. Avoid stilted exposition. Characters should speak in distinct voices (if character traits are known from prior context).

Emotional tone requirements:
- beat_to_write.emotional_tone must be evident in the prose.
- Show emotion through:
  - Physical sensations: "Her stomach twisted." (fear), "His chest swelled." (pride)
  - Environmental perception: "The shadows seemed to close in." (fear), "The colors felt brighter." (joy)
  - Internal thoughts: "What if I'm wrong?" (doubt), "Finally." (relief)
  - Dialogue tone and word choice
- Do not tell emotion directly ("He was angry"). Show it ("His jaw clenched. 'Get out.'").

Sensory detail requirements:
- If beat_to_write.sensory_details includes specific senses, incorporate them naturally.
- Prioritize sight and sound as default. Add smell, touch, taste if specified or contextually relevant.
- Avoid generic descriptions ("the room was dark"). Be specific ("shadows pooled in the corners, swallowing the faint moonlight").

Paragraph rhythm and pacing:
- Action-heavy beats: Use shorter paragraphs (2-4 sentences), punchy verbs, minimal description. Keep momentum.
- Introspective beats: Longer paragraphs (4-7 sentences), deeper internal thoughts, richer description. Slow down.
- Dialogue-heavy beats: Mix short dialogue exchanges with action beats. Vary paragraph length to reflect conversation flow.
- Aim for 2-5 paragraphs total. If beat is simple, 2-3 paragraphs. If complex, 4-5.

Continuity requirements:
- If previous_context is provided, ensure the opening sentence or action flows naturally from it.
- Do not repeat information from previous_context unless essential for clarity.
- If previous_context ends mid-action, continue the action. If it ends with a line of dialogue, respond to it.

Output discipline:
- Emit ONLY the JSON object. No preamble like "Here is the prose:" or postamble.
- CRITICAL: Your response must START with { and END with }. Nothing before or after.
- Use double quotes for all JSON strings.
- Escape internal quotes within prose: "She said, \\"I can't.\\""
- Ensure full_prose is a single string with paragraph breaks indicated by double newline (\\n\\n).
- Ensure all lists are properly closed with ].
- Ensure all objects are properly closed with }.
- Do not use undefined or null except where specified (e.g., internal_thought or pov_character can be null).
- If you must include explanatory text, put it INSIDE the meta.warnings array, not outside the JSON.

REMINDER: Output MUST be valid JSON starting with { and ending with }. No text before or after.

Version: 2.0
"""

    def process(self, input_data):
        """Required by base class - not used"""
        return input_data

    def process_beat(self, input_data, book_idx: int, chapter_idx: int, scene_idx: int, beat_idx: int, style_guide: str = None,
                     min_words: int = 200, max_words: int = 500, max_retries: int = 3):
        """Generate prose for a specific beat

        Args:
            input_data: FictionProject
            book_idx: Book index
            chapter_idx: Chapter index
            scene_idx: Scene index
            beat_idx: Beat index
            style_guide: Optional style guide for prose generation
            min_words: Minimum word count (default: 200)
            max_words: Maximum word count (default: 500)
            max_retries: Maximum retry attempts for word count enforcement (default: 3)
        """
        book = input_data.series.books[book_idx]
        chapter = book.chapters[chapter_idx]
        scene = chapter.scenes[scene_idx]
        beat = scene.beats[beat_idx]

        # Get previous prose for context continuity
        previous_prose = ""
        if beat_idx > 0:
            prev_beat = scene.beats[beat_idx - 1]
            if prev_beat.prose and prev_beat.prose.content:
                # Get last 200 words
                words = prev_beat.prose.content.split()
                previous_prose = " ".join(words[-200:])

        # Build context with optional style guide
        context_parts = [
            f"Book: {book.title}",
            f"Chapter {chapter.chapter_number}: {chapter.title}",
            f"Scene {scene.scene_number}: {scene.title}",
            f"POV: {scene.pov}",
            f"Setting: {scene.setting.location}, {scene.setting.time}",
            f"Atmosphere: {scene.setting.atmosphere}",
            "",
            f"Beat {beat.beat_number}:",
            f"Description: {beat.description}",
            f"Emotional Tone: {beat.emotional_tone}",
            f"Actions: {', '.join(beat.character_actions)}",
            f"Dialogue: {beat.dialogue_summary}",
        ]

        # Add style guide if provided
        if style_guide and style_guide.strip():
            context_parts.insert(0, "=== STYLE GUIDE ===")
            context_parts.insert(1, style_guide.strip())
            context_parts.insert(2, "=== END STYLE GUIDE ===")
            context_parts.insert(3, "")

        context_parts.extend([
            "",
            "Previous context (last 200 words):",
            previous_prose,
            "",
            "Write prose for this beat (200-500 words)."
        ])

        # Retry loop for word count enforcement
        last_word_count = 0  # Initialize for retry feedback
        for attempt in range(max_retries):
            # Add word count feedback to context on retries
            if attempt > 0 and last_word_count > 0:
                context_parts_with_feedback = context_parts.copy()
                context_parts_with_feedback.append(f"\n⚠️ WORD COUNT ENFORCEMENT (Attempt {attempt + 1}/{max_retries}):")
                context_parts_with_feedback.append(f"Previous attempt was {last_word_count} words.")
                if last_word_count < min_words:
                    context_parts_with_feedback.append(f"TOO SHORT! Must be at least {min_words} words. Add more sensory details, internal thoughts, or expand actions.")
                else:
                    context_parts_with_feedback.append(f"TOO LONG! Must be at most {max_words} words. Be more concise, remove unnecessary description.")
                context = "\n".join(context_parts_with_feedback)
            else:
                context = "\n".join(context_parts)

            response = self.invoke_llm_with_lore(self.get_prompt(), context, input_data.metadata.project_id)

            # Debug: Save response to file
            debug_response_file = f"output/debug_response_b{beat.beat_number}_attempt{attempt + 1}.txt"
            try:
                with open(debug_response_file, 'w', encoding='utf-8') as f:
                    f.write(f"Beat {beat.beat_number}, Attempt {attempt + 1}\n")
                    f.write("=" * 60 + "\n")
                    f.write(response)
                print(f"    [Saved response to {debug_response_file}]")
            except:
                pass  # Don't fail on debug save

            try:
                # Check if response is empty
                if not response or not response.strip():
                    raise ValueError(f"LLM returned empty response for beat {beat.beat_number}")

                # Extract JSON from response (handle preamble/postamble text)
                response_text = response.strip()

                # Try to find JSON object in response
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1

                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]

                    # Debug: Show extraction
                    if json_start > 0:
                        preamble = response_text[:json_start].strip()[:100]
                        print(f"    [Extracted JSON, removed preamble: '{preamble}...']")

                    try:
                        response_json = json.loads(json_str)
                    except json.JSONDecodeError as e:
                        # Try json_repair if available
                        if HAS_JSON_REPAIR:
                            print(f"    [JSON parsing failed, attempting repair...]")
                            repaired = repair_json(json_str)
                            response_json = json.loads(repaired)
                        else:
                            # Show what we tried to parse
                            print(f"    [JSON parsing error: {e}]")
                            print(f"    [First 500 chars of extracted JSON: {json_str[:500]}]")
                            raise
                else:
                    # Fallback: try parsing entire response
                    print(f"    [No JSON braces found, trying to parse entire response]")
                    response_json = json.loads(response_text)

                prose_content = response_json.get("full_prose", "")
                paragraphs_data = response_json.get("paragraphs", [])

                # Parse paragraphs
                paragraphs = []
                for para_data in paragraphs_data:
                    # Parse dialogue lines if present
                    dialogue_lines = []
                    for dl_data in para_data.get("dialogue_lines", []):
                        # Handle None values - skip non-dialogue text (messages, signs, etc.)
                        speaker = dl_data.get("speaker")
                        if speaker is None or speaker == "":
                            # This is likely a message, sign, or internal text, not spoken dialogue
                            # Skip it or use a placeholder
                            continue

                        dialogue_lines.append(DialogueLine(
                            speaker=speaker,
                            dialogue=dl_data.get("dialogue", ""),
                            action=dl_data.get("action"),
                            internal_thought=dl_data.get("internal_thought")
                        ))

                    paragraphs.append(Paragraph(
                        paragraph_number=para_data.get("paragraph_number", 0),
                        paragraph_type=para_data.get("paragraph_type", "narrative"),
                        content=para_data.get("content", ""),
                        dialogue_lines=dialogue_lines,
                        pov_character=para_data.get("pov_character"),
                        word_count=para_data.get("word_count", len(para_data.get("content", "").split()))
                    ))

                # Check word count
                actual_word_count = len(prose_content.split())
                last_word_count = actual_word_count  # Store for retry feedback

                # Word count validation with retry
                if min_words <= actual_word_count <= max_words:
                    # SUCCESS - within range
                    print(f"✓ Beat {beat.beat_number} prose: {actual_word_count} words (target: {min_words}-{max_words})")

                    # Create Prose object
                    beat.prose = Prose(
                        draft_version=1,
                        content=prose_content,
                        paragraphs=paragraphs,
                        word_count=actual_word_count,
                        generated_timestamp=datetime.now().isoformat(),
                        status="draft"
                    )

                    # Update word counts up the hierarchy
                    scene.actual_word_count = sum(
                        b.prose.word_count for b in scene.beats if b.prose
                    )
                    chapter.actual_word_count = sum(
                        s.actual_word_count for s in chapter.scenes
                    )
                    book.current_word_count = sum(
                        c.actual_word_count for c in book.chapters
                    )

                    input_data.metadata.last_updated = datetime.now()
                    input_data.metadata.last_updated_by = self.agent_name

                    # Success - break out of retry loop
                    break

                else:
                    # FAILED - out of range
                    if attempt < max_retries - 1:
                        # Retry
                        if actual_word_count < min_words:
                            print(f"⚠️  Beat {beat.beat_number}: {actual_word_count} words - TOO SHORT (min: {min_words}). Retrying ({attempt + 1}/{max_retries})...")
                        else:
                            print(f"⚠️  Beat {beat.beat_number}: {actual_word_count} words - TOO LONG (max: {max_words}). Retrying ({attempt + 1}/{max_retries})...")
                        continue  # Retry
                    else:
                        # Max retries reached - accept anyway with warning
                        print(f"⚠️  Beat {beat.beat_number}: {actual_word_count} words (target: {min_words}-{max_words}) - Max retries reached, accepting anyway")

                        # Create Prose object anyway
                        beat.prose = Prose(
                            draft_version=1,
                            content=prose_content,
                            paragraphs=paragraphs,
                            word_count=actual_word_count,
                            generated_timestamp=datetime.now().isoformat(),
                            status="draft"
                        )

                        # Update word counts up the hierarchy
                        scene.actual_word_count = sum(
                            b.prose.word_count for b in scene.beats if b.prose
                        )
                        chapter.actual_word_count = sum(
                            s.actual_word_count for s in chapter.scenes
                        )
                        book.current_word_count = sum(
                            c.actual_word_count for c in book.chapters
                        )

                        input_data.metadata.last_updated = datetime.now()
                        input_data.metadata.last_updated_by = self.agent_name
                        break

            except Exception as e:
                # On error, try next attempt or raise
                if attempt < max_retries - 1:
                    print(f"⚠️  Beat {beat.beat_number}: Error during generation - {e}. Retrying...")
                    continue
                else:
                    raise ValueError(f"ProseGenerator failed after {max_retries} attempts: {e}\nResponse: {response}")

        return input_data
