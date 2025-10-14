# Complete Novel Creation Workflow in LangChain with Structured JSON Output
# This implements the hierarchical workflow: Outline -> Chapters -> Scenes -> Beats -> Prose -> Editing

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.output_parsers import PydanticOutputParser
import json
import os

# =============================================================================
# PYDANTIC MODELS FOR STRUCTURED OUTPUT
# =============================================================================

class NovelOutline(BaseModel):
    """Overall novel outline structure"""
    title: str = Field(description="Title of the novel")
    genre: str = Field(description="Primary genre")
    premise: str = Field(description="One-sentence premise/logline")
    main_characters: List[str] = Field(description="List of main character names")
    setting: str = Field(description="Time and place setting")
    themes: List[str] = Field(description="Major themes explored")
    act_structure: List[str] = Field(description="Three-act structure breakdown")
    estimated_chapters: int = Field(description="Estimated number of chapters")

class ChapterOutline(BaseModel):
    """Individual chapter outline"""
    chapter_number: int = Field(description="Chapter number")
    title: str = Field(description="Chapter title")
    pov_character: str = Field(description="Point of view character")
    setting: str = Field(description="Chapter setting")
    main_goal: str = Field(description="Main goal/objective for this chapter")
    conflict: str = Field(description="Primary conflict or tension")
    key_events: List[str] = Field(description="Key events that occur")
    character_development: str = Field(description="How characters change/grow")
    chapter_ending: str = Field(description="How the chapter ends")

class ChapterBreakdown(BaseModel):
    """Complete chapter breakdown for the novel"""
    novel_title: str = Field(description="Title of the novel")
    chapters: List[ChapterOutline] = Field(description="List of all chapter outlines")

class SceneOutline(BaseModel):
    """Individual scene outline"""
    scene_number: int = Field(description="Scene number within chapter")
    location: str = Field(description="Specific location/setting")
    characters_present: List[str] = Field(description="Characters in this scene")
    scene_goal: str = Field(description="What this scene needs to accomplish")
    opening: str = Field(description="How the scene opens")
    main_action: str = Field(description="Primary action/events")
    dialogue_focus: str = Field(description="Key dialogue or conversation points")
    conflict_tension: str = Field(description="Conflict or tension in the scene")
    scene_ending: str = Field(description="How the scene concludes")
    emotional_arc: str = Field(description="Emotional journey of characters")

class ChapterScenes(BaseModel):
    """Scenes breakdown for a single chapter"""
    chapter_number: int = Field(description="Chapter number")
    chapter_title: str = Field(description="Chapter title")
    scenes: List[SceneOutline] = Field(description="List of scenes in this chapter")

class Beat(BaseModel):
    """Individual story beat"""
    beat_number: int = Field(description="Beat number within scene")
    beat_type: str = Field(description="Type of beat (action, dialogue, description, internal)")
    content: str = Field(description="What happens in this beat")
    character_focus: Optional[str] = Field(description="Character focus if applicable")
    emotional_note: Optional[str] = Field(description="Emotional tone or note")

class SceneBeats(BaseModel):
    """Beat breakdown for a single scene"""
    chapter_number: int = Field(description="Chapter number")
    scene_number: int = Field(description="Scene number")
    scene_goal: str = Field(description="Scene goal for context")
    beats: List[Beat] = Field(description="List of beats in this scene")

class SceneProse(BaseModel):
    """Generated prose for a scene"""
    chapter_number: int = Field(description="Chapter number")
    scene_number: int = Field(description="Scene number")
    word_count: int = Field(description="Approximate word count")
    prose: str = Field(description="The actual prose text")

class EditedContent(BaseModel):
    """Edited version of content"""
    original_word_count: int = Field(description="Original word count")
    edited_word_count: int = Field(description="Edited word count")
    editing_notes: List[str] = Field(description="List of changes made")
    edited_prose: str = Field(description="The edited prose")

# =============================================================================
# WORKFLOW CLASS
# =============================================================================

