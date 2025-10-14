"""
Simple test example to demonstrate the pipeline
"""

from datetime import datetime
from models.schema import FictionProject, Metadata, Series, Lore
from pipeline import FictionPipeline

# Create a simple test project
project = FictionProject(
    metadata=Metadata(
        last_updated=datetime.now(),
        last_updated_by="Test",
        processing_stage="series",
        status="draft",
        project_id="quantum_heist_test",
        iteration=1
    ),
    series=Series(
        title="The Quantum Heist",
        premise="A team of specialists must steal an impossible artifact from a time-locked vault.",
        genre="science fiction",
        target_audience="adult",
        themes=[],
        persistent_threads=[],
        lore=Lore(),
        books=[]
    )
)

print("=" * 60)
print("FICTION PIPELINE TEST")
print("=" * 60)
print(f"Project: {project.series.title}")
print(f"Premise: {project.series.premise}")
print("=" * 60)

# Initialize pipeline
pipeline = FictionPipeline(
    project_id="quantum_heist_test",
    output_dir="output_test"
)

# Run pipeline
try:
    print("\nStarting pipeline...")
    final_project = pipeline.run(project)

    print("\n✓ Pipeline completed successfully!")
    print(f"Books generated: {len(final_project.series.books)}")

    if final_project.series.books:
        book = final_project.series.books[0]
        print(f"Chapters in Book 1: {len(book.chapters)}")

        total_scenes = sum(len(ch.scenes) for ch in book.chapters)
        print(f"Total scenes: {total_scenes}")

        total_beats = sum(
            len(scene.beats)
            for ch in book.chapters
            for scene in ch.scenes
        )
        print(f"Total beats: {total_beats}")

        print(f"Word count: {book.current_word_count}")

    # Export manuscript
    pipeline.export_manuscript(final_project, "manuscripts_test")

except Exception as e:
    print(f"\n✗ Pipeline failed: {e}")
    import traceback
    traceback.print_exc()
