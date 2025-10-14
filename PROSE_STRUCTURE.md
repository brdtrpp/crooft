# Structured Prose Output Documentation

## Overview

The prose generation system now outputs **structured paragraph data** with **dialogue attribution tracking**. This allows you to:

- Analyze dialogue vs. narrative ratios
- Track which characters speak in each scene
- Extract dialogue for audio production or translation
- Identify paragraph types (action, description, dialogue, etc.)
- Process prose programmatically for custom exports

---

## Data Structure

### Prose Object

```json
{
  "draft_version": 1,
  "content": "Full prose text here...",
  "paragraphs": [...],  // Structured breakdown (see below)
  "word_count": 387,
  "generated_timestamp": "2025-10-06T12:34:56",
  "status": "draft"
}
```

### Paragraph Object

Each paragraph contains:

```json
{
  "paragraph_number": 1,
  "paragraph_type": "dialogue",  // See types below
  "content": "\"I can't do this,\" Sara whispered. Her hands trembled.",
  "dialogue_lines": [...],  // Only if paragraph contains dialogue
  "pov_character": null,  // Populated for internal_monologue type
  "word_count": 12
}
```

### Paragraph Types

| Type | Description | Example |
|------|-------------|---------|
| `narrative` | Pure description/narration | "The sun set over the mountains, casting long shadows..." |
| `dialogue` | Mostly/only conversation | "\"We need to go,\" he said. \"Now.\"" |
| `mixed` | Dialogue + narrative | "\"Stop!\" Sara ran after him, her breath ragged." |
| `description` | Environmental/setting details | "The room was cold, sterile, with harsh fluorescent lights..." |
| `action` | Physical actions/movement | "He dove behind the car, bullets whizzing overhead..." |
| `internal_monologue` | Character thoughts (POV) | "She wondered if this was all a mistake. Too late now." |

### DialogueLine Object

For paragraphs with dialogue (`dialogue` or `mixed` types):

```json
{
  "speaker": "Sara",
  "dialogue": "I can't believe this is happening",
  "action": "she whispered, hands trembling",
  "internal_thought": null  // Populated for POV character
}
```

**Fields:**
- `speaker`: Character name
- `dialogue`: What they say (without quotation marks)
- `action`: Dialogue tag or action beat (e.g., "she whispered", "he slammed the door")
- `internal_thought`: If this is the POV character, their internal reaction

---

## Complete Example

### Input Beat

```json
{
  "beat_number": 1,
  "description": "Sara confronts the betrayal, John tries to explain",
  "emotional_tone": "tense, betrayed, desperate",
  "character_actions": ["Sara backs away", "John reaches out"],
  "dialogue_summary": "Sara accuses John, he tries to justify his actions"
}
```

### Generated Prose Output

```json
{
  "draft_version": 1,
  "content": "Sara stepped back, her eyes wide with disbelief. The documents scattered across the floor told a story she'd refused to believe until now.\n\n\"How could you?\" Her voice cracked. \"After everything we've been through?\"\n\nJohn reached out, desperation etched across his face. \"You don't understand. I had no choice.\"\n\n\"There's always a choice.\" She turned away, unable to look at him. The betrayal cut deeper than any blade.",
  "paragraphs": [
    {
      "paragraph_number": 1,
      "paragraph_type": "description",
      "content": "Sara stepped back, her eyes wide with disbelief. The documents scattered across the floor told a story she'd refused to believe until now.",
      "dialogue_lines": [],
      "pov_character": "Sara",
      "word_count": 28
    },
    {
      "paragraph_number": 2,
      "paragraph_type": "dialogue",
      "content": "\"How could you?\" Her voice cracked. \"After everything we've been through?\"",
      "dialogue_lines": [
        {
          "speaker": "Sara",
          "dialogue": "How could you? After everything we've been through?",
          "action": "her voice cracked",
          "internal_thought": null
        }
      ],
      "pov_character": null,
      "word_count": 13
    },
    {
      "paragraph_number": 3,
      "paragraph_type": "mixed",
      "content": "John reached out, desperation etched across his face. \"You don't understand. I had no choice.\"",
      "dialogue_lines": [
        {
          "speaker": "John",
          "dialogue": "You don't understand. I had no choice.",
          "action": "desperation etched across his face",
          "internal_thought": null
        }
      ],
      "pov_character": null,
      "word_count": 16
    },
    {
      "paragraph_number": 4,
      "paragraph_type": "mixed",
      "content": "\"There's always a choice.\" She turned away, unable to look at him. The betrayal cut deeper than any blade.",
      "dialogue_lines": [
        {
          "speaker": "Sara",
          "dialogue": "There's always a choice.",
          "action": "turned away, unable to look at him",
          "internal_thought": "The betrayal cut deeper than any blade"
        }
      ],
      "pov_character": "Sara",
      "word_count": 21
    }
  ],
  "word_count": 78,
  "generated_timestamp": "2025-10-06T14:23:45",
  "status": "draft"
}
```

---

## Use Cases

### 1. Dialogue Extraction

Extract all dialogue for a character:

