"""
CLI Entry Point for Fiction Generation Pipeline
"""

import argparse
import sys
from pipeline import FictionPipeline, create_project_from_concept


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Fiction Generation Pipeline - AI-powered novel creation"
    )

    parser.add_argument(
        "--input",
        type=str,
        help="Input file with series concept (format: Title\\nPremise\\nGenre)"
    )

    parser.add_argument(
        "--project-id",
        type=str,
        required=True,
        help="Unique project identifier"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Output directory for checkpoints (default: output/)"
    )

    parser.add_argument(
        "--manuscript-dir",
        type=str,
        default="manuscripts",
        help="Output directory for final manuscript (default: manuscripts/)"
    )

    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenRouter API key (or set OPENROUTER_API_KEY env var)"
    )

    parser.add_argument(
        "--num-books",
        type=int,
        default=3,
        help="Number of books in the series (default: 3)"
    )

    parser.add_argument(
        "--chapters-per-book",
        type=int,
        default=15,
        help="Target number of chapters per book (default: 15)"
    )

    parser.add_argument(
        "--target-word-count",
        type=int,
        default=100000,
        help="Target word count per book (default: 100,000)"
    )

    parser.add_argument(
        "--preset",
        type=str,
        choices=[
            "balanced",
            "creative",
            "precise",
            "cost_optimized",
            "premium",
            "balanced_nsfw",
            "creative_nsfw",
            "precise_nsfw",
            "cost_optimized_nsfw",
            "premium_nsfw"
        ],
        help="Model configuration preset. NSFW presets use uncensored models for mature content."
    )

    parser.add_argument(
        "--scenes-per-chapter",
        type=int,
        default=3,
        help="Target number of scenes per chapter (default: 3)"
    )

    args = parser.parse_args()

    try:
        # Read input concept
        if args.input:
            with open(args.input, 'r', encoding='utf-8') as f:
                concept = f.read()
        else:
            # Interactive input
            print("Enter series concept (Title on line 1, Premise on line 2, Genre on line 3):")
            print("Press Ctrl+D (Unix) or Ctrl+Z (Windows) when done.")
            concept = sys.stdin.read()

        # Create initial project
        print(f"\nInitializing project: {args.project_id}")
        project = create_project_from_concept(concept, args.project_id)

        print(f"Series: {project.series.title}")
        print(f"Premise: {project.series.premise}")
        print(f"Genre: {project.series.genre}")
        print(f"\nGeneration Settings:")
        print(f"  Books: {args.num_books}")
        print(f"  Chapters per book: {args.chapters_per_book}")
        print(f"  Scenes per chapter: {args.scenes_per_chapter}")
        print(f"  Target word count per book: {args.target_word_count:,}")
        if args.preset:
            print(f"  Model preset: {args.preset}")

        # Initialize pipeline
        pipeline = FictionPipeline(
            project_id=args.project_id,
            output_dir=args.output,
            openrouter_api_key=args.api_key,
            preset=args.preset,
            requirements={
                "num_books": args.num_books,
                "chapters_per_book": args.chapters_per_book,
                "target_word_count": args.target_word_count,
                "target_scenes_per_chapter": args.scenes_per_chapter,
                "min_scenes_per_chapter": max(1, args.scenes_per_chapter - 1),
                "max_scenes_per_chapter": args.scenes_per_chapter + 2
            }
        )

        # Run pipeline
        final_project = pipeline.run(project)

        # Export manuscript
        pipeline.export_manuscript(final_project, args.manuscript_dir)

        print("\n✓ Complete! Check output files:")
        print(f"  - Checkpoints: {args.output}/{args.project_id}_*.json")
        print(f"  - Manuscript: {args.manuscript_dir}/{args.project_id}_manuscript.md")

    except FileNotFoundError as e:
        print(f"Error: Input file not found - {e}", file=sys.stderr)
        sys.exit(1)

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(130)

    except Exception as e:
        print(f"Error: Unexpected error - {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