class NovelCreationWorkflow:
    def __init__(self, model_name="anthropic/claude-3.5-sonnet", temperature=0.3, openrouter_api_key=None):
        """Initialize the workflow with LLM configuration for OpenRouter"""
        api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "http://localhost",
                "X-Title": "Novel Creation Workflow"
            }
        )
        self.workflow_data = {}
        
    def create_chain(self, prompt_template: str, output_model: BaseModel, input_variables: List[str]):
        """Helper method to create a standardized chain with structured output"""
        parser = PydanticOutputParser(pydantic_object=output_model)
        
        prompt = PromptTemplate(
            template=prompt_template + "\n\n{format_instructions}",
            input_variables=input_variables,
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt, output_parser=parser)
        return chain
    
    def step1_create_outline(self, concept: str, genre: str = "science fiction") -> NovelOutline:
        """Step 1: Create overall novel outline from concept"""
        print("Step 1: Creating Novel Outline...")
        
        prompt_template = """
        Create a comprehensive novel outline based on the following concept and genre.
        
        Concept: {concept}
        Genre: {genre}
        
        Generate a detailed outline that includes:
        - A compelling title
        - Clear premise/logline
        - Main characters (3-5 key characters)
        - Setting details
        - Major themes
        - Three-act structure breakdown
        - Estimated chapter count (typically 15-25 for a novel)
        
        Ensure the outline is cohesive and provides a strong foundation for a full novel.
        """
        
        chain = self.create_chain(prompt_template, NovelOutline, ["concept", "genre"])
        outline = chain.invoke({"concept": concept, "genre": genre})
        self.workflow_data['outline'] = outline
        return outline
    
    def step2_create_chapter_breakdown(self, outline: NovelOutline) -> ChapterBreakdown:
        """Step 2: Break outline into detailed chapter outlines"""
        print("Step 2: Creating Chapter Breakdown...")
        
        prompt_template = """
        Based on the following novel outline, create detailed chapter outlines for the entire book.
        
        Novel Title: {title}
        Premise: {premise}
        Characters: {characters}
        Setting: {setting}
        Themes: {themes}
        Act Structure: {act_structure}
        Estimated Chapters: {estimated_chapters}
        
        Create exactly {estimated_chapters} detailed chapter outlines. Each chapter should:
        - Have a clear goal and conflict
        - Advance the plot meaningfully
        - Develop characters
        - Maintain proper pacing
        - Connect logically to adjacent chapters
        
        Ensure the chapters follow the three-act structure and build toward a satisfying conclusion.
        """
        
        chain = self.create_chain(
            prompt_template, 
            ChapterBreakdown, 
            ["title", "premise", "characters", "setting", "themes", "act_structure", "estimated_chapters"]
        )
        
        chapter_breakdown = chain.invoke({
            "title": outline.title,
            "premise": outline.premise,
            "characters": ", ".join(outline.main_characters),
            "setting": outline.setting,
            "themes": ", ".join(outline.themes),
            "act_structure": " | ".join(outline.act_structure),
            "estimated_chapters": outline.estimated_chapters
        })
        
        self.workflow_data['chapter_breakdown'] = chapter_breakdown
        return chapter_breakdown
    
    def step3_create_scene_breakdown(self, chapter_outline: ChapterOutline) -> ChapterScenes:
        """Step 3: Break individual chapter into scenes"""
        print(f"Step 3: Creating Scene Breakdown for Chapter {chapter_outline.chapter_number}...")
        
        prompt_template = """
        Break this chapter outline into detailed scenes (typically 2-4 scenes per chapter).
        
        Chapter {chapter_number}: {title}
        POV Character: {pov_character}
        Setting: {setting}
        Main Goal: {main_goal}
        Conflict: {conflict}
        Key Events: {key_events}
        Character Development: {character_development}
        Chapter Ending: {chapter_ending}
        
        Create 2-4 scenes that:
        - Each have a clear purpose and goal
        - Build toward the chapter's main objective
        - Include proper scene transitions
        - Balance action, dialogue, and description
        - Develop characters and advance plot
        """
        
        chain = self.create_chain(
            prompt_template, 
            ChapterScenes,
            ["chapter_number", "title", "pov_character", "setting", "main_goal", "conflict", "key_events", "character_development", "chapter_ending"]
        )
        
        scenes = chain.invoke({
            "chapter_number": chapter_outline.chapter_number,
            "title": chapter_outline.title,
            "pov_character": chapter_outline.pov_character,
            "setting": chapter_outline.setting,
            "main_goal": chapter_outline.main_goal,
            "conflict": chapter_outline.conflict,
            "key_events": ", ".join(chapter_outline.key_events),
            "character_development": chapter_outline.character_development,
            "chapter_ending": chapter_outline.chapter_ending
        })
        
        return scenes
    
    def step4_create_beat_breakdown(self, scene_outline: SceneOutline, chapter_number: int) -> SceneBeats:
        """Step 4: Break individual scene into beats"""
        print(f"Step 4: Creating Beat Breakdown for Chapter {chapter_number}, Scene {scene_outline.scene_number}...")
        
        prompt_template = """
        Break this scene outline into detailed story beats (typically 5-8 beats per scene).
        
        Scene {scene_number} - Location: {location}
        Characters Present: {characters_present}
        Scene Goal: {scene_goal}
        Opening: {opening}
        Main Action: {main_action}
        Dialogue Focus: {dialogue_focus}
        Conflict/Tension: {conflict_tension}
        Scene Ending: {scene_ending}
        Emotional Arc: {emotional_arc}
        
        Create 5-8 beats that:
        - Each represent a small story unit
        - Include mix of action, dialogue, description, and internal thoughts
        - Build logical progression through the scene
        - Create proper pacing and rhythm
        - Support the scene's emotional arc
        """
        
        chain = self.create_chain(
            prompt_template,
            SceneBeats,
            ["chapter_number", "scene_number", "location", "characters_present", "scene_goal", "opening", "main_action", "dialogue_focus", "conflict_tension", "scene_ending", "emotional_arc"]
        )
        
        beats = chain.invoke({
            "chapter_number": chapter_number,
            "scene_number": scene_outline.scene_number,
            "location": scene_outline.location,
            "characters_present": ", ".join(scene_outline.characters_present),
            "scene_goal": scene_outline.scene_goal,
            "opening": scene_outline.opening,
            "main_action": scene_outline.main_action,
            "dialogue_focus": scene_outline.dialogue_focus,
            "conflict_tension": scene_outline.conflict_tension,
            "scene_ending": scene_outline.scene_ending,
            "emotional_arc": scene_outline.emotional_arc
        })
        
        return beats
    
    def step5_generate_prose(self, scene_beats: SceneBeats, style_guide: str = "literary science fiction") -> SceneProse:
        """Step 5: Generate prose from beats"""
        print(f"Step 5: Generating Prose for Chapter {scene_beats.chapter_number}, Scene {scene_beats.scene_number}...")
        
        # Convert beats to string format for prompt
        beats_text = "\n".join([f"Beat {beat.beat_number} ({beat.beat_type}): {beat.content}" for beat in scene_beats.beats])
        
        prompt_template = """
        Write compelling prose for this scene based on the following beats and style guide.
        
        Style Guide: {style_guide}
        Scene Goal: {scene_goal}
        
        Story Beats:
        {beats_text}
        
        Generate prose that:
        - Follows the beats closely while adding rich detail
        - Matches the specified style guide
        - Includes vivid descriptions and strong dialogue
        - Maintains consistent POV and voice
        - Creates engaging, readable narrative
        - Aims for approximately 1000-1500 words
        
        Write the complete scene prose based on these beats.
        """
        
        chain = self.create_chain(
            prompt_template,
            SceneProse,
            ["chapter_number", "scene_number", "style_guide", "scene_goal", "beats_text"]
        )
        
        prose = chain.invoke({
            "chapter_number": scene_beats.chapter_number,
            "scene_number": scene_beats.scene_number,
            "style_guide": style_guide,
            "scene_goal": scene_beats.scene_goal,
            "beats_text": beats_text
        })
        
        return prose
    
    def step6_edit_prose(self, scene_prose: SceneProse, editing_focus: str = "clarity and flow") -> EditedContent:
        """Step 6: Edit and refine the generated prose"""
        print(f"Step 6: Editing Prose for Chapter {scene_prose.chapter_number}, Scene {scene_prose.scene_number}...")
        
        prompt_template = """
        Edit and improve the following prose with focus on: {editing_focus}
        
        Original Prose ({word_count} words):
        {prose}
        
        Edit for:
        - Grammar and syntax
        - Clarity and readability
        - Flow and pacing
        - Character voice consistency
        - Vivid descriptions
        - Strong dialogue
        - Narrative tension
        
        Provide the edited version along with notes on changes made.
        """
        
        chain = self.create_chain(
            prompt_template,
            EditedContent,
            ["editing_focus", "word_count", "prose"]
        )
        
        edited = chain.invoke({
            "editing_focus": editing_focus,
            "word_count": scene_prose.word_count,
            "prose": scene_prose.prose
        })
        
        return edited
    
    def run_full_workflow(self, concept: str, genre: str = "science fiction", style_guide: str = "literary science fiction"):
        """
        Complete workflow orchestrator that runs all steps in sequence
        """
        print("Starting Complete Novel Creation Workflow...")
        print("=" * 60)
        
        # Step 1: Create outline
        outline = self.step1_create_outline(concept, genre)
        print(f"✓ Created outline for: {outline.title}")
        
        # Step 2: Create chapter breakdown  
        chapter_breakdown = self.step2_create_chapter_breakdown(outline)
        print(f"✓ Created {len(chapter_breakdown.chapters)} chapter outlines")
        
        # Step 3-6: For each chapter, create scenes, beats, prose, and edit
        full_novel_content = []
        
        for chapter in chapter_breakdown.chapters:
            print(f"\n--- Processing Chapter {chapter.chapter_number}: {chapter.title} ---")
            
            # Get scenes for this chapter
            chapter_scenes = self.step3_create_scene_breakdown(chapter)
            print(f"✓ Created {len(chapter_scenes.scenes)} scenes for chapter {chapter.chapter_number}")
            
            chapter_content = []
            for scene in chapter_scenes.scenes:
                # Get beats for this scene
                scene_beats = self.step4_create_beat_breakdown(scene, chapter.chapter_number)
                print(f"✓ Created {len(scene_beats.beats)} beats for scene {scene.scene_number}")
                
                # Generate prose from beats
                scene_prose = self.step5_generate_prose(scene_beats, style_guide)
                print(f"✓ Generated {scene_prose.word_count} words of prose")
                
                # Edit the prose
                edited_prose = self.step6_edit_prose(scene_prose)
                print(f"✓ Edited prose ({edited_prose.edited_word_count} words)")
                
                chapter_content.append(edited_prose.edited_prose)
            
            # Combine all scenes in chapter
            full_chapter = "\n\n".join(chapter_content)
            chapter_with_title = f"# Chapter {chapter.chapter_number}: {chapter.title}\n\n{full_chapter}"
            full_novel_content.append(chapter_with_title)
        
        # Combine all chapters
        complete_novel = "\n\n\n".join(full_novel_content)
        
        # Save to file
        with open(f"{outline.title.replace(' ', '_')}_complete.txt", "w", encoding="utf-8") as f:
            f.write(f"# {outline.title}\n")
            f.write(f"*{outline.premise}*\n\n")
            f.write("---\n\n")
            f.write(complete_novel)
        
        print("\n" + "=" * 60)
        print("✓ WORKFLOW COMPLETE!")
        print(f"✓ Novel '{outline.title}' has been generated")
        print(f"✓ Total chapters: {len(chapter_breakdown.chapters)}")
        print(f"✓ Saved to: {outline.title.replace(' ', '_')}_complete.txt")
        
        return complete_novel

