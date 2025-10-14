"""
Cleanup Pinecone Indexes - Delete all except specified index
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

def cleanup_indexes(keep_index_name=None):
    """Delete all Pinecone indexes (or all except the specified one if keep_index_name is set)"""

    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("❌ Error: PINECONE_API_KEY not set in environment")
        return

    try:
        pc = Pinecone(api_key=api_key)

        # List all indexes
        existing_indexes = pc.list_indexes().names()

        print(f"📋 Found {len(existing_indexes)} indexes:")
        for idx in existing_indexes:
            print(f"   - {idx}")

        # Determine which to delete
        if keep_index_name:
            to_delete = [idx for idx in existing_indexes if idx != keep_index_name]
            if not to_delete:
                print(f"\n✅ No indexes to delete (only {keep_index_name} exists or no indexes found)")
                return
            print(f"\n✅ Will KEEP:")
            if keep_index_name in existing_indexes:
                print(f"   - {keep_index_name}")
            else:
                print(f"   ⚠️  WARNING: {keep_index_name} does not exist!")
        else:
            to_delete = existing_indexes
            if not to_delete:
                print(f"\n✅ No indexes to delete")
                return
            print(f"\n⚠️  Will delete ALL indexes!")

        print(f"\n🗑️  Will DELETE the following {len(to_delete)} indexes:")
        for idx in to_delete:
            print(f"   - {idx}")

        # Confirm deletion
        confirm = input(f"\nType 'DELETE' to confirm deletion of {len(to_delete)} indexes: ")

        if confirm != "DELETE":
            print("❌ Aborted - no indexes were deleted")
            return

        # Delete indexes
        print("\n🗑️  Deleting indexes...")
        for idx in to_delete:
            try:
                pc.delete_index(idx)
                print(f"   ✓ Deleted: {idx}")
            except Exception as e:
                print(f"   ✗ Failed to delete {idx}: {e}")

        print(f"\n✅ Cleanup complete!")

        # List remaining indexes
        remaining = pc.list_indexes().names()
        print(f"\n📋 Remaining indexes ({len(remaining)}):")
        for idx in remaining:
            print(f"   - {idx}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Delete all indexes to start fresh
    cleanup_indexes(keep_index_name=None)  # Set to None to delete ALL indexes
