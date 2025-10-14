#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test JSON extraction from LLM responses"""

import sys
import json

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def extract_json(response):
    """Extract JSON from response (same logic as prose_generator.py)"""
    response_text = response.strip()

    # Try to find JSON object in response
    json_start = response_text.find('{')
    json_end = response_text.rfind('}') + 1

    if json_start != -1 and json_end > json_start:
        json_str = response_text[json_start:json_end]
        return json.loads(json_str)
    else:
        # Fallback: try parsing entire response
        return json.loads(response_text)

# Test cases
test_cases = [
    # Case 1: Preamble text (your actual error case)
    """Here is the output JSON for the requested beat:

{
  "meta": {
    "version": "2.0",
    "beat_id": "test1"
  },
  "full_prose": "Test prose content.",
  "paragraphs": [],
  "word_count": 3
}""",

    # Case 2: Pure JSON (ideal case)
    """{
  "meta": {
    "version": "2.0",
    "beat_id": "test2"
  },
  "full_prose": "Pure JSON test.",
  "paragraphs": [],
  "word_count": 3
}""",

    # Case 3: Postamble text
    """{
  "meta": {
    "version": "2.0",
    "beat_id": "test3"
  },
  "full_prose": "With postamble.",
  "paragraphs": [],
  "word_count": 2
}

I hope this JSON meets your requirements!""",

    # Case 4: Both preamble and postamble
    """Here's the JSON you requested:

{
  "meta": {
    "version": "2.0",
    "beat_id": "test4"
  },
  "full_prose": "Both pre and post.",
  "paragraphs": [],
  "word_count": 4
}

Let me know if you need any changes!"""
]

print("Testing JSON extraction...\n")

for i, test in enumerate(test_cases, 1):
    print(f"Test Case {i}:")
    print("-" * 50)
    try:
        result = extract_json(test)
        beat_id = result.get('meta', {}).get('beat_id', 'unknown')
        prose = result.get('full_prose', '')
        print(f"✅ SUCCESS")
        print(f"   Beat ID: {beat_id}")
        print(f"   Prose: {prose}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
    print()

print("All tests completed!")
