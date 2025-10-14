# Technical Specification: Reproducible Fiction Generation Pipeline

**Version**: 1.0

**Target**: LangChain + Ollama/OpenRouter hybrid implementation

**Language**: Python 3.10+

**Output**: Complete book outlines from series concepts

---

## 1. System Architecture

### 1.1 Core Components

```
project/
├── agents/
│   ├── __init__.py
│   ├── base_[agent.py](http://agent.py)          # Abstract base class
│   ├── series_[refiner.py](http://refiner.py)
│   ├── book_[outliner.py](http://outliner.py)
│   ├── chapter_[developer.py](http://developer.py)
│   ├── scene_[developer.py](http://developer.py)
│   ├── beat_[developer.py](http://developer.py)
│   ├── qa_[agent.py](http://agent.py)
│   └── lore_[master.py](http://master.py)
├── models/
│   ├── __init__.py
│   ├── [schema.py](http://schema.py)              # Pydantic models
│   └── [config.py](http://config.py)              # LLM configurations
├── validators/
│   ├── __init__.py
│   └── schema_[validator.py](http://validator.py)
├── utils/
│   ├── __init__.py
│   ├── [logger.py](http://logger.py)
│   ├── state_[manager.py](http://manager.py)       # Checkpointing
│   └── [prompts.py](http://prompts.py)             # Versioned prompts
├── tests/
│   ├── test_[schema.py](http://schema.py)
│   ├── test_[agents.py](http://agents.py)
│   └── fixtures/
│       ├── minimal_series.txt
│       ├── standard_series.txt
│       └── expected_outputs/
├── output/                     # Generated JSON files
├── logs/                       # Run logs
├── [pipeline.py](http://pipeline.py)                 # Main orchestrator
├── [run.py](http://run.py)                      # CLI entry point
├── requirements.txt
└── [README.md](http://README.md)
```

### 1.2 Data Flow (Quality Gate Pattern)

**Every content agent is followed by QA → Lore Master validation**

**All agents query Pinecone for relevant lore before generation**

```jsx
Input (text)
    ↓
[Series Refiner] → JSON v1 (creates initial lore)
    ↓ (schema validate)
[Store Lore in Pinecone] → Vector embeddings of all lore entries
    ↓
[QA Agent] → v1 + qa_report
    ↓ QA PASS?
    ├─ NO → retry with feedback (max 3x) → FAIL if still no pass
    └─ YES → continue
        ↓
[Lore Master Agent] → v1 + lore validation
    ↓ LORE PASS?
    ├─ NO → retry with feedback (max 3x) → FAIL if still no pass
    └─ YES → continue
        ↓
[Book Outliner Agent] → JSON v2 (queries Pinecone for lore before generation)
    ↓ (validate)
[QA Agent] → v2 + qa_report
    ↓ QA PASS?
    ├─ NO → retry
    └─ YES → continue
        ↓
[Lore Master Agent] → v2 + lore validation + detect new lore
    ↓ LORE PASS?
    ├─ NO → retry
    └─ YES → continue
        ↓
[Chapter Developer Agent] → JSON v3 (queries lore)
    ↓ (validate)
[QA + Lore Master] → ... (repeat pattern)
    ↓
[Scene Developer Agent] → JSON v4
    ↓ (validate + QA + Lore)
[Beat Developer Agent] → JSON v5
    ↓ (validate + QA + Lore)
[Prose Generator Agent] → JSON v6 (beats with prose)
    ↓ (validate + QA + Lore)
[Editorial Phase]
    ├─ Story Analyst
    ├─ Consistency Validator
    ├─ Developmental Editor (with re-analysis cycles)
    └─ Line Editor
    ↓
[Final QA] → Approval
    ↓
[Export] → .md manuscript + .json project file
```

**State Persistence**: After each agent completes, save full JSON to `output/project_v{iteration}.json`

**Quality Gate Logic**:

- Content agent generates → Schema validation
- QA Agent reviews structure/craft → Approval status
- Lore Master checks continuity → Approval status
- Both must return "approved" to advance
- On failure: inject feedback into retry prompt

**Error Recovery**: If agent fails validation, retry up to 3x with error feedback in prompt

---

## 2. Data Structures (Pydantic Models)

### 2.1 Complete Schema

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

class Metadata(BaseModel):
    schema_version: str = "1.0"
    last_updated: datetime
    last_updated_by: str
    processing_stage: Literal["series", "book", "chapter", "scene", "beat", "qa", "prose"]
    status: Literal["draft", "in_review", "approved", "needs_revision"]
    project_id: str
    iteration: int = 1

class Character(BaseModel):
    name: str
    role: str
    description: str
    traits: List[str] = []
    relationships: List[str] = []

class Location(BaseModel):
    name: str
    description: str
    significance: str

class WorldElement(BaseModel):
    name: str
    type: Literal["technology", "magic", "species", "faction", "custom"]
    description: str
    rules: List[str] = []

class Lore(BaseModel):
    characters: List[Character] = []
    locations: List[Location] = []
    world_elements: List[WorldElement] = []

class ActStructure(BaseModel):
    percentage: int
    word_target: int
    summary: str
    key_events: List[str] = []
    ending_hook: str
    midpoint: Optional[str] = None  # Act 2 only
    climax: Optional[str] = None     # Act 3 only
    resolution: Optional[str] = None # Act 3 only

class CharacterArc(BaseModel):
    character_name: str
    starting_state: str
    ending_state: str
    transformation: str
    key_moments: List[str] = []

class Conflict(BaseModel):
    type: Literal["internal", "external", "interpersonal"]
    description: str

class Setting(BaseModel):
    location: str = ""
    time: str = ""
    atmosphere: str = ""
    primary_location: Optional[str] = None
    time_period: Optional[str] = None

class Prose(BaseModel):
    draft_version: int = 1
    content: str = ""
    word_count: int = 0
    generated_timestamp: str = ""
    status: Literal["draft", "revised", "final"] = "draft"

class Beat(BaseModel):
    beat_number: int
    description: str
    emotional_tone: str
    character_actions: List[str] = []
    dialogue_summary: str = ""
    prose: Optional[Prose] = None

class Scene(BaseModel):
    scene_id: str
    scene_number: int
    title: str = ""
    purpose: str
    scene_type: Literal["action", "dialogue", "exposition", "transition", "climax"]
    pov: str
    setting: Setting
    characters_present: List[str] = []
    conflicts: List[Conflict] = []
    turning_points: List[str] = []
    subplot_advancement: List[str] = []
    theme_expression: List[str] = []
    planned_word_count: int = 0
    actual_word_count: int = 0
    beats: List[Beat] = []

class CharacterFocus(BaseModel):
    pov: str
    present: List[str] = []
    arc_moments: List[str] = []

class Chapter(BaseModel):
    chapter_number: int
    title: str = ""
    act: int
    purpose: str
    plot_points: List[str] = []
    character_focus: CharacterFocus
    setting: Setting
    subplot_threads: List[str] = []
    themes: List[str] = []
    planned_word_count: int = 0
    actual_word_count: int = 0
    status: Literal["planned", "drafted", "revised", "final"] = "planned"
    scenes: List[Scene] = []

class Book(BaseModel):
    book_number: int
    title: str = ""
    premise: str
    themes: List[str] = []
    target_word_count: int = 100000
    current_word_count: int = 0
    status: Literal["planned", "outlined", "drafted", "complete"] = "planned"
    act_structure: dict[str, ActStructure] = {}
    character_arcs: List[CharacterArc] = []
    chapters: List[Chapter] = []

class Series(BaseModel):
    title: str
    premise: str
    themes: List[str] = []
    genre: str
    target_audience: str
    persistent_threads: List[str] = []
    lore: Lore
    books: List[Book] = []

class RevisionTask(BaseModel):
    priority: Literal["high", "medium", "low"]
    description: str
    status: Literal["pending", "completed"] = "pending"

class QAReport(BaseModel):
    qa_id: str
    timestamp: str
    scope: Literal["series", "book", "chapter", "scene", "beat"]
    target_id: str
    scores: dict[str, int]  # structure, pacing, character_arcs, theme_integration, consistency, overall
    major_issues: List[str] = []
    strengths: List[str] = []
    required_rewrites: List[str] = []
    revision_tasks: List[RevisionTask] = []
    approval: Literal["approved", "needs_revision"]
    reviewer_notes: str = ""

class RevisionHistory(BaseModel):
    timestamp: str
    agent: str
    scope: str
    changes_summary: str
    reason: str

class FictionProject(BaseModel):
    """Root schema for the entire project"""
    metadata: Metadata
    series: Series
    qa_reports: List[QAReport] = []
    revision_history: List[RevisionHistory] = []
```

---

## 3. Agent Specifications

### 3.1 Base Agent Interface

```python
from abc import ABC, abstractmethod
from typing import Optional
import hashlib
import json

class BaseAgent(ABC):
    def __init__(self, llm, temperature: float = 0.3, seed: Optional[int] = None):
        self.llm = llm
        self.temperature = temperature
        self.seed = seed
        self.agent_name = self.__class__.__name__
        self.prompt_version = "1.0"
    
    @abstractmethod
    def get_prompt(self) -> str:
        """Return the versioned prompt for this agent"""
        pass
    
    @abstractmethod
    def process(self, input_data: FictionProject) -> FictionProject:
        """Process input and return updated project"""
        pass
    
    def get_prompt_hash(self) -> str:
        """Generate hash of current prompt for versioning"""
        prompt = self.get_prompt()
        return hashlib.sha256(prompt.encode()).hexdigest()[:8]
    
    def invoke_llm(self, prompt: str, context: str) -> str:
        """Wrapper for LLM calls with standardized parameters"""
        full_prompt = f"{prompt}\n\nContext:\n{context}\n\nOutput (JSON only):"
        
        if self.seed:
            response = self.llm.invoke(
                full_prompt,
                temperature=self.temperature,
                seed=self.seed
            )
        else:
            response = self.llm.invoke(
                full_prompt,
                temperature=self.temperature
            )
        
        return response.content
