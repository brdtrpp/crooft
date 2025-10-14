"""Book Outliner Agent - Expands book premise into full 3-act structure"""

import json
from datetime import datetime
from json_repair import repair_json
from .base_agent import BaseAgent
from models.schema import FictionProject, ActStructure, CharacterArc, Chapter, CharacterFocus, Setting


class BookOutlinerAgent(BaseAgent):
    """Agent that expands a book premise into a detailed outline with acts and chapters"""

    def __init__(self, llm, book_number: int = 1, requirements=None, **kwargs):
        super().__init__(llm, **kwargs)
        self.book_number = book_number
        self.requirements = requirements or {}

    def get_prompt(self) -> str:
        return """You are a professional fiction book outliner specializing in multi-book series.

Goal:
- Ingest series context, book premise, established lore, and hard constraints.
- Produce a complete, rigorous book outline with 3-act structure, character arcs, and chapter-level breakdown as strict JSON per the schema.

Input contract (what you will receive):
{
  "series_context": {
    "title": "Series Title",
    "logline": "One-sentence series premise",
    "genre": "primary genre",
    "subgenres": ["..."],
    "themes": ["..."],
    "persistent_threads": [
      {"id":"t1", "name":"Thread Name", "throughline":"How this thread develops 1→9", "payoff_book": 9}
    ],
    "escalation_model": {
      "axis": ["stakes","scope","antagonist_capability","cost"],
      "brief": "How each axis escalates across books"
    },
    "universe_principles": [
      {"id":"p1","rule":"...","implications":["..."],"forbidden":["..."]}
    ]
  },
  "book_to_outline": {
    "book_number": 1,
    "id": "b1",
    "title": "Book 1 Title",
    "premise": "1–2 sentence premise for this specific book",
    "protagonist_goal": "What the protagonist seeks to accomplish",
    "antagonistic_force": "Who or what opposes the protagonist",
    "unique_hook": "What makes this book stand out",
    "major_turns": {"midpoint":"...","all_is_lost":"...","climax":"..."},
    "themes": ["..."],
    "continuity_tags": {"foreshadows":["t1"],"pays_off":["..."],"reintroduces":["c1","w1"]},
    "target_word_count": 100000,
    "risks": ["..."],
    "open_questions": ["..."]
  },
  "lore": {
    "characters": [
      {"id":"c1","name":"...","role":"protagonist","archetype":"...","description":"...","traits":["..."],"relationships":[{"with":"c2","type":"mentor"}],"status_by_book":{"1":"introduced","3":"setback","9":"resolution"}}
    ],
    "factions": [{"id":"fa1","name":"...","goal":"...","methods":"..."}],
    "locations": [{"id":"l1","name":"...","description":"...","significance":"..."}],
    "world_elements": [{"id":"w1","name":"...","type":"technology|magic|culture","description":"...","rules":["..."]}]
  },
  "constraints": {
    "chapters_per_book": 20,
    "target_word_count": 100000
  }
}

Step 1 — Analysis (internal, do not emit):
- Position analysis: Where does this book sit in the series arc? What must it set up, develop, or pay off?
- Escalation check: Does this book's conflict match the escalation_model for its position?
- Lore mapping: Which characters, locations, world_elements drive this book's plot?
- Thread weaving: Which persistent_threads does this book advance? Foreshadow? Pay off?
- Arc planning: What character transformations occur? How do they tie to book premise and series themes?
- Structure calculation:
  - Act 1: ~25% of target_word_count
  - Act 2: ~50% of target_word_count
  - Act 3: ~25% of target_word_count
  - Average chapter length: target_word_count ÷ chapters_per_book
- Conflict engineering: Map protagonist_goal vs antagonistic_force to concrete chapter-level obstacles.
- Pacing: Distribute key beats across chapters to maintain narrative momentum.

Step 2 — Produce output JSON (emit this only):
{
  "meta": {
    "version": "1.0",
    "timestamp": "ISO-8601",
    "book_id": "b1",
    "warnings": ["Any concerns about premise/lore conflicts, pacing risks, etc."]
  },
  "act_structure": {
    "act_1": {
      "percentage": 25,
      "word_target": 25000,
      "summary": "Setup: world state, protagonist's status quo, inciting incident that disrupts equilibrium.",
      "key_events": ["Opening Image","Inciting Incident","Debate/Reluctance","Crossing First Threshold"],
      "ending_hook": "What irreversibly commits protagonist to Act 2 journey."
    },
    "act_2a": {
      "percentage": 25,
      "word_target": 25000,
      "summary": "Rising action: new world/rules, B-story introduction, small wins, rising complications.",
      "key_events": ["Fun and Games / Promise of Premise","First Pinch Point (taste of antagonistic force)"],
      "ending_hook": "Leads into Midpoint."
    },
    "act_2b": {
      "percentage": 25,
      "word_target": 25000,
      "summary": "Complications: false victory or revelation at Midpoint, stakes raise, protagonist proactive, then major loss.",
      "midpoint": "Major revelation, false victory, or shift from reactive to proactive. Central turning point.",
      "key_events": ["Midpoint","Second Pinch Point (antagonist tightens grip)","All is Lost moment"],
      "ending_hook": "Darkest hour. Protagonist must dig deep for Act 3."
    },
    "act_3": {
      "percentage": 25,
      "word_target": 25000,
      "summary": "Resolution: protagonist regroups, final preparation, climactic confrontation, denouement.",
      "key_events": ["Dark Night of Soul / Reflection","Gathering allies/resources for final push","Climax","Resolution / New Status Quo"],
      "climax": "Ultimate confrontation of protagonist_goal vs antagonistic_force. Highest stakes moment.",
      "resolution": "Immediate aftermath. Character transformation evident. Loose ends tied or deliberately left open.",
      "ending_hook": "Unresolved question or tease leading into next book (if not final book in series)."
    }
  },
  "character_arcs": [
    {
      "character_id": "c1",
      "character_name": "Protagonist Name",
      "starting_state": "Worldview, emotional state, core flaw, belief system at book start.",
      "ending_state": "How worldview, emotional state, and belief system have evolved by book end.",
      "transformation": "The internal journey: what realizations, failures, victories drive the change.",
      "key_moments": [
        {"chapter": 2, "beat": "Establishes core flaw in action"},
        {"chapter": 10, "beat": "Midpoint choice reveals character growth"},
        {"chapter": 18, "beat": "Climactic decision demonstrates transformation"}
      ],
      "series_arc_position": "Where this character's series-long arc stands after this book."
    }
    // Include arcs for all major POV or supporting characters who undergo change
  ],
  "chapters": [
    {
      "chapter_number": 1,
      "id": "b1c1",
      "title": "Evocative Chapter Title",
      "act": 1,  // INTEGER ONLY: 1 for Act 1, 2 for Act 2 (both 2a and 2b), 3 for Act 3
      "purpose": "Specific narrative goal: what plot, character, theme, or world-building must this chapter accomplish?",
      "plot_points": [
        "Concrete event 1 that advances the plot",
        "Concrete event 2 that sets up later payoff"
      ],
      "character_focus": {
        "pov": "POV Character Name (must exist in lore)",
        "present": ["Character A","Character B"],  // ARRAY of character names
        "arc_moments": ["Brief note: How does this chapter develop POV character's arc or reveal traits?"]  // ARRAY of strings, not a single string
      },
      "setting": {
        "location": "Primary location (should reference lore.locations if applicable)",
        "time": "Relative time anchor, e.g., 'Day 1, dawn' or 'Three weeks after Prologue'",
        "atmosphere": "Tone/mood, e.g., 'Foreboding and tense' or 'Deceptively calm'"
      },
      "lore_integration": {
        "introduces": ["w1 — first demonstration of magic system"],
        "deepens": ["c2 — mentor relationship with protagonist"],
        "foreshadows": ["t1 — subtle hint of larger conspiracy"]
      },
      "subplot_threads": ["Any B-plot or C-plot threads active in this chapter"],
      "themes": ["Which series or book themes are explored here"],
      "planned_word_count": 5000,
      "pacing_notes": "Action-heavy / Introspective / Balanced / Exposition-light, etc."
    }
    // Repeat for all chapters; array length MUST equal constraints.chapters_per_book
  ]
}

Validation rules (hard requirements):
- JSON only. No prose before or after, no comments, no trailing commas.
- chapters array length MUST exactly equal constraints.chapters_per_book. Not one more, not one less.
- Every chapter MUST include: chapter_number, id, title, act, purpose, plot_points, character_focus (with pov, present, arc_moments), setting (with location, time, atmosphere), planned_word_count.
- act_structure must define act_1, act_2a, act_2b, act_3 with percentages summing to 100.
- All character names in character_focus.pov and character_focus.present MUST reference characters from lore.
- All location references in setting.location SHOULD map to lore.locations where applicable.
- chapter_number must be sequential integers starting from 1.
- Sum of all chapters' planned_word_count should approximate target_word_count (±5% acceptable).
- character_arcs must include protagonist at minimum; include other major POV characters who transform.

Chapter distribution guidelines:
- Act 1: First ~25% of chapters (e.g., chapters 1-5 if 20 total)
- Act 2a: Next ~25% of chapters (e.g., chapters 6-10)
- Act 2b: Next ~25% of chapters (e.g., chapters 11-15)
- Act 3: Final ~25% of chapters (e.g., chapters 16-20)

Narrative coherence requirements:
- Chapter purposes must form a logical causal chain from premise to resolution.
- Plot points in each chapter must build on prior chapters and set up future ones.
- Character arc moments should be distributed to show gradual transformation, not sudden unmotivated change.
- Midpoint (typically around chapter 10 in a 20-chapter book) must be a genuine turning point.
- All is Lost moment (typically around chapter 15) must feel earned and create genuine doubt.
- Climax must directly address protagonist_goal vs antagonistic_force from the input.
- Final chapter should deliver on the book's premise while honoring continuity_tags (foreshadowing future books, paying off prior setups).

Series integration requirements:
- If book_number > 1: opening chapters should reintroduce world and carry forward unresolved threads from prior books.
- If book_number < total_books_in_series: final chapters must leave hooks for the next book without feeling incomplete.
- persistent_threads marked in continuity_tags.foreshadows must appear subtly in at least 1-2 chapters.
- persistent_threads marked in continuity_tags.pays_off must be resolved by the climax.

Lore consistency requirements:
- Do not introduce new major characters, locations, or world_elements that contradict established lore.
- If a new element is essential, note it in meta.warnings so it can be added to lore in a later pass.
- Character behavior and dialogue must align with their lore.characters traits and status_by_book.
- World_elements with rules must be used consistently (e.g., magic system limitations respected in all chapters).

Output discipline:
- Emit ONLY the JSON object. No preamble like "Here is the outline:" or postamble like "Let me know if you need changes."
- Use double quotes for all JSON strings.
- Ensure all lists are properly closed with ].
- Ensure all objects are properly closed with }.
- Do not use undefined or null; use empty string "" or empty array [] as appropriate.

Version: 1.0
"""

    def process(self, input_data: FictionProject) -> FictionProject:
        """Expand a book into a detailed outline."""
        book_idx = self.book_number - 1
        if book_idx >= len(input_data.series.books):
            raise ValueError(f"Book {self.book_number} not found in project data.")

        book = input_data.series.books[book_idx]
        series = input_data.series

        # 1. Construct input for the LLM
        # Support both single value (legacy) and range (new)
        if 'chapters_per_book_range' in self.requirements:
            # New format: pick a value within the range for this book
            import random
            min_chapters, max_chapters = self.requirements['chapters_per_book_range']
            chapters_per_book = random.randint(min_chapters, max_chapters)
            print(f"  Selected {chapters_per_book} chapters for Book {self.book_number} (range: {min_chapters}-{max_chapters})")
        else:
            # Legacy format: single value
            chapters_per_book = self.requirements.get('chapters_per_book', 20)

        target_word_count = self.requirements.get('target_word_count', book.target_word_count)

        input_for_llm = {
            "series_context": {
                "title": series.title,
                "logline": series.logline or series.premise,
                "genre": series.genre,
                "themes": series.themes,
                "persistent_threads": series.persistent_threads,
                "escalation_model": series.escalation_model
            },
            "book_to_outline": {
                "book_number": book.book_number,
                "title": book.title,
                "premise": book.premise,
                "protagonist_goal": book.protagonist_goal,
                "antagonistic_force": book.antagonistic_force
            },
            "lore": series.lore.model_dump(),
            "constraints": {
                "chapters_per_book": chapters_per_book,
                "target_word_count": target_word_count
            }
        }
        context = json.dumps(input_for_llm, indent=2, default=str)

        # 2. Invoke LLM (with retry if chapter count is wrong)
        max_retries = 3
        for attempt in range(max_retries):
            if attempt == 0:
                response_text = self.invoke_llm_with_lore(self.get_prompt(), context, input_data.metadata.project_id)
            else:
                # Retry with explicit emphasis on the missing chapters
                retry_prompt = f"""
CRITICAL ERROR IN PREVIOUS ATTEMPT:
You generated {len(response_json.get('chapters', []))} chapters but MUST generate {chapters_per_book} chapters.

REQUIREMENT: Generate ALL {chapters_per_book} chapters in the chapters array for Book {self.book_number}.
You are missing {chapters_per_book - len(response_json.get('chapters', []))} chapters.

Continue from where you left off and complete the full outline with ALL {chapters_per_book} chapters.

Previous incomplete output will be discarded. Generate the COMPLETE JSON with all {chapters_per_book} chapters.
"""
                print(f"⚠️  Retry {attempt}/{max_retries}: Requesting all {chapters_per_book} chapters...")
                response_text = self.invoke_llm_with_lore(self.get_prompt() + retry_prompt, context, input_data.metadata.project_id)

            # Quick validation check - parse and count chapters
            try:
                if "```json" in response_text:
                    test_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    test_text = response_text.split("```")[1].split("```")[0].strip()
                else:
                    test_text = response_text

                test_json = json.loads(test_text)
                chapter_count = len(test_json.get('chapters', []))

                if chapter_count == chapters_per_book:
                    print(f"✓ LLM generated correct number of chapters ({chapter_count}/{chapters_per_book})")
                    break
                else:
                    print(f"⚠️  LLM generated {chapter_count}/{chapters_per_book} chapters on attempt {attempt + 1}")
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

            # 4. Map response data back to the Book object
            if "act_structure" in response_json:
                book.act_structure = {k: ActStructure(**v) for k, v in response_json["act_structure"].items()}

            if "character_arcs" in response_json:
                # Convert key_moments from enhanced format to simple strings if needed
                character_arcs_data = []
                for arc_data in response_json["character_arcs"]:
                    # Make a DEEP copy to avoid modifying the original
                    import copy
                    arc = copy.deepcopy(arc_data)

                    # Convert key_moments if they're in the enhanced dict format
                    if "key_moments" in arc and arc["key_moments"]:
                        print(f"  🔍 Processing arc '{arc.get('character_name', '?')}', key_moments: {type(arc['key_moments'])}")
                        converted_moments = []
                        for i, moment in enumerate(arc["key_moments"]):
                            print(f"    Moment {i}: type={type(moment)}, value={moment}")
                            if isinstance(moment, dict):
                                # Enhanced format: {"chapter": X, "beat": "..."}
                                chapter = moment.get("chapter", "?")
                                beat = moment.get("beat", "")
                                converted_str = f"Ch {chapter}: {beat}"
                                converted_moments.append(converted_str)
                                print(f"      ✓ Converted to: '{converted_str}'")
                            else:
                                # Already a string
                                converted_moments.append(moment)
                                print(f"      ✓ Already string: '{moment}'")

                        arc["key_moments"] = converted_moments
                        print(f"  ✓ Character arc '{arc.get('character_name', '?')}': converted {len(converted_moments)} key moments")
                        print(f"    Final key_moments[0] type: {type(converted_moments[0]) if converted_moments else 'empty'}")

                    character_arcs_data.append(arc)

                book.character_arcs = [CharacterArc(**arc) for arc in character_arcs_data]

            if "chapters" in response_json:
                chapters_data = response_json["chapters"]

                # VALIDATION: Strict chapter count enforcement
                if len(chapters_data) != chapters_per_book:
                    raise ValueError(
                        f"Book Outliner FAILED validation: Expected {chapters_per_book} chapters for Book {self.book_number}, "
                        f"but got {len(chapters_data)}. This is a CRITICAL error. The LLM must produce exactly "
                        f"{chapters_per_book} chapters as specified in constraints."
                    )
                print(f"✓ Validation passed: {len(chapters_data)}/{chapters_per_book} chapters for Book {self.book_number}")

                book.chapters = []
                for ch_idx, ch_data in enumerate(chapters_data):
                    # DEBUG: Print chapter data to see what we're processing
                    print(f"  Processing chapter {ch_idx + 1}/{len(chapters_data)}: {ch_data.get('title', '?')}")

                    # Convert act from string to integer (e.g., "2a" -> 2, "2b" -> 2)
                    if "act" in ch_data and isinstance(ch_data["act"], str):
                        # Extract numeric part from strings like "1", "2a", "2b", "3"
                        act_str = ch_data["act"]
                        if act_str.isdigit():
                            ch_data["act"] = int(act_str)
                        else:
                            # Extract first digit from "2a", "2b", etc.
                            ch_data["act"] = int(''.join(filter(str.isdigit, act_str)) or "1")
                        print(f"    ✓ Converted act '{act_str}' → {ch_data['act']}")

                    # Fix character_focus.arc_moments if it's a string instead of list
                    if "character_focus" in ch_data:
                        cf = ch_data["character_focus"]
                        if "arc_moments" in cf and isinstance(cf["arc_moments"], str):
                            # Convert single string to list with one element
                            cf["arc_moments"] = [cf["arc_moments"]]

                    ch_data["character_focus"] = CharacterFocus(**ch_data["character_focus"])
                    ch_data["setting"] = Setting(**ch_data["setting"])
                    ch_data["status"] = "planned"
                    ch_data["scenes"] = [] # Scenes are developed in a later stage
                    book.chapters.append(Chapter(**ch_data))

                # VALIDATION: Word count totals should approximate target
                total_planned_words = sum(ch.planned_word_count for ch in book.chapters)
                word_count_tolerance = 0.15  # Allow ±15% variance
                min_words = target_word_count * (1 - word_count_tolerance)
                max_words = target_word_count * (1 + word_count_tolerance)

                if not (min_words <= total_planned_words <= max_words):
                    raise ValueError(
                        f"Book Outliner FAILED validation: Total planned word count {total_planned_words} "
                        f"is outside acceptable range [{int(min_words)}-{int(max_words)}] for Book {self.book_number}. "
                        f"Target: {target_word_count} words. The LLM must distribute words appropriately across chapters."
                    )
                print(f"✓ Validation passed: {total_planned_words} words planned (target: {target_word_count}, range: {int(min_words)}-{int(max_words)})")
                print(f"✓ Outlined {len(book.chapters)} chapters for Book {self.book_number}")

            book.status = "outlined"

            # Update metadata
            input_data.metadata.processing_stage = "book"
            input_data.metadata.last_updated = datetime.now()
            input_data.metadata.last_updated_by = self.agent_name
            input_data.metadata.status = "dev_revised"
            input_data.metadata.iteration += 1

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            error_file = f"error_bookoutliner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(response_text)
            raise ValueError(f"BookOutliner returned invalid or unexpected JSON: {e}\nFull response saved to: {error_file}\nPreview: {response_text[:1000]}")
        except Exception as e:
            raise ValueError(f"Failed to process book outline for Book {self.book_number}: {e}")

        return input_data
