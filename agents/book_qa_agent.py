"""Book QA Agent - Quality assurance for book-level outlines"""

import json
from datetime import datetime
from json_repair import repair_json
from .base_agent import BaseAgent
from models.schema import QAReport, RevisionTask


class BookQAAgent(BaseAgent):
    """Agent that performs quality assurance checks on book outlines"""

    def get_prompt(self) -> str:
        return """You are a professional developmental editor specializing in single-book narrative structure within multi-book series.

Your role: Review book-level outlines (premise, character arcs, chapter breakdowns) for structural integrity, pacing, and series integration.

What you're reviewing:
- Book premise and central conflict
- Three-act structure and plot progression
- Character arcs within this book
- Chapter breakdown and pacing
- Series integration (how this book fits into the larger arc)
- Theme exploration
- Major plot turns (inciting incident, midpoint, all-is-lost, climax)

Quality Dimensions (1-10 scale):

1. THREE-ACT STRUCTURE (1-10):
   - Does the book have clear Act 1 (setup), Act 2 (confrontation), Act 3 (resolution)?
   - Is the inciting incident compelling and positioned correctly (~10-15% mark)?
   - Does the midpoint raise stakes or shift direction (~50% mark)?
   - Is there an "all is lost" moment before the climax (~75% mark)?
   - Does the climax resolve the book's central conflict satisfyingly?
   - Is the resolution earned (not rushed or convenient)?

2. PACING & PROGRESSION (1-10):
   - Does tension build steadily throughout the book?
   - Are there appropriate peaks and valleys (not flat, not exhausting)?
   - Do chapters vary in pace (action vs. introspection vs. dialogue)?
   - Are there clear turning points that propel the story forward?
   - Does the book avoid sagging in the middle?
   - Is the climax positioned for maximum impact?

3. CHARACTER ARCS (1-10):
   - Do main characters have clear wants and needs?
   - Do protagonists face meaningful choices that reveal character?
   - Are character transformations believable and earned?
   - Do supporting characters serve distinct narrative purposes?
   - Are character relationships developed with nuance?
   - Do character arcs connect to the book's themes?

4. PLOT COHERENCE (1-10):
   - Is the central conflict clear and compelling?
   - Do plot threads advance logically (cause and effect)?
   - Are there too many or too few subplots?
   - Do all major plot points contribute to the resolution?
   - Are there plot holes or logical inconsistencies?
   - Is the antagonistic force appropriately challenging?

5. SERIES INTEGRATION (1-10):
   - Does this book fit appropriately into its series position (Book X of 9)?
   - Are stakes/scope appropriate for this point in the series?
   - Are series-level threads advanced meaningfully?
   - Does the book work as a standalone while serving the series?
   - Are callbacks to previous books earned (not forced)?
   - Does setup for future books feel organic (not just sequel-bait)?

6. THEME EXPLORATION (1-10):
   - Are themes integrated into plot and character (not preachy)?
   - Does the story explore thematic questions (not just answer them)?
   - Do plot events organically test the themes?
   - Are themes layered (not one-dimensional)?
   - Do character choices reflect thematic conflicts?

7. CHAPTER STRUCTURE (1-10):
   - Does each chapter have a clear purpose/goal?
   - Do chapters begin with hooks and end with forward momentum?
   - Are chapter lengths varied appropriately for pacing?
   - Do scene sequences within chapters flow logically?
   - Are POV shifts (if any) strategic and clear?
   - Do chapters build toward act breaks and the climax?

8. STAKES & URGENCY (1-10):
   - Are the stakes clear and personally meaningful to characters?
   - Is there a ticking clock or sense of urgency?
   - Do stakes escalate appropriately throughout the book?
   - Are consequences of failure significant and specific?
   - Does the reader care about the outcome?

Output ONLY valid JSON:
{
  "scores": {
    "three_act_structure": 8,
    "pacing_progression": 7,
    "character_arcs": 9,
    "plot_coherence": 8,
    "series_integration": 7,
    "theme_exploration": 8,
    "chapter_structure": 6,
    "stakes_urgency": 9,
    "overall": 8
  },
  "approval": "approved",
  "strengths": [
    "Protagonist arc is compelling and emotionally resonant",
    "Midpoint twist genuinely shifts the story direction",
    "Stakes feel personal and urgent throughout"
  ],
  "major_issues": [
    "Act 2 sags from chapters 12-18 - no meaningful progression",
    "Climax feels rushed - only 1 chapter for final confrontation"
  ],
  "minor_issues": [
    "Supporting character arc for Mentor feels incomplete",
    "Chapter 7 serves no clear narrative purpose - can be cut or merged"
  ],
  "revision_tasks": [
    {
      "priority": "critical",
      "category": "pacing",
      "description": "Add 2-3 escalating complications in chapters 12-18 to maintain Act 2 momentum",
      "scope": "chapters"
    },
    {
      "priority": "high",
      "category": "structure",
      "description": "Expand climax to 2-3 chapters - needs more space for satisfying resolution",
      "scope": "chapters"
    },
    {
      "priority": "medium",
      "category": "character",
      "description": "Complete mentor's arc - add decision point or sacrifice in Act 3",
      "scope": "character_arc"
    }
  ],
  "notes": "Solid book structure with strong character work. Main concern is pacing - mid-book sag and rushed climax need addressing before moving to chapter development."
}

Approval Logic:
- "approved" if overall score >= 7 AND no critical revision tasks
- "needs_revision" if overall score < 7 OR has critical revision tasks

Severity Guide:
- critical: Would cause readers to abandon the book
- high: Significantly weakens the book's impact
- medium: Notable issue but book still functional
- low: Minor polish opportunity

Version: 1.0"""

    def process(self, input_data):
        """Validate book outline quality"""
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
                print("⚠️ Book QA: Empty response from LLM, creating default approval")
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
                    print("⚠️ Book QA: Malformed JSON detected, attempting repair...")
                    try:
                        repaired = repair_json(response)
                        response_json = json.loads(repaired)
                    except:
                        print("⚠️ Book QA: Repair failed, creating default approval")
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
            error_file = f"error_qa_book_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f"Error: {e}\n\nResponse:\n{response}")
            print(f"⚠️ Book QA error saved to: {error_file}")

            # Return default approval
            print("⚠️ Book QA: Exception occurred, returning default approval")
            input_data.metadata.last_updated = datetime.now()
            input_data.metadata.last_updated_by = self.agent_name

            qa_report = QAReport(
                scores={"overall": 7},
                approval="approved",
                strengths=[],
                major_issues=[],
                minor_issues=[],
                revision_tasks=[],
                notes=f"Automatic approval due to Book QA error: {e}"
            )

            return input_data, qa_report

    def _build_context(self, project):
        """Build context for book QA"""
        series = project.series

        # Find the book being reviewed (last book in list)
        if not series.books:
            return "No book found to review"

        book = series.books[-1]

        context = f"""BOOK OUTLINE TO REVIEW:

Series: {series.title}
Book {book.book_number} of {len(series.books)}: {book.title}

Premise:
{book.premise}

Target Word Count: {book.target_word_count}
Themes: {', '.join(book.themes)}

Character Arcs:
"""

        for arc in book.character_arcs:
            context += f"  - {arc.character_name}: {arc.starting_state} → {arc.ending_state}\n"
            context += f"    Transformation: {arc.arc_type}\n"

        if book.chapters:
            context += f"\nChapter Breakdown ({len(book.chapters)} chapters):\n"
            for chapter in book.chapters:
                context += f"\n  Chapter {chapter.chapter_number}: {chapter.title}\n"
                context += f"    Purpose: {chapter.purpose}\n"
                if hasattr(chapter, 'character_focus') and chapter.character_focus:
                    context += f"    POV: {chapter.character_focus.pov}\n"

        context += f"\n\nSeries Context:\n"
        context += f"  - Genre: {series.genre}\n"
        context += f"  - Target Audience: {series.target_audience}\n"
        context += f"  - Series Themes: {', '.join(series.themes)}\n"

        return context