```

### 3.2 Series Refiner Agent

```python
class SeriesRefinerAgent(BaseAgent):
    def get_prompt(self) -> str:
        return """You are a professional fiction series refiner.

Your task:
1. Read the provided series concept
2. Expand it into a complete series outline
3. Define universe principles and lore foundations
4. Create book slate with premises
5. Establish persistent threads across books

Output ONLY valid JSON matching the FictionProject schema.
Focus on series-level elements: series.title, series.premise, series.themes, series.lore, series.books (stubs only).

Version: 1.0"""
    
    def process(self, input_data: FictionProject) -> FictionProject:
        # Extract series concept
        context = f"""Series Title: {input_data.series.title}
Premise: {input_data.series.premise}
Genre: {input_data.series.genre}"""
        
        # Invoke LLM
        response = self.invoke_llm(self.get_prompt(), context)
        
        # Parse JSON response
        try:
            response_json = json.loads(response)
            # Update input_data with response
            # Implementation: merge response into input_data.series
            # Update metadata
            input_data.metadata.last_updated_by = self.agent_name
            input_data.metadata.processing_stage = "series"
            input_data.metadata.last_updated = [datetime.now](http://datetime.now)()
        except json.JSONDecodeError as e:
            raise ValueError(f"Agent returned invalid JSON: {e}")
        
        return input_data
```

### 3.3 Book Outliner Agent

```python
class BookOutlinerAgent(BaseAgent):
    def __init__(self, llm, book_number: int, **kwargs):
        super().__init__(llm, **kwargs)
        [self.book](http://self.book)_number = book_number
    
    def get_prompt(self) -> str:
        return """You are a professional fiction book outliner.

Your task:
1. Read the series context
2. Expand book {book_number} into a full 3-act structure
3. Define character arcs with transformations
4. Create chapter scaffold with word budgets
5. Set POV and tense inheritance flags

Output ONLY valid JSON matching the FictionProject schema.
Focus on the target book: series.books[{book_number}] with complete act_structure, character_arcs, and chapters (outlines only).

Version: 1.0"""
    
    def process(self, input_data: FictionProject) -> FictionProject:
        # Extract relevant context
        series_context = {
            "title": input_data.series.title,
            "premise": input_data.series.premise,
            "themes": input_data.series.themes,
            "lore": input_data.series.lore.dict()
        }
        
        book_context = input_data.series.books[[self.book](http://self.book)_number - 1].dict()
        
        context = f"""Series Context:\n{json.dumps(series_context, indent=2)}\n\nTarget Book:\n{json.dumps(book_context, indent=2)}"""
        
        # Invoke LLM
        response = self.invoke_llm(self.get_prompt(), context)
        
        # Parse and update
        try:
            response_json = json.loads(response)
            # Update book in input_data.series.books
            # Update metadata
            input_data.metadata.last_updated_by = self.agent_name
            input_data.metadata.processing_stage = "book"
            input_data.metadata.last_updated = [datetime.now](http://datetime.now)()
        except json.JSONDecodeError as e:
            raise ValueError(f"Agent returned invalid JSON: {e}")
        
        return input_data
```

### 3.4 Remaining Agents

Implement similar patterns for:

- **ChapterDeveloperAgent**: Expands chapters with scene scaffolds
- **SceneDeveloperAgent**: Breaks chapters into detailed scenes
- **BeatDeveloperAgent**: Creates beat-level breakdowns
- **QAAgent**: Validates structure and appends qa_reports
- **LoreMasterAgent**: Checks continuity and expands lore

---

## 4. Validation System

### 4.1 Schema Validator

```python
from pydantic import ValidationError
import json

class SchemaValidator:
    @staticmethod
    def validate(data: dict) -> tuple[bool, Optional[str]]:
        """
        Validate data against FictionProject schema.
        Returns: (is_valid, error_message)
        """
        try:
            FictionProject(**data)
            return (True, None)
        except ValidationError as e:
            return (False, str(e))
    
    @staticmethod
    def validate_stage(data: dict, stage: str) -> tuple[bool, Optional[str]]:
        """
        Validate data has required fields for a specific stage.
        """
        # Stage-specific validation logic
        if stage == "series":
            required = ["series.title", "series.premise", "series.books"]
        elif stage == "book":
            required = ["series.books[].act_structure", "series.books[].character_arcs"]
        # etc.
        
        # Check required fields exist
        for field in required:
            if not SchemaValidator._has_field(data, field):
                return (False, f"Missing required field: {field}")
        
        return (True, None)
    
    @staticmethod
    def _has_field(data: dict, path: str) -> bool:
        """Check if nested field exists in data"""
        keys = path.split('.')
        current = data
        for key in keys:
            if '[' in key:  # Handle array notation
                key = key.split('[')[0]
                if key not in current or not current[key]:
                    return False
                current = current[key][0]  # Check first element
            else:
                if key not in current:
                    return False
                current = current[key]
        return True
```

---

## 5. Pipeline Orchestration

### 5.1 Main Pipeline

```python
import os
import json
from datetime import datetime
from typing import Optional

class FictionPipeline:
    def __init__(self, project_id: str, output_dir: str = "output"):
        self.project_id = project_id
        self.output_dir = output_dir
        self.state_file = os.path.join(output_dir, f"{project_id}_state.json")
        self.validator = SchemaValidator()
        
        # Initialize LLMs
        self.structured_llm = self._init_structured_llm()
        self.creative_llm = self._init_creative_llm()
        
        # Initialize agents
        self.agents = {
            "series": SeriesRefinerAgent(self.structured_llm),
            "book": BookOutlinerAgent(self.structured_llm, book_number=1),
            "chapter": ChapterDeveloperAgent(self.structured_llm),
            "scene": SceneDeveloperAgent(self.structured_llm),
            "beat": BeatDeveloperAgent(self.structured_llm),
            "qa": QAAgent(self.creative_llm),
            "lore": LoreMasterAgent(self.creative_llm)
        }
    
    def _init_structured_llm(self):
        """Initialize local Ollama for structured tasks"""
        from langchain_community.llms import Ollama
        return Ollama(
            model="llama3.1:70b",
            temperature=0.3,
            format="json",
            base_url="http://localhost:11434"
        )
    
    def _init_creative_llm(self):
        """Initialize OpenRouter for creative tasks"""
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="anthropic/claude-3.7-sonnet",
            temperature=0.8,
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1"
        )
    
    def run(self, input_text: str, resume: bool = False) -> FictionProject:
        """
        Execute full pipeline from series concept to complete outline.
        """
        # Initialize or load state
        if resume and os.path.exists(self.state_file):
            project = self._load_state()
            print(f"Resuming from stage: {project.metadata.processing_stage}")
        else:
            project = self._initialize_project(input_text)
        
        # Define pipeline stages
        stages = ["series", "book", "chapter", "scene", "beat", "qa", "lore"]
        
        # Execute pipeline
        for stage in stages:
            if self._should_skip_stage(project, stage):
                continue
            
            print(f"\nExecuting stage: {stage}")
            project = self._execute_stage(project, stage)
            
            # Save checkpoint
            self._save_state(project)
        
        return project
    
    def _execute_stage(self, project: FictionProject, stage: str, max_retries: int = 3) -> FictionProject:
        """
        Execute a single stage with validation and retry logic.
        """
        agent = self.agents[stage]
        
        for attempt in range(max_retries):
            try:
                # Execute agent
                project = agent.process(project)
                
                # Validate output
                is_valid, error = self.validator.validate_stage(project.dict(), stage)
                
                if is_valid:
                    print(f"✓ Stage {stage} completed successfully")
                    return project
                else:
                    print(f"✗ Validation failed (attempt {attempt + 1}/{max_retries}): {error}")
                    # Add error feedback to next attempt
                    # Implementation: inject error into prompt context
            
            except Exception as e:
                print(f"✗ Agent error (attempt {attempt + 1}/{max_retries}): {str(e)}")
        
        raise RuntimeError(f"Stage {stage} failed after {max_retries} attempts")
    
    def _initialize_project(self, input_text: str) -> FictionProject:
        """Create initial project structure from input text"""
        # Parse input text for series concept
        # This is a simplified version - implement proper parsing
        lines = input_text.strip().split('\n')
        title = lines[0] if lines else "Untitled Series"
        premise = lines[1] if len(lines) > 1 else ""
        
        return FictionProject(
            metadata=Metadata(
                last_updated=[datetime.now](http://datetime.now)(),
                last_updated_by="Initializer",
                processing_stage="series",
                status="draft",
                project_id=self.project_id,
                iteration=1
            ),
            series=Series(
                title=title,
                premise=premise,
                themes=[],
                genre="",
                target_audience="",
                persistent_threads=[],
                lore=Lore(),
                books=[]
            )
        )
    
    def _save_state(self, project: FictionProject):
        """Save current state to disk"""
        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(project.dict(), f, indent=2, default=str)
    
    def _load_state(self) -> FictionProject:
        """Load state from disk"""
        with open(self.state_file, 'r') as f:
            data = json.load(f)
        return FictionProject(**data)
    
    def _should_skip_stage(self, project: FictionProject, stage: str) -> bool:
        """Determine if stage should be skipped based on current progress"""
        stage_order = ["series", "book", "chapter", "scene", "beat", "qa", "lore"]
        current_idx = stage_order.index(project.metadata.processing_stage)
        target_idx = stage_order.index(stage)
        return target_idx < current_idx
```

### 5.2 CLI Entry Point

```python
# [run.py](http://run.py)
import argparse
import sys
from pipeline import FictionPipeline

def main():
    parser = argparse.ArgumentParser(description="Fiction Generation Pipeline")
    parser.add_argument("--input", required=True, help="Input series concept file")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--project-id", required=True, help="Project identifier")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    
    args = parser.parse_args()
    
    # Read input
    with open(args.input, 'r') as f:
        input_text = [f.read](http://f.read)()
    
    # Execute pipeline
    try:
        pipeline = FictionPipeline(project_id=args.project_id, output_dir=args.output)
        result = [pipeline.run](http://pipeline.run)(input_text, resume=args.resume)
        
        print("\n✓ Pipeline completed successfully")
        print(f"Output saved to: {pipeline.state_file}")
        
    except Exception as e:
        print(f"\n✗ Pipeline failed: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## 6. Configuration

### 6.1 requirements.txt

```
langchain==0.1.0
langchain-community==0.1.0
langchain-openai==0.0.5
pydantic==2.5.0
python-dotenv==1.0.0
```

### 6.2 .env.example

```
OPENROUTER_API_KEY=your_key_here
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 7. Testing

### 7.1 Test Fixtures

```python
# tests/fixtures/minimal_series.txt
The Quantum Heist
A team of specialists must steal an impossible artifact from a time-locked vault.
```

### 7.2 Schema Tests

```python
# tests/test_[schema.py](http://schema.py)
import pytest
from models.schema import FictionProject, Metadata, Series, Lore
from datetime import datetime

def test_minimal_project():
    """Test that minimal valid project passes validation"""
    project = FictionProject(
        metadata=Metadata(
            last_updated=[datetime.now](http://datetime.now)(),
            last_updated_by="test",
            processing_stage="series",
            status="draft",
            project_id="test_001",
            iteration=1
        ),
        series=Series(
            title="Test Series",
            premise="Test premise",
            themes=[],
            genre="sci-fi",
            target_audience="adult",
            persistent_threads=[],
            lore=Lore(),
            books=[]
        )
    )
    
    assert project.metadata.project_id == "test_001"
    assert project.series.title == "Test Series"

def test_invalid_project():
    """Test that invalid data raises ValidationError"""
    with pytest.raises(Exception):
        FictionProject(
            metadata={"invalid": "data"},
            series={}
        )
```

---

## 8. Implementation Sequence

### Week 1: Foundation

1. Create project structure
2. Implement Pydantic models in `models/[schema.py](http://schema.py)`
3. Implement `SchemaValidator` in `validators/schema_[validator.py](http://validator.py)`
4. Write schema tests in `tests/test_[schema.py](http://schema.py)`
5. Set up Git repo with proper .gitignore

### Week 2: Minimal Pipeline

1. Implement `BaseAgent` in `agents/base_[agent.py](http://agent.py)`
2. Implement `SeriesRefinerAgent`
3. Implement `BookOutlinerAgent`
4. Create `FictionPipeline` with just Series → Book stages
5. Test with minimal fixture

### Week 3: Validation & Testing

1. Create test fixtures (minimal, standard, series)
2. Implement stage-specific validation
3. Add retry logic with error feedback
4. Measure variance across 3 runs

### Week 4: Full Pipeline

1. Implement remaining agents (Chapter, Scene, Beat, QA, Lore)
2. Add checkpointing and resume logic
3. Implement progress monitoring
4. Integration testing

---

## 9. Key Implementation Notes

### 9.1 Prompt Engineering

- Always include schema version in prompt
- Use few-shot examples for complex structures
- Inject validation errors into retry prompts
- Keep prompts under 2000 tokens

### 9.2 State Management

- Save after every successful agent run
- Use project_id as filename prefix
- Include iteration number in metadata
- Keep last 5 iterations as backups

### 9.3 Error Handling

- Catch JSON decode errors separately from validation errors
- Provide specific error messages (field name, expected type)
- Log all errors with timestamps
- Allow manual intervention via checkpoint editing

### 9.4 Performance

- Use Ollama for 80% of calls (local, fast, free)
- Reserve OpenRouter for QA and Lore (quality-critical)
- Batch scene processing where possible
- Cache lore lookups within a run

---

## 10. Success Criteria

✓ **Schema validation**: 100% of outputs pass Pydantic validation

✓ **Reproducibility**: Same input + seed → <5% variance in structure

✓ **Completeness**: All required fields populated at each stage

✓ **Error recovery**: Automatic retry with <3 attempts per stage

✓ **Performance**: Series → Book outline in <10 minutes

✓ **Resumability**: Can resume from any checkpoint without data loss

---

**Next Steps for Coding Agent**:

1. Set up Python virtual environment
2. Create project structure per Section 1.1
3. Implement Pydantic models from Section 2.1
4. Implement SchemaValidator from Section 4.1
5. Write tests from Section 7.2
6. Implement BaseAgent and SeriesRefinerAgent from Section 3
7. Create minimal pipeline from Section 5.1
8. Test with minimal fixture from Section 7.1

**Next Steps for Coding Agent**:

1. Set up Python virtual environment
2. Create project structure per Section 1.1
3. Implement Pydantic models from Section 2.1
4. Implement SchemaValidator from Section 4.1
5. Write tests from Section 7.2
6. Implement BaseAgent and SeriesRefinerAgent from Section 3
7. Create minimal pipeline from Section 5.1
8. Test with minimal fixture from Section 7.1

---

## 11. Prose Generator Agent (ADDENDUM)

**Note**: The Prose Generator Agent was initially omitted but is required for complete pipeline.

### 11.1 Agent Implementation

```python
class ProseGeneratorAgent(BaseAgent):
    def __init__(self, llm, **kwargs):
        # Use higher temperature for creative prose generation
        super().__init__(llm, temperature=0.8, **kwargs)
    
    def get_prompt(self) -> str:
        return """You are a professional fiction prose writer.

Your task:
1. Read the beat description and surrounding context
2. Generate prose matching the beat's emotional tone and purpose
3. Maintain POV, tense, and voice consistency
4. Respect character arcs and world-building
5. Target 200-800 words based on beat type

Output format:
{
  "prose": "Generated prose content here..."
}

NO commentary. ONLY prose.

Version: 1.0"""
    
    def process(self, input_data: FictionProject, book_idx: int, 
                chapter_idx: int, scene_idx: int, beat_idx: int) -> FictionProject:
        """Generate prose for a specific beat"""
        book = input_data.series.books[book_idx]
        chapter = book.chapters[chapter_idx]
        scene = chapter.scenes[scene_idx]
        beat = [scene.beats](http://scene.beats)[beat_idx]
        
        # Build context
        context = f"""
Beat Context:
- Book: {book.title}
- Chapter {chapter.chapter_number}: {chapter.title}
- Scene {scene.scene_number} POV: {scene.pov}
- Setting: {scene.setting.location}, {scene.setting.time}
- Scene Type: {scene.scene_type}

Current Beat #{beat.beat_number}:
- Description: {beat.description}
- Emotional Tone: {beat.emotional_tone}
- Actions: {', '.join(beat.character_actions)}
- Dialogue: {beat.dialogue_summary}

Previous Context (last 500 words):
{self._get_previous_prose(chapter, scene, beat_idx)}
"""
        
        # Invoke LLM
        response = self.invoke_llm(self.get_prompt(), context)
        
        try:
            response_json = json.loads(response)
            prose_content = response_json.get("prose", "")
            
            # Create Prose object
            beat.prose = Prose(
                content=prose_content,
                word_count=len(prose_content.split()),
                generated_timestamp=[datetime.now](http://datetime.now)().isoformat(),
                status="draft"
            )
            
            # Update word counts up the hierarchy
            scene.actual_word_count = sum(
                b.prose.word_count for b in [scene.beats](http://scene.beats) if b.prose
            )
            chapter.actual_word_count = sum(
                s.actual_word_count for s in chapter.scenes
            )
            book.current_word_count = sum(
                c.actual_word_count for c in book.chapters
            )
            
            # Update metadata
            input_data.metadata.last_updated_by = self.agent_name
            input_data.metadata.processing_stage = "prose"
            input_data.metadata.last_updated = [datetime.now](http://datetime.now)()
            
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Prose generation failed: {e}")
        
        return input_data
    
    def _get_previous_prose(self, chapter: Chapter, scene: Scene, 
                           current_beat_idx: int, word_limit: int = 500) -> str:
        """Extract previous prose for context continuity"""
        prose_chunks = []
        
        # Collect from previous beats in current scene
        for i in range(current_beat_idx):
            if [scene.beats](http://scene.beats)[i].prose:
                prose_chunks.append([scene.beats](http://scene.beats)[i].prose.content)
        
        # Combine and truncate to word limit
        full_text = " ".join(prose_chunks)
        words = full_text.split()
        
        if len(words) <= word_limit:
            return full_text
        
        return " ".join(words[-word_limit:])
```

### 11.2 Pipeline Integration

**Add to FictionPipeline.init()** agents dict:

```python
"prose": ProseGeneratorAgent(self.creative_llm)  # After beat, before QA
```

**Update pipeline stages list**:

```python
stages = ["series", "book", "chapter", "scene", "beat", "prose", "qa", "lore"]
```

**Update data flow diagram in Section 1.2**:

```
[Beat Developer Agent] → JSON v5
    ↓ (validate)
[Prose Generator Agent] → JSON v6 (beats with prose)
    ↓ (validate)
[QA Agent] → JSON v6 + qa_reports
```

### 11.3 Implementation Notes

**Processing Strategy**: Prose generation is the most expensive operation. Consider:

1. **Batch by scene**: Process all beats in a scene sequentially to maintain context
2. **Parallel scenes**: Process multiple scenes in parallel if memory allows
3. **Checkpoint frequency**: Save after each scene completes (not each beat)

**Context Management**:

- Always read 500 words of prior prose for continuity
- Pass scene-level POV/tense constraints explicitly
- Include character arc status at beat level

**Quality Control**:

- QA agent should validate prose against beat description
- Check for POV breaks, tense shifts, voice inconsistencies
- Verify emotional tone matches beat specification

### 11.4 Usage Example

```python
# In pipeline execution
if stage == "prose":
    # Process all beats in all scenes
    for book_idx, book in enumerate(project.series.books):
        for ch_idx, chapter in enumerate(book.chapters):
            for sc_idx, scene in enumerate(chapter.scenes):
                for bt_idx in range(len([scene.beats](http://scene.beats))):
                    project = agents["prose"].process(
                        project, book_idx, ch_idx, sc_idx, bt_idx
                    )
                # Save checkpoint after each scene
                _save_state(project)
```

**Cost Estimate** (using OpenRouter Claude):

- ~800 words/beat × 0.003¢/1K tokens = ~$0.002/beat
- 100K word book ≈ 125 beats = ~$0.25/book for prose generation

**Updated Success Criteria**:

- ✓ All beats have prose populated
- ✓ Prose maintains consistent POV/tense
- ✓ Word counts match targets (±10%)
- ✓ Emotional tone matches beat specifications

**Updated Success Criteria**:

- ✓ All beats have prose populated
- ✓ Prose maintains consistent POV/tense
- ✓ Word counts match targets (±10%)
- ✓ Emotional tone matches beat specifications

---

## 12. Fully Local Ollama Configuration (ADDENDUM)

**Note**: This section provides 100% local model recommendations, eliminating OpenRouter dependency.

### 12.1 Recommended Ollama Models

**Install commands**:

```bash
# Structured agents (70B for best quality, 32B for speed/memory trade-off)
ollama pull llama3.1:70b        # Best: structured output, reasoning
ollama pull qwen2.5:32b         # Fast alternative with good JSON

# Creative agents
ollama pull llama3.1:70b        # Use same model, higher temperature
ollama pull mixtral:8x7b        # Alternative: good creative output

# Embeddings (for future lore lookups)
ollama pull nomic-embed-text    # Fast, high-quality embeddings
```

### 12.2 Agent Model Configuration Table

| Agent | Model | Temperature | Seed | Format | Context Window | RAM Required | Rationale |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Series Refiner** | `llama3.1:70b` | 0.3 | 42 | `json` | 8192 | 48GB | Complex reasoning, multi-book planning |
| **Book Outliner** | `llama3.1:70b` | 0.3 | 42 | `json` | 8192 | 48GB | Structured acts, character arcs |
| **Chapter Developer** | `qwen2.5:32b` | 0.3 | 42 | `json` | 8192 | 24GB | Fast, excellent structured output |
| **Scene Developer** | `qwen2.5:32b` | 0.3 | 42 | `json` | 8192 | 24GB | Scene-level detail, good JSON |
| **Beat Developer** | `qwen2.5:32b` | 0.3 | 42 | `json` | 8192 | 24GB | Granular beats, fast iteration |
| **Prose Generator** | `llama3.1:70b` | 0.8 | None | `text` | 8192 | 48GB | Creative quality, narrative voice |
| **QA Agent** | `llama3.1:70b` | 0.5 | None | `json` | 8192 | 48GB | Critical analysis, reasoning |
| **Lore Master** | `qwen2.5:32b` | 0.4 | 42 | `json` | 8192 | 24GB | Consistency checking, fast |

### 12.3 Hardware Requirements

**Minimum specs by configuration**:

**Option A: High Quality (Recommended)**

- CPU: 16+ cores
- RAM: 64GB (allows 70B models)
- GPU: Optional but speeds up 2-5x (24GB+ VRAM)
- Disk: 100GB free (model storage)
- Speed: Series → Book outline in ~15 mins

**Option B: Fast/Memory-Constrained**

- CPU: 8+ cores
- RAM: 32GB (32B models only)
- GPU: Optional (12GB+ VRAM)
- Disk: 50GB free
- Speed: Series → Book outline in ~8 mins
- Trade-off: Use `qwen2.5:32b` for all agents

**Option C: Ultra-Fast (GPU Required)**

- CPU: 8+ cores
- RAM: 32GB
- GPU: 24GB+ VRAM (RTX 4090, A5000, etc.)
- Disk: 100GB free
- Speed: Series → Book outline in ~5 mins

### 12.4 Updated Pipeline Initialization

```python
class FictionPipeline:
    def __init__(self, project_id: str, output_dir: str = "output", 
                 mode: str = "quality"):
        self.project_id = project_id
        self.output_dir = output_dir
        self.mode = mode
        self.state_file = os.path.join(output_dir, f"{project_id}_state.json")
        self.validator = SchemaValidator()
        
        # Initialize models based on mode
        if mode == "quality":
            self.structured_llm = self._init_ollama("llama3.1:70b", temp=0.3, format="json")
            self.creative_llm = self._init_ollama("llama3.1:70b", temp=0.8)
            [self.fast](http://self.fast)_llm = self._init_ollama("qwen2.5:32b", temp=0.3, format="json")
        elif mode == "fast":
            self.structured_llm = self._init_ollama("qwen2.5:32b", temp=0.3, format="json")
            self.creative_llm = self._init_ollama("qwen2.5:32b", temp=0.8)
            [self.fast](http://self.fast)_llm = self.structured_llm
        
        # Initialize agents with appropriate models
        self.agents = {
            "series": SeriesRefinerAgent(self.structured_llm, seed=42),
            "book": BookOutlinerAgent(self.structured_llm, book_number=1, seed=42),
            "chapter": ChapterDeveloperAgent([self.fast](http://self.fast)_llm, seed=42),
            "scene": SceneDeveloperAgent([self.fast](http://self.fast)_llm, seed=42),
            "beat": BeatDeveloperAgent([self.fast](http://self.fast)_llm, seed=42),
            "prose": ProseGeneratorAgent(self.creative_llm),  # No seed for variety
            "qa": QAAgent(self.creative_llm),
            "lore": LoreMasterAgent([self.fast](http://self.fast)_llm, seed=42)
        }
    
    def _init_ollama(self, model: str, temp: float, format: str = None):
        """Initialize Ollama model with parameters"""
        from langchain_community.llms import Ollama
        
        kwargs = {
            "model": model,
            "temperature": temp,
            "base_url": "http://localhost:11434"
        }
        
        if format:
            kwargs["format"] = format
        
        return Ollama(**kwargs)
```

### 12.5 Model Selection Decision Tree

```
Start
  │
  ├─ Have 64GB+ RAM?
  │   ├─ YES → Use llama3.1:70b for structured + creative
  │   │         Estimated time: 15-20 mins for full outline
  │   │         Quality: Excellent
  │   │
  │   └─ NO → Have 32GB+ RAM?
  │       ├─ YES → Use qwen2.5:32b for all agents
  │       │         Estimated time: 8-12 mins for full outline
  │       │         Quality: Very good
  │       │
  │       └─ NO → Use qwen2.5:14b or llama3.2:8b
  │                 Estimated time: 15-25 mins for full outline
  │                 Quality: Acceptable for drafts
  │
  ├─ Have GPU (24GB+ VRAM)?
  │   └─ Speed boost: 2-5x faster
  │       Use same models, set num_gpu=1
```

### 12.6 Performance Comparison

| Configuration | Series→Book | +Chapters | +Scenes | +Beats | +Prose | Total Time | Cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **70B Quality** | 3 min | +5 min | +8 min | +10 min | +25 min | ~51 min | $0 |
| **32B Fast** | 1.5 min | +2.5 min | +4 min | +5 min | +12 min | ~25 min | $0 |
| **70B + GPU** | 40 sec | +1.5 min | +3 min | +4 min | +8 min | ~17 min | $0 |
| **32B + GPU** | 20 sec | +45 sec | +1.5 min | +2 min | +4 min | ~9 min | $0 |
| **Cloud (ref)** | 30 sec | +1 min | +2 min | +3 min | +5 min | ~11.5 min | $2-5 |

### 12.7 Quality vs Speed Trade-offs

**Use llama3.1:70b when**:

- First draft of series structure (reasoning matters)
- Complex character arcs and themes
- Prose generation (creative quality critical)
- Final QA pass (catch subtle issues)

**Use qwen2.5:32b when**:

- Iterating on outlines (speed > perfection)
- Chapter/scene/beat breakdown (structured tasks)
- Lore consistency checking (pattern matching)
- Multiple revision cycles

**Mixed strategy** (recommended):

- 70B for Series, Book, Prose, QA (~70% of quality)
- 32B for Chapter, Scene, Beat, Lore (~90% of speed)
- Best balance of quality and performance

### 12.8 Environment Variables

```bash
# .env for local-only setup
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_NUM_GPU=1              # Use GPU if available
OLLAMA_NUM_THREAD=8           # CPU threads (adjust to your cores)
PIPELINE_MODE=quality         # or "fast"
```

### 12.9 CLI Usage

```bash
# Quality mode (70B + 32B mix)
python [run.py](http://run.py) --input series.txt --project-id my-series --mode quality

# Fast mode (32B for everything)
python [run.py](http://run.py) --input series.txt --project-id my-series --mode fast

# Resume from checkpoint
python [run.py](http://run.py) --input series.txt --project-id my-series --resume

# Check model availability
ollama list
```

### 12.10 Troubleshooting Local Setup

**Out of memory errors**:

```bash
# Check Ollama memory usage
ollama ps

# Reduce model size
ollama pull qwen2.5:14b  # Instead of 32b

# Or use quantized versions
ollama pull llama3.1:70b-q4_0  # 4-bit quantization
```

**Slow generation**:

```bash
# Check if GPU is being used
ollama run llama3.1:70b --verbose

# Force GPU usage
export OLLAMA_NUM_GPU=1

# Reduce context window in prompts (< 4096 tokens)
```

**JSON parsing failures**:

```python
# Add explicit JSON schema to prompt
schema = {
    "type": "object",
    "properties": {
        "series": {"type": "object"},
        # ... schema definition
    }
}

prompt = f"{base_prompt}\n\nOutput JSON matching schema:\n{json.dumps(schema)}"
```

### 12.11 Cost & Privacy Benefits

**100% local advantages**:

- ✓ Zero API costs (save $2-5 per book)
- ✓ Complete privacy (content never leaves machine)
- ✓ No rate limits (run 24/7)
- ✓ Offline capable (no internet required)
- ✓ Consistent results (same models, same outputs)

**Trade-offs**:

- ✗ Hardware investment required (RAM/GPU)
- ✗ Slightly slower than cloud (unless GPU)
- ✗ Model quality 85-95% of GPT-4/Claude
- ✗ Manual model management (updates, disk space)

### 12.11 Cost & Privacy Benefits

**100% local advantages**:

- ✓ Zero API costs (save $2-5 per book)
- ✓ Complete privacy (content never leaves machine)
- ✓ No rate limits (run 24/7)
- ✓ Offline capable (no internet required)
- ✓ Consistent results (same models, same outputs)

**Trade-offs**:

- ✗ Hardware investment required (RAM/GPU)
- ✗ Slightly slower than cloud (unless GPU)
- ✗ Model quality 85-95% of GPT-4/Claude
- ✗ Manual model management (updates, disk space)

---

## 13. Post-Prose Editorial Pipeline (ADDENDUM)

**Purpose**: After prose generation, run a professional editorial workflow to ensure top-quality lore, plot logic, character consistency, and prose craft.

### 13.1 Editorial Workflow Overview

```
[Prose Complete] → JSON + export [manuscript.md](http://manuscript.md)
    ↓
=== DEVELOPMENTAL EDITING PHASE ===
    ↓
[Story Analyst] → Compare prose vs. Series Refiner outline
    ↓ (generates dev_report)
    ├─ Plot holes identified
    ├─ Character arc breaks
    ├─ Lore inconsistencies
    ├─ Pacing issues
    ├─ Theme drift
    └─ Structure problems
    ↓
[Consistency Validator] → Check lore/logic/continuity
    ↓ (generates consistency_report)
    ├─ Lore violations (world rules, magic systems, tech)
    ├─ Timeline conflicts
    ├─ Character behavior inconsistencies
    ├─ Setting/location errors
    └─ Plot logic gaps
    ↓
    ├─ PASS (minor issues) → continue
    └─ FAIL (major issues) → Developmental Editor
    ↓
[Developmental Editor] → Fix structure/plot/character issues
    ↓ (generates revised JSON + dev_[changes.md](http://changes.md))
    ├─ Rewrite scenes with plot holes
    ├─ Fix character arc breaks
    ├─ Resolve lore conflicts
    ├─ Adjust pacing
    ├─ Strengthen theme expression
    └─ Update metadata.status = "dev_revised"
    ↓
[Story Analyst] → Re-review (Round 2)
    ↓
    ├─ PASS → continue
    └─ FAIL → Developmental Editor (max 3 cycles)
    ↓
=== LINE EDITING PHASE ===
    ↓
[Line Editor] → Sentence-level craft
    ↓ (generates line_edited JSON + line_[changes.md](http://changes.md))
    ├─ Tighten prose (remove fluff)
    ├─ Fix awkward sentences
    ├─ Improve dialogue flow
    ├─ Enhance descriptions
    ├─ Fix POV/tense slips
    ├─ Polish voice consistency
    └─ Update metadata.status = "line_edited"
    ↓
[Final QA] → Approval gate
    ↓ (generates final_qa_report)
    ├─ All dev issues resolved?
    ├─ Lore/consistency clean?
    ├─ Prose craft acceptable?
    ├─ Word count on target?
    └─ Ready for publication?
    ↓
    ├─ APPROVED → Export final [manuscript.md](http://manuscript.md) + JSON
    └─ REJECTED → Back to appropriate phase
    ↓
[Export] → final_[manuscript.md](http://manuscript.md) + final_project.json
```

**Key principle**: Each phase has a **Review → Edit → Re-review** cycle. No phase advances until its reviewer approves.

### 13.2 Updated Schema (Editorial Extensions)

Add to `FictionProject` schema:

```python
class DevelopmentalIssue(BaseModel):
    issue_type: Literal["plot_hole", "character_break", "lore_conflict", 
                        "pacing", "theme_drift", "structure"]
    severity: Literal["critical", "major", "minor"]
    location: str  # book.chapter.scene.beat
    description: str
    suggested_fix: str
    status: Literal["open", "fixed", "deferred"] = "open"

class ConsistencyIssue(BaseModel):
    issue_type: Literal["lore_violation", "timeline_conflict", 
                        "character_inconsistency", "setting_error", "logic_gap"]
    severity: Literal["critical", "major", "minor"]
    location: str
    description: str
    conflicting_references: List[str] = []  # URLs to conflicting content
    resolution: str = ""
    status: Literal["open", "fixed", "deferred"] = "open"

class EditorialReport(BaseModel):
    report_id: str
    timestamp: str
    phase: Literal["developmental", "consistency", "line_editing", "final_qa"]
    reviewer_agent: str
    scope: str  # "series", "book", "chapter_range", etc.
    
    # Developmental
    developmental_issues: List[DevelopmentalIssue] = []
    
    # Consistency
    consistency_issues: List[ConsistencyIssue] = []
    
    # Line editing
    line_edit_changes: int = 0
    line_edit_summary: str = ""
    
    # Overall
    overall_score: int  # 1-10
    approval: Literal["approved", "needs_revision", "needs_rewrite"]
    reviewer_notes: str = ""
    next_steps: List[str] = []

class FictionProject(BaseModel):
    """Root schema - ADD THIS"""
    # ... existing fields ...
    editorial_reports: List[EditorialReport] = []
    editorial_status: Literal["draft", "dev_editing", "line_editing", 
                              "final_qa", "approved"] = "draft"
```

### 13.3 Story Analyst Agent

```python
class StoryAnalystAgent(BaseAgent):
    def __init__(self, llm, **kwargs):
        super().__init__(llm, temperature=0.4, **kwargs)
    
    def get_prompt(self) -> str:
        return """You are a professional story analyst and developmental editor.

Your task:
1. Read the Series Refiner outline (the original plan)
2. Read the completed prose
3. Compare prose execution vs. outline intent
4. Identify developmental issues:
   - Plot holes or unresolved threads
   - Character arc breaks (missing beats, inconsistent motivation)
   - Lore inconsistencies
   - Pacing problems (rushed or dragging)
   - Theme drift (themes not expressed in prose)
   - Structure issues (act breaks, chapter flow)

Output format (JSON):
{
  "developmental_issues": [
    {
      "issue_type": "plot_hole",
      "severity": "major",
      "location": "book_1.chapter_5.scene_2.beat_3",
      "description": "Character X learns about Y in Ch5, but acts as if they don't know Y in Ch7.",
      "suggested_fix": "Add a scene where X forgets Y due to trauma, or remove the Ch5 reveal."
    }
  ],
  "overall_score": 7,
  "approval": "needs_revision",
  "reviewer_notes": "Strong character work, but several plot threads unresolved.",
  "next_steps": ["Fix major plot holes in Act 2", "Strengthen theme expression in Act 3"]
}

Be specific. Reference exact locations. Suggest concrete fixes.

Version: 1.0"""
    
    def process(self, input_data: FictionProject) -> FictionProject:
        """Compare prose against original series outline"""
        # Extract series outline
        series_outline = {
            "title": input_data.series.title,
            "premise": input_data.series.premise,
            "themes": input_data.series.themes,
            "books": [{"title": b.title, "premise": b.premise, 
                       "character_arcs": b.character_arcs} 
                      for b in input_data.series.books]
        }
        
        # Extract prose samples (first 500 words per chapter for analysis)
        prose_samples = self._extract_prose_samples(input_data)
        
        context = f"""SERIES OUTLINE (from Series Refiner):
{json.dumps(series_outline, indent=2)}

PROSE SAMPLES:
{prose_samples}

Compare the prose execution against the outline. Identify issues."""
        
        response = self.invoke_llm(self.get_prompt(), context)
        report_data = json.loads(response)
        
        # Create editorial report
        report = EditorialReport(
            report_id=f"story_analyst_{[datetime.now](http://datetime.now)().isoformat()}",
            timestamp=[datetime.now](http://datetime.now)().isoformat(),
            phase="developmental",
            reviewer_agent=self.agent_name,
            scope="series",
            developmental_issues=[DevelopmentalIssue(**issue) 
                                  for issue in report_data.get("developmental_issues", [])],
            overall_score=report_data.get("overall_score", 5),
            approval=report_data.get("approval", "needs_revision"),
            reviewer_notes=report_data.get("reviewer_notes", ""),
            next_steps=report_data.get("next_steps", [])
        )
        
        input_data.editorial_reports.append(report)
        input_data.editorial_status = "dev_editing"
        
        return input_data
    
    def _extract_prose_samples(self, project: FictionProject, words_per_chapter: int = 500) -> str:
        """Extract prose samples for analysis (to keep context manageable)"""
        samples = []
        for book in project.series.books:
            for chapter in book.chapters:
                prose_words = []
                for scene in chapter.scenes:
                    for beat in [scene.beats](http://scene.beats):
                        if beat.prose and beat.prose.content:
                            prose_words.extend(beat.prose.content.split())
                            if len(prose_words) >= words_per_chapter:
                                break
                    if len(prose_words) >= words_per_chapter:
                        break
                
                sample = " ".join(prose_words[:words_per_chapter])
                samples.append(f"### {book.title} - Chapter {chapter.chapter_number}: {chapter.title}\n{sample}...")
        
        return "\n\n".join(samples)
```

### 13.4 Consistency Validator Agent

```python
class ConsistencyValidatorAgent(BaseAgent):
    def __init__(self, llm, **kwargs):
        super().__init__(llm, temperature=0.3, **kwargs)
    
    def get_prompt(self) -> str:
        return """You are a continuity and consistency expert.

Your task:
1. Read the series lore (world rules, magic/tech systems, character bios)
2. Read the completed prose
3. Identify consistency issues:
   - Lore violations (breaking established world rules)
   - Timeline conflicts (events out of order, age/date math errors)
   - Character behavior inconsistencies (contradicts established personality/skills)
   - Setting errors (location details change, impossible geography)
   - Plot logic gaps (cause-effect breaks, impossible actions)

Output format (JSON):
{
  "consistency_issues": [
    {
      "issue_type": "lore_violation",
      "severity": "critical",
      "location": "book_1.chapter_8.scene_1.beat_2",
      "description": "Character uses magic indoors, but series lore states magic only works outdoors.",
      "conflicting_references": ["[series.lore.world](http://series.lore.world)_elements[magic_system].rules[0]"],
      "resolution": "Either change scene to outdoors or establish indoor magic exception."
    }
  ],
  "overall_score": 8,
  "approval": "needs_revision"
}

Be forensic. Cite exact conflicting references.

Version: 1.0"""
    
    def process(self, input_data: FictionProject) -> FictionProject:
        """Validate consistency against lore"""
        # Extract lore
        lore = {
            "characters": [{"name": [c.name](http://c.name), "traits": c.traits, "relationships": c.relationships} 
                           for c in input_data.series.lore.characters],
            "locations": [{"name": [l.name](http://l.name), "description": l.description} 
                          for l in input_data.series.lore.locations],
            "world_elements": [{"name": [w.name](http://w.name), "type": w.type, "rules": w.rules} 
                               for w in input_[data.series.lore.world](http://data.series.lore.world)_elements]
        }
        
        # Extract prose for checking
        prose_samples = self._extract_prose_samples(input_data, words_per_chapter=1000)
        
        context = f"""SERIES LORE:
{json.dumps(lore, indent=2)}

PROSE TO CHECK:
{prose_samples}

Identify consistency issues. Cross-reference lore."""
        
        response = self.invoke_llm(self.get_prompt(), context)
        report_data = json.loads(response)
        
        # Create editorial report
        report = EditorialReport(
            report_id=f"consistency_{[datetime.now](http://datetime.now)().isoformat()}",
            timestamp=[datetime.now](http://datetime.now)().isoformat(),
            phase="consistency",
            reviewer_agent=self.agent_name,
            scope="series",
            consistency_issues=[ConsistencyIssue(**issue) 
                                for issue in report_data.get("consistency_issues", [])],
            overall_score=report_data.get("overall_score", 5),
            approval=report_data.get("approval", "needs_revision"),
            reviewer_notes=report_data.get("reviewer_notes", "")
        )
        
        input_data.editorial_reports.append(report)
        
        return input_data
```

### 13.5 Developmental Editor Agent

```python
class DevelopmentalEditorAgent(BaseAgent):
    def __init__(self, llm, **kwargs):
        super().__init__(llm, temperature=0.7, **kwargs)
    
    def get_prompt(self) -> str:
        return """You are a developmental editor who fixes story-level issues.

Your task:
1. Read the editorial reports (developmental + consistency issues)
2. Read the prose at flagged locations
3. Rewrite prose to fix issues:
   - Fill plot holes
   - Repair character arc breaks
   - Resolve lore conflicts
   - Fix pacing (expand rushed beats, tighten dragging ones)
   - Strengthen theme expression
   - Repair logic gaps

Output format (JSON):
{
  "revised_beats": [
    {
      "location": "book_1.chapter_5.scene_2.beat_3",
      "issue_fixed": "plot_hole",
      "original_prose": "...",
      "revised_prose": "...",
      "change_summary": "Added dialogue where X questions Y's motives, resolving later plot hole."
    }
  ]
}

Maintain voice, POV, tense. Only change what's necessary to fix issues.

Version: 1.0"""
    
    def process(self, input_data: FictionProject) -> FictionProject:
        """Fix developmental issues"""
        # Get latest editorial reports
        dev_report = next((r for r in reversed(input_data.editorial_reports) 
                           if r.phase == "developmental"), None)
        consistency_report = next((r for r in reversed(input_data.editorial_reports) 
                                   if r.phase == "consistency"), None)
        
        if not dev_report and not consistency_report:
            return input_data  # Nothing to fix
        
        # Collect all open issues
        issues = []
        if dev_report:
            issues.extend([i for i in dev_report.developmental_issues if i.status == "open"])
        if consistency_report:
            issues.extend([i for i in consistency_report.consistency_issues if i.status == "open"])
        
        # Process each issue
        for issue in issues:
            # Parse location (e.g., "book_1.chapter_5.scene_2.beat_3")
            location_parts = issue.location.split(".")
            # ... navigate to beat, get prose, rewrite, update ...
            # Implementation: call LLM with issue context + prose, get revision
        
        # Update status
        input_data.metadata.status = "dev_revised"
        input_data.revision_history.append(RevisionHistory(
            timestamp=[datetime.now](http://datetime.now)().isoformat(),
            agent=self.agent_name,
            scope="series",
            changes_summary=f"Fixed {len(issues)} developmental/consistency issues",
            reason="Editorial review"
        ))
        
        return input_data
```

### 13.6 Line Editor Agent

```python
class LineEditorAgent(BaseAgent):
    def __init__(self, llm, **kwargs):
        super().__init__(llm, temperature=0.6, **kwargs)
    
    def get_prompt(self) -> str:
        return """You are a line editor who polishes prose at the sentence level.

Your task:
1. Read prose beat-by-beat
2. Improve craft:
   - Tighten (remove unnecessary words, filter words, adverbs)
   - Fix awkward phrasing
   - Improve dialogue naturalness
   - Enhance sensory descriptions
   - Fix POV breaks, tense slips
   - Polish voice consistency
   - Improve rhythm and flow

DO NOT change:
- Plot events
- Character actions
- Dialogue meaning
- Scene structure

Output format (JSON):
{
  "line_edits": [
    {
      "location": "book_1.chapter_1.scene_1.beat_1",
      "before": "He walked slowly into the room and looked around carefully.",
      "after": "He entered the room, scanning for threats.",
      "change_type": "tighten",
      "rationale": "Removed filter words (slowly, carefully), made action more active."
    }
  ],
  "total_changes": 147,
  "summary": "Tightened prose, removed 847 words of fluff, improved dialogue flow in Act 2."
}

Version: 1.0"""
    
    def process(self, input_data: FictionProject) -> FictionProject:
        """Line edit all prose"""
        total_changes = 0
        
        for book in input_data.series.books:
            for chapter in book.chapters:
                for scene in chapter.scenes:
                    for beat in [scene.beats](http://scene.beats):
                        if beat.prose and beat.prose.content:
                            # Line edit this beat
                            context = f"""BEAT CONTEXT:
Scene: {scene.title} ({scene.scene_type})
POV: {scene.pov}
Emotional tone: {beat.emotional_tone}

PROSE TO EDIT:
{beat.prose.content}

Line edit this prose. Improve craft without changing meaning."""
                            
                            response = self.invoke_llm(self.get_prompt(), context)
                            edit_data = json.loads(response)
                            
                            # Update prose
                            if edit_data.get("line_edits"):
                                beat.prose.content = edit_data["line_edits"][0]["after"]
                                beat.prose.draft_version += 1
                                total_changes += 1
        
        # Create report
        report = EditorialReport(
            report_id=f"line_edit_{[datetime.now](http://datetime.now)().isoformat()}",
            timestamp=[datetime.now](http://datetime.now)().isoformat(),
            phase="line_editing",
            reviewer_agent=self.agent_name,
            scope="series",
            line_edit_changes=total_changes,
            line_edit_summary=f"Line edited {total_changes} beats",
            overall_score=9,
            approval="approved"
        )
        
        input_data.editorial_reports.append(report)
        input_data.editorial_status = "line_editing"
        input_data.metadata.status = "line_edited"
        
        return input_data
```

### 13.7 Manuscript Export

```python
class ManuscriptExporter:
    @staticmethod
    def export_markdown(project: FictionProject, output_path: str):
        """Export complete manuscript as Markdown"""
        lines = []
        
        # Title page
        lines.append(f"# {project.series.title}\n")
        lines.append(f"*{project.series.premise}*\n")
        lines.append("---\n")
        
        # For each book
        for book in project.series.books:
            lines.append(f"\n# {book.title}\n")
            
            # For each chapter
            for chapter in book.chapters:
                lines.append(f"\n## Chapter {chapter.chapter_number}: {chapter.title}\n")
                
                # For each scene
                for scene in chapter.scenes:
                    # Concatenate all beat prose
                    scene_prose = []
                    for beat in [scene.beats](http://scene.beats):
                        if beat.prose and beat.prose.content:
                            scene_prose.append(beat.prose.content)
                    
                    lines.append("\n".join(scene_prose))
                    lines.append("\n")  # Scene break
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    @staticmethod
    def export_json(project: FictionProject, output_path: str):
        """Export complete project JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(project.model_dump_json(indent=2))
```

### 13.8 Updated Pipeline with Editorial Phase

```python
class FictionPipeline:
    def run_editorial_phase(self, project: FictionProject) -> FictionProject:
        """Run complete editorial workflow"""
        
        print("=== DEVELOPMENTAL EDITING PHASE ===")
        
        # Round 1: Analysis
        print("Running Story Analyst...")
        project = self.agents["story_analyst"].process(project)
        
        print("Running Consistency Validator...")
        project = self.agents["consistency_validator"].process(project)
        
        # Check if we need developmental edits
        latest_report = project.editorial_reports[-1]
        if latest_report.approval != "approved":
            print("Developmental issues found. Running Developmental Editor...")
            
            max_cycles = 3
            for cycle in range(max_cycles):
                project = self.agents["developmental_editor"].process(project)
                
                # Re-analyze
                project = self.agents["story_analyst"].process(project)
                project = self.agents["consistency_validator"].process(project)
                
                # Check approval
                latest_report = project.editorial_reports[-1]
                if latest_report.approval == "approved":
                    print(f"Developmental editing approved after {cycle + 1} cycles")
                    break
        
        print("\n=== LINE EDITING PHASE ===")
        print("Running Line Editor...")
        project = self.agents["line_editor"].process(project)
        
        print("\n=== FINAL QA ===")
        print("Running Final QA...")
        project = self.agents["qa"].process(project)
        
        final_report = project.editorial_reports[-1]
        if final_report.approval == "approved":
            project.editorial_status = "approved"
            print("\n✓ Editorial process complete. Manuscript approved.")
        else:
            print("\n✗ Final QA rejected. Review editorial reports.")
        
        return project
    
    def export_manuscript(self, project: FictionProject, output_dir: str):
        """Export final manuscript"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Export Markdown
        md_path = os.path.join(output_dir, f"{project.metadata.project_id}_[manuscript.md](http://manuscript.md)")
        ManuscriptExporter.export_markdown(project, md_path)
        print(f"✓ Exported: {md_path}")
        
        # Export JSON
        json_path = os.path.join(output_dir, f"{project.metadata.project_id}_final.json")
        ManuscriptExporter.export_json(project, json_path)
        print(f"✓ Exported: {json_path}")
```

### 13.9 Complete Workflow with Editorial

```bash
# Full pipeline: Series → Book → ... → Prose → Editorial → Export

python [main.py](http://main.py) \
  --input series_concept.txt \
  --stages all \
  --run-editorial \
  --export manuscript_output/
```

### 13.10 Editorial Success Criteria

✓ **Developmental approval**: All plot holes, character breaks, lore conflicts resolved

✓ **Consistency validation**: Zero critical lore violations, timeline conflicts

✓ **Line editing**: Prose tightened, voice consistent, craft improved

✓ **Final QA approval**: Manuscript ready for publication

✓ **Export**: Clean .md manuscript + complete .json project file

**Estimated time** (editorial phase):

- Story Analyst: ~5 min
- Consistency Validator: ~3 min
- Developmental Editor: ~15-30 min (depending on issues)
- Re-analysis: ~5 min
- Line Editor: ~20-40 min
- Final QA: ~3 min
- **Total**: ~50-90 min for editorial phase (after prose complete)

### 13.10 Editorial Success Criteria

✓ **Developmental approval**: All plot holes, character breaks, lore conflicts resolved

✓ **Consistency validation**: Zero critical lore violations, timeline conflicts

✓ **Line editing**: Prose tightened, voice consistent, craft improved

✓ **Final QA approval**: Manuscript ready for publication

✓ **Export**: Clean .md manuscript + complete .json project file

**Estimated time** (editorial phase):

- Story Analyst: ~5 min
- Consistency Validator: ~3 min
- Developmental Editor: ~15-30 min (depending on issues)
- Re-analysis: ~5 min
- Line Editor: ~20-40 min
- Final QA: ~3 min
- **Total**: ~50-90 min for editorial phase (after prose complete)

---

## 14. Lore Management with Pinecone (ADDENDUM)

**Purpose**: Every agent needs access to established lore. Use Pinecone to store, retrieve, and validate lore consistency. Detect new lore creation and trigger structured lore entry creation.

### 14.1 Lore Lifecycle

```
[Series Refiner] → Creates initial lore
    ↓
[Store in Pinecone] → Vector embeddings of all lore entries
    ↓
[Each Content Agent] → Queries Pinecone for relevant lore
    ↓ (uses lore in generation)
    ↓
[Lore Master] → After each stage
    ↓
    ├─ Check for lore breaks (contradicts existing lore)
    └─ Check for new lore (introduces new elements)
    ↓
[New Lore Detected?]
    ├─ YES → Trigger Lore Creation Agent
    │         ↓
    │         Creates structured lore entry
    │         ↓
    │         Stores in Pinecone + updates FictionProject.series.lore
    │         ↓
    │         Returns to workflow
    └─ NO → Continue to next stage
```

### 14.2 Pinecone Integration

```python
from pinecone import Pinecone, ServerlessSpec
from langchain_community.embeddings import OllamaEmbeddings
import json
from typing import List, Dict

class LoreVectorStore:
    def __init__(self, api_key: str, index_name: str = "fiction-lore"):
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name
        
        # Use Ollama for embeddings (local, free)
        self.embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url="http://localhost:11434"
        )
        
        # Create index if doesn't exist
        if index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=index_name,
                dimension=768,  # nomic-embed-text dimension
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
        
        self.index = self.pc.Index(index_name)
    
    def store_lore_entry(self, lore_id: str, lore_type: str, 
                         name: str, content: Dict, project_id: str):
        """Store a single lore entry"""
        # Create text representation for embedding
        text = self._lore_to_text(lore_type, name, content)
        
        # Generate embedding
        embedding = self.embeddings.embed_query(text)
        
        # Store in Pinecone
        self.index.upsert(vectors=[{
            "id": lore_id,
            "values": embedding,
            "metadata": {
                "project_id": project_id,
                "lore_type": lore_type,  # character, location, world_element
                "name": name,
                "content": json.dumps(content)
            }
        }])
    
    def store_all_lore(self, project: FictionProject):
        """Store all lore from a FictionProject"""
        project_id = project.metadata.project_id
        
        # Store characters
        for char in project.series.lore.characters:
            lore_id = f"{project_id}_char_{[char.name](http://char.name).lower().replace(' ', '_')}"
            [self.store](http://self.store)_lore_entry(
                lore_id=lore_id,
                lore_type="character",
                name=[char.name](http://char.name),
                content=char.model_dump(),
                project_id=project_id
            )
        
        # Store locations
        for loc in project.series.lore.locations:
            lore_id = f"{project_id}_loc_{[loc.name](http://loc.name).lower().replace(' ', '_')}"
            [self.store](http://self.store)_lore_entry(
                lore_id=lore_id,
                lore_type="location",
                name=[loc.name](http://loc.name),
                content=loc.model_dump(),
                project_id=project_id
            )
        
        # Store world elements
        for elem in [project.series.lore.world](http://project.series.lore.world)_elements:
            lore_id = f"{project_id}_elem_{[elem.name](http://elem.name).lower().replace(' ', '_')}"
            [self.store](http://self.store)_lore_entry(
                lore_id=lore_id,
                lore_type="world_element",
                name=[elem.name](http://elem.name),
                content=elem.model_dump(),
                project_id=project_id
            )
    
    def query_lore(self, query: str, project_id: str, 
                   top_k: int = 10, lore_type: str = None) -> List[Dict]:
        """Query relevant lore entries"""
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)
        
        # Build filter
        filter_dict = {"project_id": project_id}
        if lore_type:
            filter_dict["lore_type"] = lore_type
        
        # Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            filter=filter_dict,
            include_metadata=True
        )
        
        # Parse results
        lore_entries = []
        for match in results.matches:
            lore_entries.append({
                "id": [match.id](http://match.id),
                "score": match.score,
                "lore_type": match.metadata["lore_type"],
                "name": match.metadata["name"],
                "content": json.loads(match.metadata["content"])
            })
        
        return lore_entries
    
    def _lore_to_text(self, lore_type: str, name: str, content: Dict) -> str:
        """Convert lore entry to text for embedding"""
        if lore_type == "character":
            return f"""Character: {name}
Role: {content.get('role', '')}
Description: {content.get('description', '')}
Traits: {', '.join(content.get('traits', []))}
Relationships: {', '.join(content.get('relationships', []))}"""
        
        elif lore_type == "location":
            return f"""Location: {name}
Description: {content.get('description', '')}
Significance: {content.get('significance', '')}"""
        
        elif lore_type == "world_element":
            return f"""World Element: {name}
Type: {content.get('type', '')}
Description: {content.get('description', '')}
Rules: {'; '.join(content.get('rules', []))}"""
        
        return f"{lore_type}: {name}\n{json.dumps(content)}"
```

### 14.3 Lore-Aware Agent Base Class

Update `BaseAgent` to query lore before generation:

```python
class BaseAgent(ABC):
    def __init__(self, llm, lore_store: LoreVectorStore = None, 
                 temperature: float = 0.3, seed: Optional[int] = None):
        self.llm = llm
        self.lore_store = lore_store
        self.temperature = temperature
        self.seed = seed
        self.agent_name = self.__class__.__name__
        self.prompt_version = "1.0"
    
    def get_relevant_lore(self, context: str, project_id: str, 
                          top_k: int = 10) -> str:
        """Query Pinecone for relevant lore given context"""
        if not self.lore_store:
            return ""
        
        lore_entries = self.lore_store.query_lore(
            query=context,
            project_id=project_id,
            top_k=top_k
        )
        
        # Format lore for prompt
        lore_text = "### ESTABLISHED LORE:\n\n"
        for entry in lore_entries:
            lore_text += f"**{entry['lore_type'].title()}: {entry['name']}**\n"
            lore_text += f"{json.dumps(entry['content'], indent=2)}\n\n"
        
        return lore_text
    
    def invoke_llm_with_lore(self, prompt: str, context: str, 
                             project_id: str) -> str:
        """Wrapper for LLM calls with lore context"""
        # Get relevant lore
        lore_context = self.get_relevant_lore(context, project_id)
        
        # Build full prompt
        full_prompt = f"""{prompt}

{lore_context}

Context:
{context}

Output (JSON only):"""
        
        if self.seed:
            response = self.llm.invoke(
                full_prompt,
                temperature=self.temperature,
                seed=self.seed
            )
        else:
            response = self.llm.invoke(
                full_prompt,
                temperature=self.temperature
            )
        
        return response.content
```

### 14.4 Lore Master with Break Detection

Enhanced `LoreMasterAgent` to detect lore breaks AND new lore:

```python
class LoreMasterAgent(BaseAgent):
    def get_prompt(self) -> str:
        return """You are a lore continuity expert.

Your task:
1. Read the established lore (provided below)
2. Read the generated content
3. Identify:
   - LORE BREAKS: Content contradicts established lore
   - NEW LORE: Content introduces new elements not in established lore

Output format (JSON):
{
  "lore_breaks": [
    {
      "location": "book_1.chapter_3.scene_1",
      "description": "Character uses teleportation, but lore states teleportation is impossible.",
      "conflicting_lore": "world_elements/ftl_travel"
    }
  ],
  "new_lore_detected": [
    {
      "lore_type": "world_element",
      "name": "Quantum Resonance Field",
      "description": "Energy field mentioned in scene that enables FTL communication",
      "requires_formal_entry": true
    }
  ],
  "approval": "needs_revision"
}

Version: 1.0"""
    
    def process(self, input_data: FictionProject) -> FictionProject:
        """Check lore consistency and detect new lore"""
        project_id = input_data.metadata.project_id
        
        # Get content to check (vary by stage)
        content_sample = self._extract_content_for_stage(input_data)
        
        # Get all relevant lore
        lore_context = self.get_relevant_lore(content_sample, project_id, top_k=50)
        
        context = f"""Content to check:
{content_sample}"""
        
        response = self.invoke_llm_with_lore(
            self.get_prompt(), 
            context, 
            project_id
        )
        
        result = json.loads(response)
        
        # If new lore detected, trigger creation
        if result.get("new_lore_detected"):
            for new_lore in result["new_lore_detected"]:
                if new_lore.get("requires_formal_entry"):
                    self._create_lore_entry(input_data, new_lore)
        
        # Update metadata
        input_data.metadata.last_updated_by = self.agent_name
        
        # Determine approval
        if result.get("lore_breaks"):
            input_data.metadata.status = "needs_revision"
            return input_data
        
        input_data.metadata.status = "approved"
        return input_data
    
    def _create_lore_entry(self, project: FictionProject, new_lore: Dict):
        """Trigger Lore Creation Agent to formalize new lore"""
        lore_creator = LoreCreationAgent(self.llm, self.lore_store)
        lore_creator.create_and_store(project, new_lore)
```

### 14.5 Lore Creation Agent

New agent to formalize newly discovered lore:

```python
class LoreCreationAgent(BaseAgent):
    def get_prompt(self) -> str:
        return """You are a lore architect who formalizes new lore entries.

Your task:
1. Read the detected new lore (name, description, context)
2. Create a complete, structured lore entry
3. Define rules, relationships, and constraints

Output format depends on lore_type:

For world_element:
{
  "name": "Quantum Resonance Field",
  "type": "technology",
  "description": "...",
  "rules": [
    "Only works in vacuum",
    "Requires exotic matter generators",
    "Limited to 1000 light-year range"
  ]
}

For character:
{
  "name": "...",
  "role": "...",
  "description": "...",
  "traits": [...],
  "relationships": [...]
}

For location:
{
  "name": "...",
  "description": "...",
  "significance": "..."
}

Version: 1.0"""
    
    def create_and_store(self, project: FictionProject, new_lore: Dict):
        """Create formal lore entry and store in Pinecone + project"""
        lore_type = new_lore["lore_type"]
        name = new_lore["name"]
        description = new_lore["description"]
        
        context = f"""New {lore_type} detected:
Name: {name}
Description: {description}

Series context:
Title: {project.series.title}
Genre: {project.series.genre}
Themes: {', '.join(project.series.themes)}

Formalize this lore entry with complete details."""
        
        response = self.invoke_llm(self.get_prompt(), context)
        lore_data = json.loads(response)
        
        # Add to project
        if lore_type == "character":
            project.series.lore.characters.append(Character(**lore_data))
        elif lore_type == "location":
            project.series.lore.locations.append(Location(**lore_data))
        elif lore_type == "world_element":
            [project.series.lore.world](http://project.series.lore.world)_elements.append(WorldElement(**lore_data))
        
        # Store in Pinecone
        if self.lore_store:
            lore_id = f"{project.metadata.project_id}_{lore_type}_{name.lower().replace(' ', '_')}"
            self.lore_[store.store](http://store.store)_lore_entry(
                lore_id=lore_id,
                lore_type=lore_type,
                name=name,
                content=lore_data,
                project_id=project.metadata.project_id
            )
        
        # Log creation
        project.revision_history.append(RevisionHistory(
            timestamp=[datetime.now](http://datetime.now)().isoformat(),
            agent=self.agent_name,
            scope=lore_type,
            changes_summary=f"Created new {lore_type}: {name}",
            reason="Detected during content generation"
        ))
```

### 14.6 Pipeline Integration

Update `FictionPipeline` to use lore store:

```python
class FictionPipeline:
    def __init__(self, project_id: str, output_dir: str = "output",
                 pinecone_api_key: str = None):
        self.project_id = project_id
        self.output_dir = output_dir
        
        # Initialize lore store
        self.lore_store = None
        if pinecone_api_key:
            self.lore_store = LoreVectorStore(
                api_key=pinecone_api_key,
                index_name=f"lore_{project_id}"
            )
        
        # Initialize LLMs
        self.structured_llm = self._init_structured_llm()
        self.creative_llm = self._init_creative_llm()
        
        # Initialize agents WITH lore store
        self.agents = {
            "series": SeriesRefinerAgent(self.structured_llm, self.lore_store),
            "book": BookOutlinerAgent(self.structured_llm, self.lore_store),
            "chapter": ChapterDeveloperAgent(self.structured_llm, self.lore_store),
            "scene": SceneDeveloperAgent(self.structured_llm, self.lore_store),
            "beat": BeatDeveloperAgent(self.structured_llm, self.lore_store),
            "prose": ProseGeneratorAgent(self.creative_llm, self.lore_store),
            "qa": QAAgent(self.creative_llm, self.lore_store),
            "lore": LoreMasterAgent(self.creative_llm, self.lore_store),
            "lore_creator": LoreCreationAgent(self.creative_llm, self.lore_store)
        }
    
    def run(self, input_text: str) -> FictionProject:
        """Run complete pipeline with lore management"""
        # ... existing pipeline code ...
        
        # After Series Refiner completes, store initial lore in Pinecone
        if self.lore_store:
            print("Storing initial lore in Pinecone...")
            self.lore_[store.store](http://store.store)_all_lore(project)
        
        # ... continue with rest of pipeline ...
        
        # After each stage, Lore Master checks for breaks and new lore
        # New lore is automatically created and stored
        
        return project
```

### 14.7 Environment Configuration

Add to `.env`:

```bash
PINECONE_API_KEY=your_pinecone_api_key_here
OLLAMA_BASE_URL=http://localhost:11434
```

### 14.8 Lore Query Examples

```python
# During prose generation, query relevant lore
lore_context = lore_store.query_lore(
    query="Tell me about the protagonist's combat abilities and weapons",
    project_id="fannec_records",
    top_k=5
)

# Query specific lore type
tech_lore = lore_store.query_lore(
    query="FTL travel systems",
    project_id="fannec_records",
    lore_type="world_element",
    top_k=10
)

# Query for character relationships
char_lore = lore_store.query_lore(
    query="Who are Robert Fannec's allies and enemies?",
    project_id="fannec_records",
    lore_type="character",
    top_k=20
)
```

### 14.9 Lore Break Example Flow

```
[Prose Generator] → Generates scene where character teleports
    ↓
[Lore Master] → Queries Pinecone for "teleportation" lore
    ↓
    Finds: world_element/ftl_travel: "Teleportation is impossible; only FTL travel exists"
    ↓
    Detects lore break!
    ↓
    Returns FAIL with feedback: "Character cannot teleport per established lore"
    ↓
[Prose Generator] → Retries with feedback, uses FTL ship instead
```

### 14.10 New Lore Example Flow

```
[Prose Generator] → Mentions "Auryl overtone authentication"
    ↓
[Lore Master] → Queries Pinecone for "Auryl overtone"
    ↓
    No matches found → NEW LORE DETECTED
    ↓
[Lore Creation Agent] → Creates formal entry
    {
      "name": "Auryl Overtone Authentication",
      "type": "technology",
      "description": "Biometric security system using harmonic frequencies",
      "rules": [
        "Unique to each Auryl individual",
        "Cannot be faked or replicated",
        "Valid for legal testimony"
      ]
    }
    ↓
[Store in Pinecone + FictionProject.series.lore]
    ↓
Continue workflow with new lore available to all future stages
```

### 14.11 Success Criteria

✓ **Lore storage**: All lore entries stored in Pinecone with embeddings

✓ **Lore retrieval**: Agents query relevant lore before generation

✓ **Break detection**: Contradictions caught and flagged for revision

✓ **New lore creation**: Automatically formalized and stored

✓ **Consistency**: Zero lore breaks in final manuscript

✓ **Completeness**: All mentioned world elements have formal lore entries