# =============================================================================
# USAGE EXAMPLES
# =============================================================================

def main():
    """
    Example usage of the NovelCreationWorkflow
    """
    # Initialize workflow (uses OPENROUTER_API_KEY environment variable)
    workflow = NovelCreationWorkflow(
        model_name="anthropic/claude-3.5-sonnet",  # Or use other OpenRouter models
        temperature=0.7,  # Higher temperature for more creative output
        # openrouter_api_key="your-key-here"  # Optional: pass directly instead of using env var
    )

    # Define your novel concept
    concept = "A space station engineer discovers an alien artifact that manipulates time, but using it threatens to unravel the fabric of reality itself."

    # Option 1: Run the complete workflow
    complete_novel = workflow.run_full_workflow(
        concept=concept,
        genre="science fiction",
        style_guide="literary science fiction with hard sci-fi elements"
    )

    # Option 2: Run individual steps for more control
    # outline = workflow.step1_create_outline(concept, "science fiction")
    # chapter_breakdown = workflow.step2_create_chapter_breakdown(outline)
    # ... continue with individual steps as needed

if __name__ == "__main__":
    print("Novel Creation Workflow with LangChain and Structured JSON Output")
    print("=" * 60)
    print("This script implements a complete 6-stage novel creation pipeline:")
    print("1. Outline Creation")
    print("2. Chapter Breakdown")
    print("3. Scene Breakdown") 
    print("4. Beat Creation")
    print("5. Prose Generation")
    print("6. Editing & Refinement")
    print("=" * 60)
    print("\nTo use this script:")
    print("1. Install dependencies: pip install langchain openai pydantic")
    print("2. Add your OpenAI API key")
    print("3. Call main() or use individual workflow methods")
    print("4. Customize prompts and models as needed")