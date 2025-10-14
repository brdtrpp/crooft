"""Scene Developer Agent - Expands scenes into beats"""

import json
from datetime import datetime
from .base_agent import BaseAgent
from models.schema import Beat


class SceneDeveloperAgent(BaseAgent):
    """Agent that expands a single scene into beats"""

    def get_prompt(self) -> str:
        return """You are a professional scene developer.

Create 5-10 story beats for this scene. Each beat is a small unit of action/dialogue/description.

Output ONLY valid JSON:
{
  "beats": [
    {
      "beat_number": 1,
      "description": "What happens in this beat",
      "emotional_tone": "The emotional quality",
      "character_actions": ["action1", "action2"],
      "dialogue_summary": "Key dialogue points"
    }
  ]
}

Version: 1.0"""

    def process(self, input_data):
        """Required by base class - not used"""
        return input_data

    def process_scene(self, input_data, book_idx: int, chapter_idx: int, scene_idx: int):
        """Expand a specific scene into beats"""
        scene = input_data.series.books[book_idx].chapters[chapter_idx].scenes[scene_idx]

        context = f"""Scene {scene.scene_number}: {scene.title}
Purpose: {scene.purpose}
Type: {scene.scene_type}
POV: {scene.pov}
Setting: {scene.setting.location}
Characters: {', '.join(scene.characters_present)}
Conflicts: {', '.join([c.description for c in scene.conflicts])}

Create 5-10 beats that accomplish the scene's purpose."""

        # Invoke LLM with retry logic for beat count
        min_beats = 5
        max_beats = 10
        max_retries = 3

        for attempt in range(max_retries):
            if attempt == 0:
                response = self.invoke_llm_with_lore(self.get_prompt(), context, input_data.metadata.project_id)
            else:
                retry_prompt = f"""
CRITICAL ERROR IN PREVIOUS ATTEMPT:
You generated {len(response_json.get('beats', []))} beats but MUST generate between {min_beats} and {max_beats} beats.

REQUIREMENT: Generate between {min_beats}-{max_beats} beats for Scene {scene.scene_number}.

Generate the COMPLETE JSON with the appropriate number of beats within the allowed range.
"""
                print(f"⚠️  Retry {attempt}/{max_retries}: Requesting {min_beats}-{max_beats} beats...")
                response = self.invoke_llm_with_lore(self.get_prompt() + retry_prompt, context, input_data.metadata.project_id)

            # Quick validation check
            try:
                # Check for empty response
                if not response or response.strip() == "":
                    print(f"⚠️  Empty response on attempt {attempt + 1}")
                    if attempt == max_retries - 1:
                        error_file = f"error_scenedev_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                        with open(error_file, 'w', encoding='utf-8') as f:
                            f.write(f"Empty response from LLM after {max_retries} attempts\nContext: {context}")
                        raise ValueError(f"SceneDeveloper returned empty response after {max_retries} attempts. Context saved to: {error_file}")
                    continue  # Try again

                # Try to parse JSON
                test_text = response
                if "```json" in test_text:
                    test_text = test_text.split("```json")[1].split("```")[0].strip()
                elif "```" in test_text:
                    test_text = test_text.split("```")[1].split("```")[0].strip()

                test_json = json.loads(test_text)
                beat_count = len(test_json.get('beats', []))

                if min_beats <= beat_count <= max_beats:
                    print(f"✓ LLM generated correct number of beats ({beat_count}, range: {min_beats}-{max_beats})")
                    break
                else:
                    print(f"⚠️  LLM generated {beat_count} beats (out of range {min_beats}-{max_beats}) on attempt {attempt + 1}")
                    response_json = test_json  # Save for retry message
                    if attempt == max_retries - 1:
                        print(f"❌ Failed after {max_retries} attempts")
            except Exception as e:
                print(f"⚠️  Parsing error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    # Save error for debugging
                    error_file = f"error_scenedev_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    with open(error_file, 'w', encoding='utf-8') as f:
                        f.write(f"Error: {e}\n\nResponse:\n{response}\n\nContext:\n{context}")
                    raise ValueError(f"SceneDeveloper parsing failed after {max_retries} attempts: {e}. Saved to: {error_file}")
                continue  # Try again

        try:
            # Handle empty response
            if not response or response.strip() == "":
                error_file = f"error_scenedev_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(error_file, 'w', encoding='utf-8') as f:
                    f.write(f"Empty response from LLM\nContext: {context}")
                raise ValueError(f"SceneDeveloper returned empty response. Context saved to: {error_file}")

            # Try to extract JSON if wrapped in markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            try:
                response_json = json.loads(response)
            except json.JSONDecodeError:
                print("⚠️ Malformed JSON detected, attempting repair...")
                from json_repair import repair_json
                repaired = repair_json(response)
                response_json = json.loads(repaired)

            if "beats" in response_json:
                beats_data = response_json["beats"]

                # VALIDATION: Beat count must be within acceptable range (5-10)
                min_beats = 5
                max_beats = 10
                num_beats = len(beats_data)

                if not (min_beats <= num_beats <= max_beats):
                    raise ValueError(
                        f"Scene Developer FAILED validation: Generated {num_beats} beats for Scene {scene.scene_number}, "
                        f"but must be within range [{min_beats}-{max_beats}] beats. "
                        f"The LLM must respect beat count constraints."
                    )
                print(f"✓ Validation passed: {num_beats} beats for Scene {scene.scene_number} (range: {min_beats}-{max_beats})")

                # Clean beat data - handle None values
                for beat_data in beats_data:
                    if beat_data.get('dialogue_summary') is None:
                        beat_data['dialogue_summary'] = ""
                    if beat_data.get('character_actions') is None:
                        beat_data['character_actions'] = []

                scene.beats = [Beat(**beat_data) for beat_data in beats_data]
                for beat in scene.beats:
                    beat.prose = None  # Will be filled by ProseGenerator

            input_data.metadata.last_updated = datetime.now()
            input_data.metadata.last_updated_by = self.agent_name

        except json.JSONDecodeError as e:
            raise ValueError(f"SceneDeveloper returned invalid JSON: {e}")
        except Exception as e:
            raise ValueError(f"SceneDeveloper failed: {e}")

        return input_data
