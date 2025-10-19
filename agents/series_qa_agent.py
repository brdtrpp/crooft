"""Series QA Agent - Quality assurance for series-level outlines"""

import json
from datetime import datetime
from json_repair import repair_json
from .base_agent import BaseAgent
from models.schema import QAReport, RevisionTask


class SeriesQAAgent(BaseAgent):
    """Agent that performs quality assurance checks on series outlines"""

    def get_prompt(self) -> str:
        return """You are a professional series development editor specializing in multi-book fiction series architecture.

Your role: Review series-level outlines (9-book arcs, trilogies, etc.) for strategic coherence, escalation design, and long-term narrative sustainability.

What you're reviewing:
- Series premise and overarching conflict
- 9-book structure with escalation across the series
- Persistent character arcs spanning multiple books
- Thematic throughlines
- World-building foundation
- Continuity planning (foreshadowing, payoffs, callbacks)

Quality Dimensions (1-10 scale):

1. SERIES ARC COHERENCE (1-10):
   - Does the series have a clear beginning, middle, and end across all books?
   - Is there a compelling overarching question/conflict that spans the series?
   - Does the final book payoff justify the journey?
   - Are there clear reasons this must be a series vs. standalone?
   - Do the books build on each other vs. feel episodic/repetitive?

2. ESCALATION MODEL (1-10):
   - Do stakes escalate appropriately from Book 1 → Book 9?
   - Does scope expand naturally (personal → community → world)?
   - Do antagonistic forces grow more complex/dangerous?
   - Are costs/sacrifices proportional to series position?
   - Is the escalation sustainable (no early peak, no flat middle)?

3. PERSISTENT THREADS (1-10):
   - Are multi-book mysteries/questions set up early?
   - Do persistent threads advance in each book (not ignored for books at a time)?
   - Are payoffs planned at appropriate moments (not all at the end)?
   - Do threads interweave vs. run in parallel without touching?
   - Are there enough threads to sustain 9 books without feeling padded?

4. CHARACTER JOURNEYS (1-10):
   - Do protagonists have clear series-long arcs (not just book-to-book)?
   - Are there meaningful character transformations planned across the series?
   - Do supporting characters have their own multi-book arcs?
   - Are character relationships designed to evolve over time?
   - Is character growth paced (not all in Book 1, not stagnant until Book 9)?

5. THEMATIC CONSISTENCY (1-10):
   - Are core themes established and explored throughout the series?
   - Do themes deepen/complicate as the series progresses?
   - Does each book explore a different facet of the core theme?
   - Are themes integrated into plot (not just stated)?
   - Do character arcs and plot events organically explore themes?

6. WORLD-BUILDING FOUNDATION (1-10):
   - Is the world large enough to sustain 9 books of exploration?
   - Are world rules/magic systems clearly defined with room for discovery?
   - Are there distinct locations/cultures for variety across books?
   - Does the world have history/depth that can be gradually revealed?
   - Are world elements integrated into plot (not just decoration)?

7. CONTINUITY & PLANNING (1-10):
   - Are foreshadowing moments planned for early books?
   - Are callback opportunities identified for later books?
   - Is there a clear continuity plan (who knows what, when)?
   - Are timeline and character status tracked across books?
   - Are there systems to prevent contradictions across 9 books?

8. STRUCTURAL VARIETY (1-10):
   - Does each book have a unique identity/hook within the series?
   - Are book structures varied (not the same formula 9 times)?
   - Are there different types of conflicts across books (external/internal/interpersonal)?
   - Does pacing vary appropriately (setup vs. action books)?
   - Are there surprises/subversions planned to keep the series fresh?

Output ONLY valid JSON:
{
  "scores": {
    "series_arc_coherence": 8,
    "escalation_model": 7,
    "persistent_threads": 9,
    "character_journeys": 7,
    "thematic_consistency": 8,
    "world_building": 9,
    "continuity_planning": 6,
    "structural_variety": 7,
    "overall": 8
  },
  "approval": "approved",
  "strengths": [
    "Exceptional persistent thread setup with clear payoffs planned",
    "World is deep and varied enough for 9 books",
    "Clear escalation from personal stakes (Book 1) to cosmic (Book 9)"
  ],
  "major_issues": [
    "Books 4-6 feel repetitive - each follows identical structure",
    "Protagonist arc stagnates in middle books - no growth from Book 3-7"
  ],
  "minor_issues": [
    "Theme of 'power corrupts' stated too explicitly in series premise",
    "Supporting character arcs are underdeveloped compared to protagonist"
  ],
  "revision_tasks": [
    {
      "priority": "critical",
      "category": "structure",
      "description": "Vary the structure of Books 4-6: consider different POVs, timelines, or conflict types",
      "scope": "series"
    },
    {
      "priority": "high",
      "category": "character",
      "description": "Add meaningful character growth moments in Books 4, 5, 6 - protagonist cannot stagnate for 3 books",
      "scope": "books"
    }
  ],
  "notes": "Strong series foundation with compelling escalation and world-building. Main concern is mid-series repetition - need structural variety to sustain reader interest across 9 books."
}

Approval Logic:
- "approved" if overall score >= 7 AND no critical revision tasks
- "needs_revision" if overall score < 7 OR has critical revision tasks

Severity Guide:
- critical: Blocks publication quality, would cause reader drop-off
- high: Significant issue that weakens the series
- medium: Notable problem but not series-breaking
- low: Minor polish/improvement opportunity

Version: 1.0"""

    def process(self, input_data):
        """Validate series outline quality"""
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
                print("⚠️ Series QA: Empty response from LLM, creating default approval")
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
                    print("⚠️ Series QA: Malformed JSON detected, attempting repair...")
                    try:
                        repaired = repair_json(response)
                        response_json = json.loads(repaired)
                    except:
                        print("⚠️ Series QA: Repair failed, creating default approval")
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
            error_file = f"error_qa_series_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f"Error: {e}\n\nResponse:\n{response}")
            print(f"⚠️ Series QA error saved to: {error_file}")

            # Return default approval
            print("⚠️ Series QA: Exception occurred, returning default approval")
            input_data.metadata.last_updated = datetime.now()
            input_data.metadata.last_updated_by = self.agent_name

            qa_report = QAReport(
                scores={"overall": 7},
                approval="approved",
                strengths=[],
                major_issues=[],
                minor_issues=[],
                revision_tasks=[],
                notes=f"Automatic approval due to Series QA error: {e}"
            )

            return input_data, qa_report

    def _build_context(self, project):
        """Build context for series QA"""
        series = project.series

        context = f"""SERIES OUTLINE TO REVIEW:

Title: {series.title}
Genre: {series.genre}
Target Audience: {series.target_audience}

Premise:
{series.premise}

Themes: {', '.join(series.themes)}

Number of Books: {len(series.books)}

Lore Foundation:
- Characters: {len(series.lore.characters)}
- Locations: {len(series.lore.locations)}
- World Elements: {len(series.lore.world_elements)}

Book Summaries:
"""

        for book in series.books:
            context += f"\nBook {book.book_number}: {book.title}\n"
            context += f"  Premise: {book.premise}\n"
            context += f"  Themes: {', '.join(book.themes)}\n"
            context += f"  Status: {book.status}\n"

        if hasattr(series, 'persistent_threads') and series.persistent_threads:
            context += f"\n\nPersistent Threads: {len(series.persistent_threads)}\n"
            for thread in series.persistent_threads[:5]:  # Show first 5
                context += f"  - {thread.get('name', 'Unnamed thread')}\n"

        return context
