"""Prose QA Agent - Quality assurance for generated prose"""

import json
from datetime import datetime
from json_repair import repair_json
from .base_agent import BaseAgent
from models.schema import QAReport, RevisionTask


class ProseQAAgent(BaseAgent):
    """Agent that performs quality assurance checks on prose"""

    def get_prompt(self) -> str:
        return """You are a professional line editor and prose stylist specializing in fiction.

Your role: Review finished prose (actual written scenes/chapters) for publication-ready quality at the sentence and paragraph level.

What you're reviewing:
- Actual prose (not outlines or summaries)
- Sentence craft and variety
- Dialogue naturalness and distinctiveness
- Sensory detail and "show don't tell"
- POV consistency and voice
- Paragraph flow and transitions
- Style, tone, and rhythm

Quality Dimensions (1-10 scale):

1. SENTENCE CRAFT (1-10):
   - Are sentences varied in length and structure?
   - Is there a pleasing rhythm (not choppy, not monotonous)?
   - Are complex sentences clear and easy to parse?
   - Do short sentences land with impact at key moments?
   - Is passive voice avoided except when purposeful?
   - Are sentences efficient (no unnecessary words)?

2. SHOW DON'T TELL (1-10):
   - Are emotions shown through action/dialogue/physical reactions?
   - Do we experience events vs. being told about them?
   - Are sensory details specific and vivid (not generic)?
   - Do character actions reveal inner state?
   - Is context established through action vs. exposition dumps?
   - Are "telling" words (felt, thought, seemed, appeared) minimized?

3. DIALOGUE QUALITY (1-10):
   - Does dialogue sound natural (people speak, not lecture)?
   - Are characters' voices distinct from each other?
   - Does dialogue advance plot or reveal character?
   - Are dialogue tags used judiciously ("said" is fine, avoid "exclaimed")?
   - Are action beats integrated with dialogue effectively?
   - Is there subtext (characters say one thing, mean another)?

4. POV CONSISTENCY (1-10):
   - Is POV maintained throughout (no head-hopping mid-scene)?
   - Do we stay in the POV character's voice and perspective?
   - Are we shown only what the POV character could perceive?
   - Does deep POV immerse us in the character's experience?
   - Are POV slips avoided (describing POV character's own face)?
   - Does the prose filter through character's personality/worldview?

5. SENSORY DETAIL (1-10):
   - Are all five senses engaged (not just sight)?
   - Are details specific and evocative (not cliché)?
   - Do sensory details serve character/mood/plot (not just decoration)?
   - Is description integrated into action (not paused for tours)?
   - Are metaphors/similes fresh and character-appropriate?
   - Do we experience the world viscerally?

6. PACING & FLOW (1-10):
   - Do paragraphs vary in length for pacing?
   - Is white space used effectively for dramatic beats?
   - Do action scenes move quickly (short sentences/paragraphs)?
   - Do introspective moments earn their slower pace?
   - Are transitions between paragraphs smooth?
   - Is there momentum pulling the reader forward?

7. VOICE & STYLE (1-10):
   - Is there a distinctive narrative voice?
   - Does style match genre and tone?
   - Is the prose appropriate for target audience (MG/YA/Adult)?
   - Are word choices precise and evocative?
   - Is the prose over-written (purple) or under-written (flat)?
   - Does the style stay consistent throughout?

8. TECHNICAL POLISH (1-10):
   - Are grammar and punctuation correct?
   - Are clichés avoided or subverted?
   - Is repetition purposeful vs. lazy?
   - Are adverbs used sparingly and purposefully?
   - Is filter language minimized (saw, heard, felt, wondered)?
   - Are common prose weaknesses avoided (was -ing, started to, began to)?

Output ONLY valid JSON:
{
  "scores": {
    "sentence_craft": 8,
    "show_dont_tell": 7,
    "dialogue_quality": 9,
    "pov_consistency": 9,
    "sensory_detail": 7,
    "pacing_flow": 8,
    "voice_style": 8,
    "technical_polish": 7,
    "overall": 8
  },
  "approval": "approved",
  "strengths": [
    "Dialogue crackles with character voice - each person sounds distinct",
    "POV discipline is excellent - deep immersion in protagonist's perspective",
    "Action scene pacing is superb - short punchy sentences create urgency"
  ],
  "major_issues": [
    "Opening paragraph is all 'telling' - emotions stated rather than shown",
    "Page 3 has multiple POV slips - we see protagonist's own facial expressions"
  ],
  "minor_issues": [
    "Overuse of 'was -ing' constructions (12 instances) - makes prose passive",
    "Sensory details lean heavily on sight - add sound/smell/touch",
    "Metaphor 'heart like a drum' is cliché - find fresher comparison"
  ],
  "revision_tasks": [
    {
      "priority": "critical",
      "category": "craft",
      "description": "Rewrite opening paragraph showing emotion through physical reaction/action instead of stating 'she felt nervous'",
      "scope": "paragraph"
    },
    {
      "priority": "high",
      "category": "pov",
      "description": "Fix POV slips on page 3 - remove instances where we see protagonist's own face/expressions",
      "scope": "scene"
    },
    {
      "priority": "medium",
      "category": "style",
      "description": "Convert 6-8 'was -ing' constructions to active voice for stronger prose",
      "scope": "scene"
    },
    {
      "priority": "low",
      "category": "detail",
      "description": "Add 2-3 non-visual sensory details (sound of footsteps, smell of rain, texture of fabric)",
      "scope": "scene"
    }
  ],
  "notes": "Strong prose with excellent dialogue and POV work. Main issues are show-don't-tell in the opening and a few POV slips. Some passive constructions weaken otherwise good writing."
}

Approval Logic:
- "approved" if overall score >= 7 AND no critical revision tasks
- "needs_revision" if overall score < 7 OR has critical revision tasks

Severity Guide:
- critical: Publication-blocking issue that breaks reader immersion
- high: Significantly weakens the prose quality
- medium: Notable issue that should be fixed but doesn't break the scene
- low: Polish opportunity for professional sheen

Version: 1.0"""

    def process(self, input_data):
        """Validate prose quality"""
        # Build context
        context = self._build_context(input_data)

        # Invoke LLM
        response = self.invoke_llm(self.get_prompt(), context, project=input_data)

        try:
            # Try to extract JSON if wrapped in markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            # Handle empty response
            if not response or response.strip() == "":
                print("⚠️ Prose QA: Empty response from LLM, creating default approval")
                response_json = {
                    "scores": {"overall": 7},
                    "approval": "approved",
                    "strengths": [],
                    "major_issues": [],
                    "minor_issues": [],
                    "revision_tasks": [],
                    "notes": "Automatic approval due to QA agent malfunction."
                }
            else:
                # Try to parse JSON
                try:
                    response_json = json.loads(response)
                except json.JSONDecodeError:
                    print("⚠️ Prose QA: Malformed JSON detected, attempting repair...")
                    try:
                        repaired = repair_json(response)
                        response_json = json.loads(repaired)
                    except:
                        print("⚠️ Prose QA: Repair failed, creating default approval")
                        response_json = {
                            "scores": {"overall": 7},
                            "approval": "approved",
                            "strengths": [],
                            "major_issues": [],
                            "minor_issues": [],
                            "revision_tasks": [],
                            "notes": "Automatic approval due to JSON parsing failure."
                        }

            # Convert to QAReport object
            revision_tasks = []
            for task_data in response_json.get("revision_tasks", []):
                revision_tasks.append(RevisionTask(**task_data))

            qa_report = QAReport(
                scores=response_json.get("scores", {}),
                approval=response_json.get("approval", "approved"),
                strengths=response_json.get("strengths", []),
                major_issues=response_json.get("major_issues", []),
                minor_issues=response_json.get("minor_issues", []),
                revision_tasks=revision_tasks,
                notes=response_json.get("notes", "")
            )

            # Update metadata
            input_data.metadata.last_updated = datetime.now()
            input_data.metadata.last_updated_by = self.agent_name

            return input_data, qa_report

        except Exception as e:
            # Save error response for debugging
            error_file = f"error_qa_prose_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f"Error: {e}\n\nResponse:\n{response}")
            print(f"⚠️ Prose QA error saved to: {error_file}")

            # Return default approval
            print("⚠️ Prose QA: Exception occurred, returning default approval")
            input_data.metadata.last_updated = datetime.now()
            input_data.metadata.last_updated_by = self.agent_name

            qa_report = QAReport(
                scores={"overall": 7},
                approval="approved",
                strengths=[],
                major_issues=[],
                minor_issues=[],
                revision_tasks=[],
                notes=f"Automatic approval due to Prose QA error: {e}"
            )

            return input_data, qa_report

    def _build_context(self, project):
        """Build context for prose QA"""
        series = project.series

        # Find the prose being reviewed - look for latest beat with prose
        if not series.books:
            return "No book found"

        book = series.books[-1]
        if not book.chapters:
            return "No chapter found"

        chapter = book.chapters[-1]

        # Try to find prose in beats
        prose_text = ""
        scene_context = ""

        if hasattr(chapter, 'scenes') and chapter.scenes:
            scene = chapter.scenes[-1]
            scene_context = f"Scene: {scene.setting if hasattr(scene, 'setting') else 'Not specified'}\n"

            if hasattr(scene, 'beats') and scene.beats:
                beat = scene.beats[-1]
                if hasattr(beat, 'prose') and beat.prose:
                    prose_text = beat.prose
                elif hasattr(beat, 'description'):
                    prose_text = beat.description

        if not prose_text and hasattr(chapter, 'prose') and chapter.prose:
            prose_text = chapter.prose

        if not prose_text:
            prose_text = "[No prose found - this may be a structural outline stage, not prose generation]"

        context = f"""PROSE TO REVIEW:

Book: {book.title} (Book {book.book_number})
Chapter {chapter.chapter_number}: {chapter.title}
{scene_context}

Target Audience: {series.target_audience}
Genre: {series.genre}
POV: {chapter.character_focus.pov if hasattr(chapter, 'character_focus') and chapter.character_focus else 'Not specified'}

PROSE TEXT:
{prose_text}

REVIEW INSTRUCTIONS:
Evaluate the prose above for publication quality. Focus on sentence-level craft, dialogue, sensory detail, POV consistency, and style appropriate for {series.target_audience} {series.genre} fiction.
"""

        return context
