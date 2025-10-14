"""
Reset Pinecone Index - Delete and recreate with correct dimensions

Use this if you get dimension mismatch errors.
"""

import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

def reset_index(index_name: str):
    """Delete and recreate Pinecone index with correct dimension"""

    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("❌ Error: PINECONE_API_KEY not set in environment")
        return

    try:
        pc = Pinecone(api_key=api_key)

        # Check if index exists
        existing_indexes = pc.list_indexes().names()

        if index_name in existing_indexes:
            print(f"🗑️  Deleting existing index: {index_name}")
            pc.delete_index(index_name)
            print(f"✅ Index deleted successfully")
        else:
            print(f"ℹ️  Index '{index_name}' does not exist (nothing to delete)")

        print(f"\n✅ Done! The index will be recreated with correct dimensions on next run.")
        print(f"   Default: 384 dimensions (all-MiniLM-L6-v2)")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        index_name = sys.argv[1]
    else:
        # Get from user input
        index_name = input("Enter index name to reset (e.g., fiction-lore-myproject): ").strip()

    if not index_name:
        print("❌ Error: Index name required")
        sys.exit(1)

    print(f"\n⚠️  WARNING: This will DELETE the Pinecone index '{index_name}'")
    print(f"   All stored lore embeddings will be lost.")
    print(f"   The index will be recreated from your project JSON on next run.\n")

    confirm = input(f"Type 'DELETE' to confirm: ").strip()

    if confirm == "DELETE":
        reset_index(index_name)
    else:
        print("❌ Cancelled")
