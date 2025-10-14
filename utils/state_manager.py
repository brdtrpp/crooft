"""
State Manager - Handles saving and loading project state/checkpoints
"""

import os
import json
from datetime import datetime
from models.schema import FictionProject


class StateManager:
    """Manages project state persistence and checkpointing"""

    def __init__(self, output_dir: str = "output"):
        """
        Initialize state manager

        Args:
            output_dir: Directory to save state files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def save_state(self, project: FictionProject, checkpoint_name: str = None):
        """
        Save project state to disk

        Args:
            project: FictionProject to save
            checkpoint_name: Optional specific checkpoint name (e.g., "chapter_5")

        Creates two files:
        1. {project_id}_state.json - Latest state (overwritten each time)
        2. {project_id}_v{iteration}_{checkpoint}.json - Versioned checkpoint
        """
        project_id = project.metadata.project_id
        iteration = project.metadata.iteration

        # Create timestamped checkpoint name if not provided
        if checkpoint_name is None:
            checkpoint_name = project.metadata.processing_stage

        # Save main state file (overwrite)
        state_file = os.path.join(self.output_dir, f"{project_id}_state.json")
        self._write_json(state_file, project)

        # Save versioned checkpoint (keep all versions)
        version_file = os.path.join(
            self.output_dir,
            f"{project_id}_v{iteration}_{checkpoint_name}.json"
        )
        self._write_json(version_file, project)

        print(f"[OK] Saved state: {checkpoint_name}")
        return version_file

    def load_state(self, project_id: str) -> FictionProject:
        """
        Load project state from disk

        Args:
            project_id: Project identifier

        Returns:
            FictionProject instance
        """
        state_file = os.path.join(self.output_dir, f"{project_id}_state.json")

        if not os.path.exists(state_file):
            raise FileNotFoundError(f"State file not found: {state_file}")

        with open(state_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert string dates back to datetime
        if 'metadata' in data and 'last_updated' in data['metadata']:
            data['metadata']['last_updated'] = datetime.fromisoformat(
                data['metadata']['last_updated']
            )

        return FictionProject(**data)

    def checkpoint_exists(self, project_id: str) -> bool:
        """Check if state file exists for project"""
        state_file = os.path.join(self.output_dir, f"{project_id}_state.json")
        return os.path.exists(state_file)

    def list_checkpoints(self, project_id: str) -> list:
        """
        List all checkpoints for a project

        Returns:
            List of checkpoint filenames
        """
        checkpoints = []
        for filename in os.listdir(self.output_dir):
            if filename.startswith(f"{project_id}_v") and filename.endswith('.json'):
                checkpoints.append(filename)

        return sorted(checkpoints)

    def _write_json(self, filepath: str, project: FictionProject):
        """Helper to write JSON with proper serialization"""
        from models.schema import Relationship

        with open(filepath, 'w', encoding='utf-8') as f:
            # Use model_dump() for Pydantic v2 with mode='json' for proper serialization
            try:
                if hasattr(project, 'model_dump'):
                    data = project.model_dump(mode='json')
                else:
                    # Fallback for Pydantic v1
                    data = project.dict()
            except Exception as e:
                print(f"⚠️  Error during model_dump: {e}")
                print(f"    Trying with mode='python' and manual conversion...")
                if hasattr(project, 'model_dump'):
                    data = project.model_dump(mode='python')
                else:
                    data = project.dict()
                print(f"    Success with python mode")

            # Deep conversion of any remaining Relationship objects
            def convert_relationships_recursive(obj):
                """Recursively convert Relationship objects to dicts"""
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        obj[key] = convert_relationships_recursive(value)
                    return obj
                elif isinstance(obj, list):
                    return [convert_relationships_recursive(item) for item in obj]
                elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'Relationship':
                    # Convert Relationship object to dict
                    return {"name": obj.name, "type": obj.type}
                else:
                    return obj

            data = convert_relationships_recursive(data)

            # Custom serializer for datetime and other objects
            def default_serializer(obj):
                if hasattr(obj, 'isoformat'):  # datetime objects
                    return obj.isoformat()
                elif isinstance(obj, Relationship):  # Relationship objects
                    return {"name": obj.name, "type": obj.type}
                elif hasattr(obj, '__dict__'):  # Any object with __dict__
                    return obj.__dict__
                return str(obj)

            json.dump(data, f, indent=2, default=default_serializer)