```python
def get_character_dialogue(project, character_name):
    dialogue = []
    for book in project.series.books:
        for chapter in book.chapters:
            for scene in chapter.scenes:
                for beat in scene.beats:
                    if beat.prose and beat.prose.paragraphs:
                        for para in beat.prose.paragraphs:
                            for line in para.dialogue_lines:
                                if line.speaker == character_name:
                                    dialogue.append({
                                        "chapter": chapter.chapter_number,
                                        "scene": scene.scene_number,
                                        "dialogue": line.dialogue,
                                        "action": line.action
                                    })
    return dialogue
```

### 2. Paragraph Type Analysis

Analyze narrative vs. dialogue ratio:

```python
def analyze_paragraph_types(project):
    counts = {}
    for book in project.series.books:
        for chapter in book.chapters:
            for scene in chapter.scenes:
                for beat in scene.beats:
                    if beat.prose and beat.prose.paragraphs:
                        for para in beat.prose.paragraphs:
                            counts[para.paragraph_type] = counts.get(para.paragraph_type, 0) + 1
    return counts

# Output: {"dialogue": 45, "narrative": 30, "description": 12, ...}
```

### 3. Character Speech Patterns

Track who speaks most:

```python
def character_speech_stats(project):
    stats = {}
    for book in project.series.books:
        for chapter in book.chapters:
            for scene in chapter.scenes:
                for beat in scene.beats:
                    if beat.prose and beat.prose.paragraphs:
                        for para in beat.prose.paragraphs:
                            for line in para.dialogue_lines:
                                speaker = line.speaker
                                stats[speaker] = stats.get(speaker, 0) + len(line.dialogue.split())
    return stats

# Output: {"Sara": 1245, "John": 987, "Marcus": 654}
```

### 4. Export Dialogue-Only Script

```python
def export_dialogue_script(project, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for book in project.series.books:
            for chapter in book.chapters:
                f.write(f"\n## Chapter {chapter.chapter_number}: {chapter.title}\n\n")
                for scene in chapter.scenes:
                    for beat in scene.beats:
                        if beat.prose and beat.prose.paragraphs:
                            for para in beat.prose.paragraphs:
                                for line in para.dialogue_lines:
                                    f.write(f"{line.speaker}: \"{line.dialogue}\"\n")
                                    if line.action:
                                        f.write(f"  [{line.action}]\n")
```

### 5. Internal Monologue Tracking

Extract POV character thoughts:

```python
def get_internal_thoughts(project, character_name):
    thoughts = []
    for book in project.series.books:
        for chapter in book.chapters:
            for scene in chapter.scenes:
                for beat in scene.beats:
                    if beat.prose and beat.prose.paragraphs:
                        for para in beat.prose.paragraphs:
                            if para.pov_character == character_name:
                                if para.paragraph_type == "internal_monologue":
                                    thoughts.append(para.content)
                                for line in para.dialogue_lines:
                                    if line.internal_thought:
                                        thoughts.append(line.internal_thought)
    return thoughts
```

---

## Backward Compatibility

The `Prose.content` field is still populated with the **full prose text** for backward compatibility. If you don't need structured data, you can continue using:

```python
# Old way (still works)
prose_text = beat.prose.content

# New way (structured)
for paragraph in beat.prose.paragraphs:
    print(f"[{paragraph.paragraph_type}] {paragraph.content}")
```

---

## Manuscript Export

The `export_manuscript()` method automatically uses the structured paragraph data:

- Exports each paragraph as a separate block
- Maintains proper paragraph breaks
- Falls back to `content` field if `paragraphs` is empty

---

## Benefits

1. **Dialogue Analysis**: Track character speech patterns, word counts, speaking frequency
2. **Translation**: Extract dialogue separately for localization
3. **Audio Production**: Generate character scripts for voice actors
4. **Pacing Analysis**: Identify action-heavy vs. dialogue-heavy scenes
5. **Custom Exports**: Generate screenplay format, podcast scripts, etc.
6. **Quality Control**: Ensure balanced paragraph types
7. **Character Development**: Track internal monologue for POV consistency

---

## Example Query: Find All Scenes with Heavy Dialogue

```python
def find_dialogue_heavy_scenes(project, threshold=0.6):
    """Find scenes where >60% of paragraphs are dialogue"""
    dialogue_scenes = []

    for book in project.series.books:
        for chapter in book.chapters:
            for scene in chapter.scenes:
                total = 0
                dialogue_count = 0

                for beat in scene.beats:
                    if beat.prose and beat.prose.paragraphs:
                        for para in beat.prose.paragraphs:
                            total += 1
                            if para.paragraph_type in ["dialogue", "mixed"]:
                                dialogue_count += 1

                if total > 0 and (dialogue_count / total) >= threshold:
                    dialogue_scenes.append({
                        "book": book.book_number,
                        "chapter": chapter.chapter_number,
                        "scene": scene.scene_number,
                        "title": scene.title,
                        "dialogue_ratio": dialogue_count / total
                    })

    return dialogue_scenes
```

---

## JSON Schema Reference

See `models/schema.py` for complete Pydantic models:

- `Prose`: Main prose container
- `Paragraph`: Individual paragraph with type tracking
- `DialogueLine`: Dialogue attribution with speaker and action

All data is validated at runtime and serialized to JSON checkpoints.
