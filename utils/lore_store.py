"""
Lore Vector Store - Pinecone integration for lore management
"""

import os
from typing import List, Dict, Optional
import hashlib
import json
from pinecone import Pinecone, ServerlessSpec
from models.schema import FictionProject, Character, Location, WorldElement


class LoreVectorStore:
    """Manages lore storage and retrieval using Pinecone vector database"""

    def __init__(self, api_key: Optional[str] = None, index_name: str = "fiction-lore", openrouter_key: Optional[str] = None, namespace: str = "default"):
        """
        Initialize Pinecone lore store

        Args:
            api_key: Pinecone API key (or use PINECONE_API_KEY env var)
            index_name: Name of Pinecone index (shared across projects)
            openrouter_key: OpenRouter API key for embeddings
            namespace: Project-specific namespace to isolate data
        """
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.index_name = index_name
        self.namespace = namespace
        self.dimension = 384  # sentence-transformers/all-MiniLM-L6-v2 produces 384 dimensions
        self.openrouter_key = openrouter_key or os.getenv("OPENROUTER_API_KEY")

        if not self.api_key:
            print("⚠️  Warning: PINECONE_API_KEY not set. Lore vector store disabled.")
            self.enabled = False
            return

        self.enabled = True

        try:
            # Initialize Pinecone
            self.pc = Pinecone(api_key=self.api_key)

            # Use a shared index for all projects to avoid hitting free tier limits
            existing_indexes = self.pc.list_indexes().names()

            # Strategy: Use a single shared index for all projects with namespaces for isolation
            shared_index_name = "fiction-lore-shared"

            if index_name == "fiction-lore":
                # User wants shared behavior - use the shared index
                index_name = shared_index_name
                if index_name in existing_indexes:
                    print(f"♻️  Using shared index: {index_name} with namespace: {self.namespace}")
            # else: user specified custom index name, use it as-is

            if index_name not in existing_indexes:
                # Create new shared index with correct dimension
                print(f"Creating new Pinecone index: {index_name} (dimension: {self.dimension})")
                print(f"  Using namespace: {self.namespace} (projects will be isolated by namespace)")
                self.pc.create_index(
                    name=index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
            else:
                # Check dimension of existing index
                print(f"✓ Using existing Pinecone index: {index_name}, namespace: {self.namespace}")
                index_info = self.pc.describe_index(index_name)
                existing_dimension = index_info.dimension

                if existing_dimension != self.dimension:
                    print(f"⚠️  WARNING: Existing index '{index_name}' has dimension {existing_dimension}, but embedding model produces {self.dimension}")
                    print(f"    Option 1: Delete the index at https://app.pinecone.io/ and restart")
                    print(f"    Option 2: Using dimension {existing_dimension} with different embedding model")
                    print(f"    → Attempting to use existing dimension...")
                    self.dimension = existing_dimension

                    # Switch to a model that matches the existing dimension
                    if existing_dimension == 1024:
                        print(f"    → Switching to model compatible with 1024 dimensions")
                        # Will use a different model in _get_embedding

            self.index = self.pc.Index(index_name)
            print(f"✓ Lore vector store initialized: {index_name} (dimension: {self.dimension})")

        except Exception as e:
            print(f"⚠️  Warning: Failed to initialize Pinecone: {e}")
            print(f"    Error type: {type(e).__name__}")
            import traceback
            print(f"    Traceback: {traceback.format_exc()}")
            self.enabled = False

    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using sentence-transformers via local model"""
        try:
            # Use sentence-transformers locally (no API key needed)
            from sentence_transformers import SentenceTransformer

            if not hasattr(self, '_embedding_model'):
                print("📦 Loading embedding model (one-time setup)...")

                # Choose model based on required dimension
                if self.dimension == 384:
                    model_name = 'sentence-transformers/all-MiniLM-L6-v2'  # 384 dimensions
                    print(f"    Using model: {model_name} (384 dimensions)")
                elif self.dimension == 768:
                    model_name = 'sentence-transformers/all-mpnet-base-v2'  # 768 dimensions
                    print(f"    Using model: {model_name} (768 dimensions)")
                elif self.dimension == 1024:
                    model_name = 'sentence-transformers/all-MiniLM-L12-v2'  # Actually 384, need padding
                    print(f"    Using model: {model_name} with zero-padding to 1024")
                    self._needs_padding = True
                else:
                    model_name = 'sentence-transformers/all-MiniLM-L6-v2'
                    print(f"    Using default model: {model_name} (384 dimensions)")

                self._embedding_model = SentenceTransformer(model_name)
                self._needs_padding = getattr(self, '_needs_padding', False)

            embedding = self._embedding_model.encode(text).tolist()

            # Pad with zeros if needed
            if self._needs_padding and len(embedding) < self.dimension:
                padding = [0.0] * (self.dimension - len(embedding))
                embedding.extend(padding)
                print(f"    Padded embedding from {len(embedding) - len(padding)} to {len(embedding)} dimensions")

            return embedding
        except ImportError:
            print(f"⚠️  sentence-transformers not installed. Install with: pip install sentence-transformers")
            print(f"    Falling back to zero vectors (lore won't be searchable)")
            return [0.0] * self.dimension
        except Exception as e:
            print(f"⚠️  Embedding generation failed: {e}")
            import traceback
            traceback.print_exc()
            return [0.0] * self.dimension

    def _create_lore_id(self, lore_type: str, name: str, project_id: str) -> str:
        """Create unique ID for lore entry"""
        unique_str = f"{project_id}_{lore_type}_{name}"
        return hashlib.md5(unique_str.encode()).hexdigest()

    def store_all_lore(self, project: FictionProject):
        """Store all lore from project into Pinecone"""
        if not self.enabled:
            print(f"⚠️  Lore storage skipped - vector store not enabled")
            return

        project_id = project.metadata.project_id
        lore = project.series.lore
        vectors = []

        print(f"📚 Storing lore for project: {project_id}")
        print(f"   Characters: {len(lore.characters)}")
        print(f"   Locations: {len(lore.locations)}")
        print(f"   World Elements: {len(lore.world_elements)}")

        # Store characters
        for char in lore.characters:
            text = f"Character: {char.name}\nRole: {char.role}\nDescription: {char.description}\nTraits: {', '.join(char.traits)}"

            # Convert relationships to JSON-serializable format
            relationships_data = []
            for rel in char.relationships:
                if isinstance(rel, str):
                    relationships_data.append(rel)
                elif isinstance(rel, dict):
                    # Already a dict
                    relationships_data.append(rel)
                elif hasattr(rel, 'name') and hasattr(rel, 'type'):
                    # Relationship object - convert to dict
                    relationships_data.append({"name": rel.name, "type": rel.type})
                elif hasattr(rel, 'model_dump'):
                    # Pydantic v2 object
                    relationships_data.append(rel.model_dump())
                elif hasattr(rel, 'dict'):
                    # Pydantic v1 object
                    relationships_data.append(rel.dict())
                else:
                    # Fallback: convert to string
                    relationships_data.append(str(rel))

            # Create content dict with safe serialization
            try:
                content_dict = {
                    "description": char.description,
                    "traits": char.traits,
                    "relationships": relationships_data
                }
                content_json = json.dumps(content_dict)
            except TypeError as e:
                print(f"⚠️  Error serializing character {char.name}: {e}")
                print(f"    Relationships data: {relationships_data}")
                print(f"    Relationships types: {[type(r).__name__ for r in relationships_data]}")
                # Try with string conversion fallback
                content_json = json.dumps({
                    "description": char.description,
                    "traits": char.traits,
                    "relationships": [str(r) for r in relationships_data]
                })

            vectors.append({
                "id": self._create_lore_id("character", char.name, project_id),
                "values": self._get_embedding(text),
                "metadata": {
                    "project_id": project_id,
                    "lore_type": "character",
                    "name": char.name,
                    "role": char.role,
                    "content": content_json
                }
            })

        # Store locations
        for loc in lore.locations:
            text = f"Location: {loc.name}\nDescription: {loc.description}\nSignificance: {loc.significance}"

            vectors.append({
                "id": self._create_lore_id("location", loc.name, project_id),
                "values": self._get_embedding(text),
                "metadata": {
                    "project_id": project_id,
                    "lore_type": "location",
                    "name": loc.name,
                    "content": json.dumps({
                        "description": loc.description,
                        "significance": loc.significance
                    })
                }
            })

        # Store world elements
        for elem in lore.world_elements:
            text = f"World Element: {elem.name}\nType: {elem.type}\nDescription: {elem.description}\nRules: {', '.join(elem.rules)}"

            vectors.append({
                "id": self._create_lore_id("world_element", elem.name, project_id),
                "values": self._get_embedding(text),
                "metadata": {
                    "project_id": project_id,
                    "lore_type": "world_element",
                    "name": elem.name,
                    "element_type": elem.type,
                    "content": json.dumps({
                        "description": elem.description,
                        "rules": elem.rules
                    })
                }
            })

        # Upsert to Pinecone
        if vectors:
            try:
                self.index.upsert(vectors=vectors, namespace=self.namespace)
                print(f"✓ Stored {len(vectors)} lore entries in vector database")
            except Exception as e:
                print(f"⚠️  Failed to store lore: {e}")

    def query_lore(self, query: str, project_id: str, top_k: int = 10) -> List[Dict]:
        """
        Query relevant lore entries

        Args:
            query: Search query
            project_id: Project identifier
            top_k: Number of results to return

        Returns:
            List of lore entries with metadata
        """
        if not self.enabled:
            return []

        try:
            # Generate embedding for query
            query_embedding = self._get_embedding(query)

            # Query Pinecone
            results = self.index.query(
                namespace=self.namespace,
                vector=query_embedding,
                filter={"project_id": {"$eq": project_id}},
                top_k=top_k,
                include_metadata=True
            )

            # Format results
            lore_entries = []
            for match in results.matches:
                lore_entries.append({
                    "lore_type": match.metadata.get("lore_type"),
                    "name": match.metadata.get("name"),
                    "content": json.loads(match.metadata.get("content", "{}")),
                    "score": match.score
                })

            return lore_entries

        except Exception as e:
            print(f"⚠️  Lore query failed: {e}")
            return []

    def delete_project_lore(self, project_id: str):
        """Delete all lore for a project"""
        if not self.enabled:
            return

        try:
            self.index.delete(filter={"project_id": {"$eq": project_id}}, namespace=self.namespace)
            print(f"✓ Deleted all lore for project: {project_id}")
        except Exception as e:
            print(f"⚠️  Failed to delete lore: {e}")
