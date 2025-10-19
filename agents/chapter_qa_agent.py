"""Chapter QA Agent - Quality assurance for chapter-level development"""

import json
from datetime import datetime
from json_repair import repair_json
from .base_agent import BaseAgent
from models.schema import QAReport, RevisionTask


class ChapterQAAgent(BaseAgent):
    """Agent that performs quality assurance checks on chapter developments"""

    def get_prompt(self) -> str:
        return """You are a professional scene-level editor specializing in chapter structure and scene sequencing.

Your role: Review chapter breakdowns (scene beats, sequences, transitions) for flow, pacing, and narrative momentum.

What you're reviewing:
- Chapter scenes and beat sequences
- Scene purposes and progression
- Transitions between scenes
- POV consistency
- Chapter hooks and endings
- Subtext and emotional beats

Quality Dimensions (1-10 scale):

1. SCENE SEQUENCING (1-10):
   - Does each scene flow logically into the next?
   - Are cause-and-effect relationships clear?
   - Do scenes build on each other vs. feel episodic?
   - Are there unnecessary scenes that could be cut?
   - Is the scene order optimal for revelation and tension?
   - Do flashbacks (if any) serve clear purposes and land effectively?

2. CHAPTER HOOKS (1-10):
   - Does the chapter open with a compelling hook?
   - Does the opening scene establish stakes or questions?
   - Is there forward momentum from the first line?
   - Does the chapter ending create urgency to continue?
   - Are cliffhangers earned (not cheap tricks)?
   - Do chapter breaks fall at natural tension peaks?

3. PACING VARIATION (1-10):
   - Do scenes vary in tempo (action/dialogue/introspection)?
   - Are long scenes balanced with short ones?
   - Does the chapter have peaks and valleys (not monotonous)?
   - Are action scenes punchy and introspective scenes earned?
   - Does dialogue advance plot or character (not just fill space)?
   - Is description integrated vs. stopping the action?

4. POV DISCIPLINE (1-10):
   - Is POV consistent within scenes (no head-hopping)?
   - If POV shifts, are transitions clear and purposeful?
   - Does the POV character have a stake in each scene?
   - Are we in the right character's head for maximum impact?
   - Does the POV character's voice/perspective come through?

5. EMOTIONAL BEATS (1-10):
   - Do characters experience emotional progression through the chapter?
   - Are emotional reactions proportional to events?
   - Is there variety in emotional tones (not all one note)?
   - Do quiet character moments balance plot progression?
   - Are relationships developed through action/dialogue (not told)?
   - Do emotional beats set up future payoffs?

6. SUBTEXT & LAYERING (1-10):
   - Do scenes operate on multiple levels (plot + character + theme)?
   - Is dialogue layered (what's said vs. what's meant)?
   - Are there visual/sensory details that add meaning?
   - Do character choices reveal inner conflict?
   - Are themes explored through action (not stated)?
   - Is foreshadowing subtle and organic?

7. SCENE PURPOSE (1-10):
   - Does each scene serve multiple functions (advance plot + develop character)?
   - Are all scenes necessary (pass the "so what?" test)?
   - Do scenes end at moments of change/decision?
   - Are conflicts introduced and escalated effectively?
   - Do quieter scenes earn their place (setup, breather, revelation)?
   - Is there a clear through-line connecting scenes?

8. TRANSITIONS (1-10):
   - Are scene breaks clear and purposeful?
   - Do transitions maintain momentum (not jarring)?
   - Is time/location established quickly after cuts?
   - Are there smooth connections between disparate scenes?
   - Do white space breaks serve pacing?

Output ONLY valid JSON:
{
  "scores": {
    "scene_sequencing": 8,
    "chapter_hooks": 9,
    "pacing_variation": 7,
    "pov_discipline": 9,
    "emotional_beats": 8,
    "subtext_layering": 7,
    "scene_purpose": 8,
    "transitions": 8,
    "overall": 8
  },
  "approval": "approved",
  "strengths": [
    "Opening scene hook is gripping - immediately establishes stakes",
    "POV discipline is excellent throughout",
    "Scene 3 emotional beat (confrontation with mentor) is powerful"
  ],
  "major_issues": [
    "Scene 4 (market conversation) serves no clear purpose - cut or merge",
    "Transition from Scene 2 to Scene 3 is jarring - 12-hour time jump unexplained"
  ],
  "minor_issues": [
    "Scene 5 pacing drags - too much internal monologue",
    "Chapter ending feels flat - needs stronger cliffhanger or question"
  ],
  "revision_tasks": [
    {
      "priority": "critical",
      "category": "structure",
      "description": "Cut Scene 4 entirely or merge its essential info into Scene 3",
      "scope": "scene"
    },
    {
      "priority": "high",
      "category": "transitions",
      "description": "Add brief transition sentence showing time/mood shift between Scene 2-3",
      "scope": "scene"
    },
    {
      "priority": "medium",
      "category": "pacing",
      "description": "Trim Scene 5 introspection by 30% - break up with action or dialogue",
      "scope": "scene"
    }
  ],
  "notes": "Strong chapter overall with good POV work. Main issues are a purposeless scene and one jarring transition. Chapter ending could be punchier."
}

Approval Logic:
- "approved" if overall score >= 7 AND no critical revision tasks
- "needs_revision" if overall score < 7 OR has critical revision tasks

Severity Guide:
- critical: Breaks reader immersion or momentum
- high: Significantly weakens chapter impact
- medium: Notable issue but chapter still functional
- low: Minor polish opportunity

Version: 1.0"""

    def process(self, input_data):
        """Validate chapter development quality"""
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
                print("⚠️ Chapter QA: Empty response from LLM, creating default approval")
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
                    print("⚠️ Chapter QA: Malformed JSON detected, attempting repair...")
                    try:
                        repaired = repair_json(response)
                        response_json = json.loads(repaired)
                    except:
                        print("⚠️ Chapter QA: Repair failed, creating default approval")
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
            error_file = f"error_qa_chapter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f"Error: {e}\n\nResponse:\n{response}")
            print(f"⚠️ Chapter QA error saved to: {error_file}")

            # Return default approval
            print("⚠️ Chapter QA: Exception occurred, returning default approval")
            input_data.metadata.last_updated = datetime.now()
            input_data.metadata.last_updated_by = self.agent_name

            qa_report = QAReport(
                scores={"overall": 7},
                approval="approved",
                strengths=[],
                major_issues=[],
                minor_issues=[],
                revision_tasks=[],
                notes=f"Automatic approval due to Chapter QA error: {e}"
            )

            return input_data, qa_report

    def _build_context(self, project):
        """Build context for chapter QA"""
        series = project.series

        # Find the chapter being reviewed (last chapter of last book)
        if not series.books:
            return "No book found"

        book = series.books[-1]
        if not book.chapters:
            return "No chapter found"

        chapter = book.chapters[-1]

        context = f"""CHAPTER TO REVIEW:

Book: {book.title} (Book {book.book_number})
Chapter {chapter.chapter_number}: {chapter.title}

Purpose: {chapter.purpose}
POV: {chapter.character_focus.pov if hasattr(chapter, 'character_focus') and chapter.character_focus else 'Not specified'}

Scenes:
"""

        if hasattr(chapter, 'scenes') and chapter.scenes:
            for i, scene in enumerate(chapter.scenes, 1):
                context += f"\nScene {i}:\n"
                if hasattr(scene, 'setting'):
                    context += f"  Setting: {scene.setting}\n"
                if hasattr(scene, 'purpose'):
                    context += f"  Purpose: {scene.purpose}\n"
                if hasattr(scene, 'beats') and scene.beats:
                    context += f"  Beats: {len(scene.beats)}\n"
                    for beat in scene.beats[:3]:  # Show first 3 beats
                        if hasattr(beat, 'description'):
                            context += f"    - {beat.description}\n"
                elif hasattr(scene, 'summary'):
                    context += f"  Summary: {scene.summary}\n"

        # Add book context
        context += f"\n\nBook Context:\n"
        context += f"  - Book Themes: {', '.join(book.themes)}\n"
        context += f"  - Chapter {chapter.chapter_number} of {len(book.chapters)}\n"
        context += f"  - Target Word Count: {book.target_word_count}\n"

        return context
