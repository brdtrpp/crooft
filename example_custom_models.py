"""
Example: Using custom model configurations
"""

from datetime import datetime
from models.schema import FictionProject, Metadata, Series, Lore
from pipeline import FictionPipeline

# Create a simple test project
project = FictionProject(
    metadata=Metadata(
        last_updated=datetime.now(),
        last_updated_by="CustomModelTest",
        processing_stage="series",
        status="draft",
        project_id="custom_model_test",
        iteration=1
    ),
    series=Series(
        title="The AI Revolution",
        premise="In 2045, an AI gains consciousness and must decide humanity's fate.",
        genre="science fiction",
        target_audience="adult",
        themes=[],
        persistent_threads=[],
        lore=Lore(),
        books=[]
    )
)

print("=" * 60)
print("CUSTOM MODEL CONFIGURATION EXAMPLES")
print("=" * 60)

# Example 1: Use a preset
print("\n\n=== Example 1: Using 'creative' preset ===")
pipeline_creative = FictionPipeline(
    project_id="test_creative",
    output_dir="output_creative",
    preset="creative"  # Maximum creativity across all stages
)

# Example 2: Use 'cost_optimized' preset
print("\n\n=== Example 2: Using 'cost_optimized' preset ===")
pipeline_cheap = FictionPipeline(
    project_id="test_cheap",
    output_dir="output_cheap",
    preset="cost_optimized"  # Uses Haiku for most stages
)

# Example 3: Custom configuration
print("\n\n=== Example 3: Custom per-agent configuration ===")
custom_config = {
    "prose": {
        "model": "anthropic/claude-3-opus",  # Best model for prose
        "temperature": 0.95,  # Maximum creativity
        "max_tokens": 3000
    },
    "qa": {
        "model": "openai/gpt-4",  # Different provider for QA
        "temperature": 0.4
    },
    "series": {
        "temperature": 0.2  # Very structured series planning
    }
    # Other agents will use defaults
}

pipeline_custom = FictionPipeline(
    project_id="test_custom",
    output_dir="output_custom",
    model_config=custom_config
)

print("\n\n=== Example 4: Premium configuration ===")
pipeline_premium = FictionPipeline(
    project_id="test_premium",
    output_dir="output_premium",
    preset="premium"  # Claude Opus for everything
)

print("\n\n=== Example 5: Precise/Consistent configuration ===")
pipeline_precise = FictionPipeline(
    project_id="test_precise",
    output_dir="output_precise",
    preset="precise"  # Low temperatures for maximum consistency
)

print("\n\n" + "=" * 60)
print("Configuration examples complete!")
print("To actually run a pipeline, uncomment one of the lines below:")
print("=" * 60)

# Uncomment to run:
# final = pipeline_creative.run(project)
# final = pipeline_cheap.run(project)
# final = pipeline_custom.run(project)
# final = pipeline_premium.run(project)
# final = pipeline_precise.run(project)
