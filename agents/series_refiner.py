"""Series Refiner Agent - Expands initial concept into complete series outline"""

import json
from datetime import datetime
from json_repair import repair_json
from .base_agent import BaseAgent
from models.schema import FictionProject, Series, Lore, Book


class SeriesRefinerAgent(BaseAgent):
    """Agent that refines a basic series concept into a detailed series outline"""

    def __init__(self, llm, lore_store=None, requirements=None, **kwargs):
        super().__init__(llm, lore_store=lore_store, **kwargs)
        self.requirements = requirements or {}

    def get_prompt(self) -> str:
        return """You are a professional fiction series refiner.

Goal:
- Ingest free-form text/markdown and optional feedback JSON.
- Extract structured inputs.
- Produce or revise a multi-book series outline as strict JSON per the schema and rules.

Inputs:
- raw_text: free-form text or markdown describing the concept and any book notes.
- feedback (optional): JSON array of feedback items the author wants applied.

Input contract (what you will receive):
{
  "raw_text": "string — may include headings (#, ##), bullets, numbered beats, scene lists, etc.",
  "constraints": {
    "book_count": "REQUIRED - exact number of books to generate (e.g., 10)",
    "target_word_count_per_book": "Target word count for each book (e.g., 100000)",
    "chapters_per_book": "Chapters per book (e.g., 20)"
  },
  "feedback": [
    {
      "id": "f1",
      "type": "request|issue|constraint|preference",
      "target_ids": ["optional: IDs from a prior outline if known"],
      "text": "clear, actionable feedback item"
    }
    // ... more items
  ]
}

Step 1 — Extraction (internal, do not emit):
- Parse raw_text to extract and/or infer:
  - series_concept: 1–3 sentences
  - genre_primary and subgenres
  - target_audience
  - themes
  - must_include and must_avoid
  - comparables
  - any explicit book beats or premises per book number/title
- If something is missing, infer conservatively. Record low-confidence inferences in meta.warnings.

Construct internal extracted_inputs:
{
  "series_concept": "...",
  "constraints": {
    "book_count": "<USE THE EXACT VALUE FROM INPUT constraints.book_count - THIS IS MANDATORY>",
    "genre_primary": "...",
    "subgenres": ["..."],
    "target_audience": "adult|YA|MG",
    "word_count_range": {"min": 85000, "max": 110000},
    "must_include": ["..."],
    "must_avoid": ["..."]
  },
  "preferences": {
    "comparables": ["..."],
    "tone": "infer from style if possible"
  },
  "books_from_text": [
    // Optional — any explicit per-book details (titles, beats, antagonists) parsed from raw_text
    {"book_number": 1, "title": "If present", "beats": {"opening_image": "...", "midpoint": "...", "all_is_lost": "...", "climax": "..."}, "antagonist": "..."}
  ]
}

Step 2 — Apply feedback:
- Map each feedback item to changes in the outline.
- If feedback conflicts, prefer constraints over preferences and note conflict in meta.warnings.
- Set meta.revision.applied_feedback_ids to IDs you actually applied.

Step 3 — Produce output JSON (emit this only):

CRITICAL BEFORE YOU BEGIN:
- You MUST generate EXACTLY constraints.book_count books in the books array
- If constraints.book_count = 10, generate 10 complete book entries
- If you generate fewer books, your output will be REJECTED
- Count your book entries before submitting to ensure the count matches

{
  "meta": {
    "version": "1.0",
    "timestamp": "ISO-8601",
    "revision": {
      "number": 1,
      "applied_feedback_ids": ["f1","f3"],
      "change_log": ["Concise bullets of what changed and why"]
    },
    "warnings": ["Any low-confidence inferences or feedback conflicts"]
  },
  "series": {
    "id": "series-uuid",
    "title": "Series Title",
    "logline": "One-sentence series premise",
    "genre": "primary genre",
    "subgenres": ["..."],
    "target_audience": "adult|YA|MG",
    "themes": ["..."],
    "universe_principles": [
      {"id":"p1","rule":"...","implications":["..."],"forbidden":["..."]}
    ],
    "assumptions": ["..."],
    "risks": ["..."],
    "open_questions": ["..."],
    "persistent_threads": [
      {"id":"t1","name":"...","throughline":"1-9 path","payoff_book": 9}
    ],
    "lore": {
      "characters": [
        {"id":"c1","name":"...","role":"protagonist","archetype":"...","description":"...","traits":["..."],"relationships":[{"with":"c2","type":"mentor"}],"status_by_book":{"1":"introduced","3":"setback","9":"resolution"}}
      ],
      "factions": [{"id":"fa1","name":"...","goal":"...","methods":"..."}],
      "locations": [{"id":"l1","name":"...","description":"...","significance":"..."}],
      "world_elements": [{"id":"w1","name":"...","type":"technology|magic","description":"...","rules":["..."]}]
    },
    "escalation_model": {
      "axis": ["stakes","scope","antagonist_capability","cost"],
      "brief": "How each axis escalates across books 1→9"
    },
    "books": [
      {
        "book_number": 1,
        "id": "b1",
        "title": "Book 1 Title",
        "premise": "1–2 sentences",
        "protagonist_goal": "...",
        "antagonistic_force": "...",
        "unique_hook": "...",
        "major_turns": {"midpoint":"...","all_is_lost":"...","climax":"..."},
        "themes": ["..."],
        "continuity_tags": {"foreshadows":["t1"],"pays_off":["..."],"reintroduces":["c1","w1"]},
        "target_word_count": 100000,
        "status": "planned",
        "risks": ["..."],
        "open_questions": ["..."]
      },
      {
        "book_number": 2,
        "id": "b2",
        "title": "Book 2 Title",
        "premise": "...",
        "protagonist_goal": "...",
        "antagonistic_force": "...",
        "unique_hook": "...",
        "major_turns": {"midpoint":"...","all_is_lost":"...","climax":"..."},
        "themes": ["..."],
        "continuity_tags": {"foreshadows":["..."],"pays_off":["..."],"reintroduces":["..."]},
        "target_word_count": 100000,
        "status": "planned",
        "risks": ["..."],
        "open_questions": ["..."]
      }
      // ... CONTINUE THIS PATTERN FOR ALL BOOKS UP TO constraints.book_count
      // If constraints.book_count = 10, you MUST have books 1 through 10 in this array
      // DO NOT STOP EARLY - generate all required books
    ]
  }
}

Validation rules (hard requirements):
- JSON only. No prose, comments, or trailing commas.
- series.title and series.logline non-empty.
- books array length MUST EXACTLY EQUAL constraints.book_count from input. NOT ONE MORE, NOT ONE LESS.
- Every book has: premise, protagonist_goal, antagonistic_force, unique_hook, major_turns.
- escalation_model present and coherent across books.
- Preserve IDs across revisions if prior outline is provided in raw_text or implied; otherwise generate stable IDs.

CRITICAL VALIDATION RULE:
The books array MUST contain EXACTLY the number of books specified in input constraints.book_count.
If constraints.book_count = 10, you MUST generate 10 books. If you generate 9 or 11, the output will be REJECTED.

Notes:
- When raw_text contains explicit per-book headings or beats (e.g., "## Outlaw", "## Rogue", "## Guard"), map them to books.title and seed premise, antagonistic_force, and major_turns.
- If numbering is implied by order of sections, assign book_number accordingly, unless an explicit number is present.
- If author-provided beats conflict with inferred genre or themes, keep the beats and note the conflict in meta.warnings.
"""

    def process(self, input_data: FictionProject) -> FictionProject:
        """Process the series concept and expand it into a detailed outline."""

        # Check if this is already a processed project (has books, no raw_text)
        if not input_data.series.raw_text and input_data.series.books:
            print("⚠️  Series already processed - skipping Series Refiner")
            # Update metadata to show we processed it (even though we skipped)
            input_data.metadata.last_updated = datetime.now()
            input_data.metadata.last_updated_by = self.agent_name
            input_data.metadata.processing_stage = "series"
            return input_data

        # If no raw_text and no books, we have a problem
        if not input_data.series.raw_text:
            # Try to reconstruct raw_text from existing data
            raw_text = f"Title: {input_data.series.title}\nPremise: {input_data.series.premise}\nGenre: {input_data.series.genre}"
            if input_data.series.target_audience:
                raw_text += f"\nTarget Audience: {input_data.series.target_audience}"
        else:
            raw_text = input_data.series.raw_text

        # 1. Construct input for the LLM with hard constraints
        num_books = self.requirements.get('num_books', len(input_data.series.books) if input_data.series.books else 1)

        input_for_llm = {
            "raw_text": raw_text,
            "feedback": input_data.series.feedback or [],
            "constraints": {
                "book_count": num_books,
                "target_word_count_per_book": self.requirements.get('target_word_count', 100000),
                "chapters_per_book": self.requirements.get('chapters_per_book', 20)
            }
        }
        context = json.dumps(input_for_llm, indent=2)

        # 2. Invoke LLM (with retry if book count is wrong)
        max_retries = 3
        for attempt in range(max_retries):
            if attempt == 0:
                response_text = self.invoke_llm(self.get_prompt(), context)
            else:
                # Retry with explicit emphasis on the missing books
                retry_prompt = f"""
CRITICAL ERROR IN PREVIOUS ATTEMPT:
You generated {len(response_json.get('series', {}).get('books', []))} books but MUST generate {num_books} books.

REQUIREMENT: Generate ALL {num_books} books in the books array.
You are missing {num_books - len(response_json.get('series', {}).get('books', []))} books.

Continue from where you left off and complete the full series outline with ALL {num_books} books.

Previous incomplete output will be discarded. Generate the COMPLETE JSON with all {num_books} books.
"""
                print(f"⚠️  Retry {attempt}/{max_retries}: Requesting all {num_books} books...")
                response_text = self.invoke_llm(self.get_prompt() + retry_prompt, context)

            # Quick validation check - parse and count books
            try:
                if "```json" in response_text:
                    test_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    test_text = response_text.split("```")[1].split("```")[0].strip()
                else:
                    test_text = response_text

                test_json = json.loads(test_text)
                book_count = len(test_json.get('series', {}).get('books', []))

                if book_count == num_books:
                    print(f"✓ LLM generated correct number of books ({book_count}/{num_books})")
                    break
                else:
                    print(f"⚠️  LLM generated {book_count}/{num_books} books on attempt {attempt + 1}")
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

            # 4. Map response data back to the FictionProject object
            series_data = response_json.get("series", {})
            meta_data = response_json.get("meta", {})

            # Update series-level fields
            s = input_data.series
            s.id = series_data.get("id", s.id)
            s.title = series_data.get("title", s.title)
            s.logline = series_data.get("logline", s.logline)
            s.genre = series_data.get("genre", s.genre)
            s.subgenres = series_data.get("subgenres", s.subgenres)
            s.target_audience = series_data.get("target_audience", s.target_audience)
            s.themes = series_data.get("themes", s.themes)
            s.universe_principles = series_data.get("universe_principles", s.universe_principles)
            s.assumptions = series_data.get("assumptions", s.assumptions)
            s.risks = series_data.get("risks", s.risks)
            s.open_questions = series_data.get("open_questions", s.open_questions)
            s.persistent_threads = series_data.get("persistent_threads", s.persistent_threads)
            s.escalation_model = series_data.get("escalation_model", s.escalation_model)

            # Update Lore
            lore_data = series_data.get("lore", {})
            if lore_data:
                s.lore = Lore(**lore_data)

            # Update Books
            books_data = series_data.get("books", [])
            if books_data:
                # Fix continuity_tags if it's an empty list instead of dict
                for book_data in books_data:
                    if "continuity_tags" in book_data and isinstance(book_data["continuity_tags"], list):
                        if not book_data["continuity_tags"]:  # Empty list
                            book_data["continuity_tags"] = {
                                "foreshadows": [],
                                "pays_off": [],
                                "reintroduces": []
                            }
                s.books = [Book(**book_data) for book_data in books_data]

            # VALIDATION: Ensure correct number of books were created
            expected_books = self.requirements.get('num_books', 1)
            actual_books = len(s.books)
            if actual_books != expected_books:
                raise ValueError(
                    f"Series Refiner FAILED validation: Expected {expected_books} books, but got {actual_books}. "
                    f"This is a CRITICAL error. The LLM must produce exactly {expected_books} books as specified in constraints."
                )
            print(f"✓ Validation passed: {actual_books}/{expected_books} books created")

            # Update metadata
            m = input_data.metadata
            m.last_updated_by = self.agent_name
            m.processing_stage = "series"
            m.last_updated = datetime.fromisoformat(meta_data.get("timestamp", datetime.now().isoformat()))
            m.status = "dev_revised"
            m.iteration += 1

            # Optionally, add to revision history
            revision_info = meta_data.get("revision", {})
            if revision_info.get("change_log"):
                from models.schema import RevisionHistory
                history_entry = RevisionHistory(
                    timestamp=m.last_updated.isoformat(),
                    agent=self.agent_name,
                    scope="series",
                    changes_summary="; ".join(revision_info["change_log"]),
                    reason="Agent processing of raw text and feedback."
                )
                input_data.revision_history.append(history_entry)

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            error_file = f"error_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(response_text)
            raise ValueError(f"Agent returned invalid or unexpected JSON structure: {e}\nFull response saved to: {error_file}\nPreview: {response_text[:1000]}")
        except Exception as e:
            raise ValueError(f"Failed to process series refinement: {e}")

        return input_data
