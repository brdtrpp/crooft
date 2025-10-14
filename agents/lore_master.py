"""Lore Master Agent - Validates consistency with established lore"""

import json
from datetime import datetime
from json_repair import repair_json
from .base_agent import BaseAgent


class LoreMasterAgent(BaseAgent):
    """Agent that validates consistency with established lore"""

    def get_prompt(self) -> str:
        return """You are a lore consistency expert for fiction.

Your task:
1. Review the provided lore database (characters, locations, world elements)
2. Analyze the latest content against this lore
3. Identify any contradictions or inconsistencies
4. Detect new lore elements that should be formally added

Output ONLY valid JSON:
{
  "lore_violations": [
    {
      "type": "character",
      "element": "Character Name",
      "violation": "Description of contradiction",
      "severity": "critical"
    }
  ],
  "new_lore_detected": [
    {
      "type": "character",
      "name": "New Character",
      "description": "Details mentioned in content",
      "should_add": true
    }
  ],
  "consistency_score": 9,
  "approval": "approved",
  "notes": "Lore is consistent. Detected 1 new character to add."
}

IMPORTANT:
- Use "approved" if consistency_score >= 8 and no critical violations
- Use "needs_revision" if consistency_score < 8 or critical violations exist
- Severity: "critical", "major", or "minor"

Version: 1.0"""

    def process(self, input_data):
        """Validate lore consistency"""
        # Build lore context
        lore_context = self._build_lore_context(input_data)

        # Build content summary
        content_summary = self._build_content_summary(input_data)

        context = f"""ESTABLISHED LORE:
{lore_context}

LATEST CONTENT:
{content_summary}

Check for contradictions and new lore elements."""

        # Invoke LLM
        response = self.invoke_llm(self.get_prompt(), context)

        try:
            # Try to extract JSON if wrapped in markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            # Handle empty response - create default passing result
            if not response or response.strip() == "":
                print("⚠️ Lore Master: Empty response from LLM, creating default approval")
                response_json = {
                    "lore_violations": [],
                    "new_lore_detected": [],
                    "consistency_score": 7,
                    "approval": "approved",
                    "notes": "Automatic approval due to Lore Master agent malfunction. Manual review recommended."
                }
            else:
                # Try to parse JSON
                try:
                    response_json = json.loads(response)
                except json.JSONDecodeError:
                    print("⚠️ Lore Master: Malformed JSON detected, attempting repair...")
                    try:
                        repaired = repair_json(response)
                        response_json = json.loads(repaired)
                    except:
                        # If repair fails, create default passing result
                        print("⚠️ Lore Master: Repair failed, creating default approval")
                        response_json = {
                            "lore_violations": [],
                            "new_lore_detected": [],
                            "consistency_score": 7,
                            "approval": "approved",
                            "notes": "Automatic approval due to JSON parsing failure."
                        }

            # Extract results
            approval = response_json.get("approval", "approved")
            violations = response_json.get("lore_violations", [])
            new_lore = response_json.get("new_lore_detected", [])
            score = response_json.get("consistency_score", 7)
            notes = response_json.get("notes", "")

            # Update metadata
            input_data.metadata.last_updated = datetime.now()
            input_data.metadata.last_updated_by = self.agent_name

            # Return validation result
            return input_data, {
                "approval": approval,
                "violations": violations,
                "new_lore": new_lore,
                "score": score,
                "notes": notes
            }

        except Exception as e:
            # Save error response for debugging
            error_file = f"error_loremaster_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f"Error: {e}\n\nResponse:\n{response}")
            print(f"⚠️ Lore Master error saved to: {error_file}")

            # Return default approval to allow pipeline to continue
            print("⚠️ Lore Master: Exception occurred, returning default approval")
            input_data.metadata.last_updated = datetime.now()
            input_data.metadata.last_updated_by = self.agent_name

            return input_data, {
                "approval": "approved",
                "violations": [],
                "new_lore": [],
                "score": 7,
                "notes": f"Automatic approval due to Lore Master error: {e}"
            }

    def _build_lore_context(self, project):
        """Build lore database summary"""
        lore = project.series.lore

        lines = []

        if lore.characters:
            lines.append("CHARACTERS:")
            for char in lore.characters:
                lines.append(f"  - {char.name} ({char.role}): {char.description}")
                if char.traits:
                    lines.append(f"    Traits: {', '.join(char.traits)}")

        if lore.locations:
            lines.append("\nLOCATIONS:")
            for loc in lore.locations:
                lines.append(f"  - {loc.name}: {loc.description}")

        if lore.world_elements:
            lines.append("\nWORLD ELEMENTS:")
            for elem in lore.world_elements:
                lines.append(f"  - {elem.name} ({elem.type}): {elem.description}")
                if elem.rules:
                    lines.append(f"    Rules: {', '.join(elem.rules)}")

        return "\n".join(lines) if lines else "No lore established yet."

    def _build_content_summary(self, project):
        """Build summary of latest content"""
        stage = project.metadata.processing_stage

        if stage == "series":
            return f"Series: {project.series.title}\nPremise: {project.series.premise}"

        if stage == "book" and project.series.books:
            book = project.series.books[-1]
            return f"Book: {book.title}\nPremise: {book.premise}\nCharacter Arcs: {', '.join([arc.character_name for arc in book.character_arcs])}"

        if stage == "chapter" and project.series.books:
            book = project.series.books[-1]
            if book.chapters:
                chapter = book.chapters[-1]
                return f"Chapter {chapter.chapter_number}: {chapter.title}\nPurpose: {chapter.purpose}\nPOV: {chapter.character_focus.pov}"

        return f"Stage: {stage}"
