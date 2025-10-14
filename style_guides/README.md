# Style Guide System for Prose Generation

## Overview

The style guide feature allows you to provide specific writing instructions to the prose generator, ensuring your novel matches your desired voice, tone, and stylistic preferences.

## How to Use Style Guides

### In the Web UI (Step-by-Step Page)

1. **Navigate to Step-by-Step page** in the web UI
2. **Find the "📝 Prose Style Guide" section** (expandable section above Auto-QA toggle)
3. **Choose one of these methods:**

   **Method 1: Type directly**
   - Click the text area
   - Type or paste your style guide
   - Style guide is auto-saved to session state

   **Method 2: Upload a file**
   - Click "Upload Style Guide (.txt, .md)"
   - Select a `.txt` or `.md` file with your style guide
   - File content loads automatically into the text area

   **Method 3: Load example**
   - Copy content from one of the example files in this folder
   - Paste into the text area

4. **Run the Prose Generator agent**
   - Your style guide will be included with every beat
   - The AI will follow your instructions while generating prose

5. **Save your style guide** (optional)
   - Click the "💾 Save" button to download current style guide
   - Reuse it for future projects

## What to Include in a Style Guide

### Essential Elements

**Voice & Tone**
- POV style (first-person, close third-person, omniscient)
- Overall tone (dark, humorous, lyrical, gritty)
- Narrative voice characteristics

**Sentence Structure**
- Preferred sentence lengths and rhythms
- When to use fragments or long sentences
- Active vs passive voice preferences

**Dialogue Style**
- How characters should speak
- Dialogue tag preferences
- Use of subtext vs direct communication

**Pacing Guidelines**
- Action scene tempo
- Emotional scene pacing
- When to slow down or speed up

**Show vs Tell**
- How to convey emotion
- Sensory detail preferences
- Internal monologue approach

**Genre-Specific Requirements**
- Romance: Heat level, consent handling, emotional focus
- Thriller: Tension building, action choreography
- Fantasy: Magic system integration, world-building balance
- Literary: Prose style, metaphor use, theme integration

### Example Style Guide Format

```markdown
# My Novel Style Guide

## Voice & Tone
- Close third-person POV, deeply embedded in character perspective
- Dark, atmospheric tone with moments of dry humor
- Literary quality prose, but accessible

## Sentence Structure
- Vary length for rhythm
- Short sentences for tension/action
- Longer, flowing sentences for introspection
- Use fragments sparingly for emphasis

## Dialogue
- Natural, character-specific voices
- Minimal dialogue tags - use action beats
- Subtext over exposition
- Characters have distinct speech patterns

## Show, Don't Tell
- Physical sensations over emotion words
- Body language reveals character state
- Environmental details reflect mood
- Specific, concrete details

## Sensory Details
- Emphasize smell and sound (my POV character's strengths)
- Ground every scene physically
- Unusual sensory details that surprise

## Pacing
- Action: Rapid, minimal description
- Emotion: Allow breathing room
- Mystery: Slow reveals, plant clues subtly

## Avoid
- Adverbs in dialogue tags
- Purple prose
- Info dumps
- Head-hopping
- Clichéd descriptions
```

## Example Style Guides Provided

1. **example_style_guide.txt** - General fiction best practices
2. **erotica_style_guide.txt** - Romance/NSFW content guidelines
3. **action_thriller_style_guide.txt** - Fast-paced action and suspense

## Tips for Effective Style Guides

### Be Specific
- ❌ "Write good dialogue"
- ✅ "Use action beats instead of dialogue tags. Each character should have distinct speech patterns reflecting their background."

### Provide Examples
- Show what you want and what to avoid
- Include specific phrases or techniques

### Focus on Your Priorities
- Don't try to control everything
- Highlight 5-10 most important style elements
- Let the AI handle the rest

### Balance Freedom and Control
- Give guidelines, not rigid rules
- Allow room for creativity
- Focus on "prefer X" rather than "never Y"

### Test and Iterate
- Generate a few beats with your style guide
- Refine based on results
- Different scenes may need different emphasis

## Advanced: Context-Specific Style Guides

You can modify your style guide based on:
- **Genre blend**: Romance-thriller gets different treatment than pure romance
- **POV character**: Each character's sections might have unique voice
- **Book in series**: Later books might have different tone
- **Scene type**: Action vs emotional vs mystery scenes

## Integration with Pipeline

The style guide is:
1. **Prepended** to each beat's context with clear delimiters
2. **Processed** by the LLM alongside beat description, character actions, dialogue summary
3. **Applied consistently** across all beats in your prose generation run
4. **Preserved** in session state until you change it

## Troubleshooting

**Style guide not being followed?**
- Make instructions more specific
- Check for conflicting guidelines
- Ensure beat descriptions don't contradict style guide
- Try shorter, clearer instructions

**Prose too similar/repetitive?**
- Allow more creative freedom in style guide
- Focus on tone/voice rather than specific techniques
- Vary beat descriptions to encourage variety

**Style guide too restrictive?**
- Reduce number of rules
- Use "prefer" language instead of "must/never"
- Focus on highest-priority elements only

## Style Guide Storage

- **Session**: Stored in Streamlit session state (temporary)
- **File**: Save/load from `.txt` or `.md` files
- **Project**: Not currently stored with project JSON (manual load each session)

To persist across sessions, save your style guide file and reload it when starting a new session.
