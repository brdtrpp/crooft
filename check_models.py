#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check available models on OpenRouter and test model IDs
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

def check_openrouter_models(search_term=None):
    """Check available models on OpenRouter"""
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not found in environment")
        return

    print("Fetching available models from OpenRouter...\n")

    response = requests.get(
        "https://openrouter.ai/api/v1/models",
        headers={
            "Authorization": f"Bearer {api_key}"
        }
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return

    models = response.json().get("data", [])

    # Filter by search term if provided
    if search_term:
        models = [m for m in models if search_term.lower() in m.get("id", "").lower()]
        print(f"📊 Found {len(models)} models matching '{search_term}':\n")
    else:
        print(f"📊 Total models available: {len(models)}\n")

    # Popular uncensored/NSFW models to check
    nsfw_models = [
        "sao10k/l3-euryale-70b",
        "sao10k/l3.1-euryale-70b",
        "sao10k/l3.3-70b-euryale-v2.2",
        "sao10k/l3-lunaris-8b",
        "lizpreciatior/lzlv-70b-fp16-hf",
        "nousresearch/hermes-3-llama-3.1-405b",
        "undi95/toppy-m-7b",
        "gryphe/mythomax-l2-13b",
        "neversleep/llama-3-lumimaid-70b",
        "sophosympatheia/midnight-rose-70b"
    ]

    if not search_term:
        print("Checking popular NSFW/uncensored models:\n")

        available_nsfw = []
        for model_id in nsfw_models:
            found = any(m.get("id") == model_id for m in models)
            status = "[AVAILABLE]" if found else "[NOT FOUND]"
            print(f"{status} {model_id}")
            if found:
                available_nsfw.append(model_id)

        print(f"\nAvailable NSFW models: {len(available_nsfw)}/{len(nsfw_models)}")

        if available_nsfw:
            print("\nAvailable NSFW models for use:")
            for model in available_nsfw:
                print(f"   - {model}")
    else:
        # Show filtered results
        for model in models[:20]:  # Limit to 20 results
            model_id = model.get("id", "unknown")
            name = model.get("name", "")
            context = model.get("context_length", "?")
            print(f"[AVAILABLE] {model_id}")
            if name and name != model_id:
                print(f"   Name: {name}")
            print(f"   Context: {context:,} tokens\n")

def test_model(model_id):
    """Test if a specific model works"""
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment")
        return

    print(f"🧪 Testing model: {model_id}\n")

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Model Test"
        },
        json={
            "model": model_id,
            "messages": [
                {"role": "user", "content": "Say 'Hello, I am working!' in exactly those words."}
            ],
            "max_tokens": 50
        }
    )

    if response.status_code == 200:
        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"SUCCESS: Model works! Response:\n{content}\n")
        return True
    else:
        print(f"FAILED: Model failed with status {response.status_code}")
        error = response.json().get("error", {})
        print(f"Error: {error.get('message', 'Unknown error')}\n")
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "search" and len(sys.argv) > 2:
            search_term = sys.argv[2]
            check_openrouter_models(search_term)
        elif command == "test" and len(sys.argv) > 2:
            model_id = sys.argv[2]
            test_model(model_id)
        elif command == "list":
            check_openrouter_models()
        else:
            print("Usage:")
            print("  python check_models.py list                    # List all NSFW models")
            print("  python check_models.py search <term>           # Search for models")
            print("  python check_models.py test <model-id>         # Test a specific model")
            print("\nExamples:")
            print("  python check_models.py search euryale")
            print("  python check_models.py test sao10k/l3.1-euryale-70b")
    else:
        # Default: check NSFW models
        check_openrouter_models()
