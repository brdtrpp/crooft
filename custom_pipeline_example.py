"""
Example: Custom Pipeline with Per-Agent Model Configuration

This shows how to create a pipeline with custom models for each agent.
Use this when you need more control than the presets provide.
"""

from datetime import datetime
from pipeline import FictionPipeline
from models.schema import FictionProject, Metadata, Series, Lore

# Define your custom model configuration
custom_config = {
    # Use GPT-4 for series planning (structured thinking)
    "series": {
        "model": "openai/gpt-4-turbo",
        "temperature": 0.3,
        "max_tokens": 4000
    },

    # Use Claude Sonnet for book outlining (balanced)
    "book": {
        "model": "anthropic/claude-3.5-sonnet",
        "temperature": 0.3,
        "max_tokens": 4000
    },

    # Use Claude Sonnet for chapter/scene/beat development
    "chapter": {
        "model": "anthropic/claude-3.5-sonnet",
        "temperature": 0.4,
        "max_tokens": 3000
    },

    "scene": {
        "model": "anthropic/claude-3.5-sonnet",
        "temperature": 0.5,
        "max_tokens": 2000
    },

    "beat": {
        "model": "anthropic/claude-3.5-sonnet",
        "temperature": 0.3,
        "max_tokens": 1000
    },

    # Use Claude Opus for prose (best quality)
    "prose": {
        "model": "anthropic/claude-3-opus",
        "temperature": 0.95,  # Maximum creativity for prose
        "max_tokens": 2000,
        "frequency_penalty": 0.3,  # Reduce repetition
        "presence_penalty": 0.2    # Encourage variety
    },

    # Use GPT-4 for QA (different perspective)
    "qa": {
        "model": "openai/gpt-4",
        "temperature": 0.5,
        "max_tokens": 2000
    },

    # Use Claude Sonnet for lore validation
    "lore": {
        "model": "anthropic/claude-3.5-sonnet",
        "temperature": 0.4,
        "max_tokens": 2000
    }
}

# Create your project
project = FictionProject(
    metadata=Metadata(
        last_updated=datetime.now(),
        last_updated_by="CustomPipeline",
        processing_stage="series",
        status="draft",
        project_id="custom_model_test",
        iteration=1
    ),
    series=Series(
        title="The Quantum Enigma",
        premise="A physicist discovers a parallel universe where her choices led to different outcomes.",
        genre="science fiction",
        target_audience="adult",
        themes=["identity", "choice", "reality"],
        persistent_threads=[],
        lore=Lore(),
        books=[]
    )
)

# Initialize pipeline with custom config
print("Initializing pipeline with custom model configuration...")
print("=" * 60)

pipeline = FictionPipeline(
    project_id="custom_model_test",
    output_dir="output",
    use_lore_db=True,  # Enable Pinecone lore database
    model_config=custom_config  # Use custom config instead of preset
)

print("\nConfiguration loaded successfully!")
print("Models assigned per agent (shown in output above)")
print("=" * 60)

# Run the pipeline
print("\nReady to run pipeline with custom models.")
print("Uncomment the line below to execute:")
print("# final = pipeline.run(project)")

# Uncomment to actually run:
# final = pipeline.run(project)
# pipeline.export_manuscript(final, "manuscripts")
