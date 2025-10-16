"""
Additional pages for the Fiction Pipeline Reflex UI
Contains implementations for Stage Viewer, Prose Reader, Analytics, Export, etc.
"""

import reflex as rx
from typing import List, Dict, Any


# Stage Viewer Page Components

def stage_viewer_series_outline(project: Dict[str, Any]) -> rx.Component:
    """Display series outline"""
    series = project.get("series", {})

    return rx.vstack(
        rx.heading("Series Outline", size="6"),

        rx.hstack(
            rx.vstack(
                rx.text("Title: ", series.get("title", "Unknown"), weight="bold"),
                rx.text("Genre: ", series.get("genre", "Unknown")),
                rx.text("Target Audience: ", series.get("target_audience", "Unknown")),
                align_items="start",
                spacing="2",
            ),
            rx.vstack(
                rx.text("Themes:", weight="bold"),
                rx.foreach(
                    series.get("themes", []),
                    lambda theme: rx.text("• ", theme, size="2"),
                ),
                align_items="start",
                spacing="1",
            ),
            spacing="4",
            width="100%",
        ),

        rx.text("Premise", weight="bold", margin_top="1rem"),
        rx.text_area(
            value=series.get("premise", ""),
            is_read_only=True,
            height="150px",
            width="100%",
        ),

        spacing="3",
        width="100%",
        align_items="start",
    )


def stage_viewer_lore_database(project: Dict[str, Any]) -> rx.Component:
    """Display lore database"""
    lore = project.get("series", {}).get("lore", {})
    characters = lore.get("characters", [])
    locations = lore.get("locations", [])
    world_elements = lore.get("world_elements", [])

    return rx.vstack(
        rx.heading("Lore Database", size="6"),

        rx.tabs(
            rx.tab_list(
                rx.tab("Characters", value="characters"),
                rx.tab("Locations", value="locations"),
                rx.tab("World Elements", value="world_elements"),
            ),
            rx.tab_panels(
                rx.tab_panel(
                    rx.vstack(
                        rx.text(f"Total Characters: {len(characters)}", weight="bold"),
                        rx.foreach(
                            characters,
                            lambda char: rx.card(
                                rx.vstack(
                                    rx.heading(f"{char.get('name', 'Unknown')} - {char.get('role', 'Unknown')}", size="4"),
                                    rx.text(char.get("description", "")),
                                    align_items="start",
                                    spacing="2",
                                ),
                                width="100%",
                                margin_bottom="0.5rem",
                            ),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    value="characters",
                ),
                rx.tab_panel(
                    rx.vstack(
                        rx.text(f"Total Locations: {len(locations)}", weight="bold"),
                        rx.foreach(
                            locations,
                            lambda loc: rx.card(
                                rx.vstack(
                                    rx.heading(loc.get('name', 'Unknown'), size="4"),
                                    rx.text(loc.get("description", "")),
                                    align_items="start",
                                    spacing="2",
                                ),
                                width="100%",
                                margin_bottom="0.5rem",
                            ),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    value="locations",
                ),
                rx.tab_panel(
                    rx.vstack(
                        rx.text(f"Total World Elements: {len(world_elements)}", weight="bold"),
                        rx.foreach(
                            world_elements,
                            lambda elem: rx.card(
                                rx.vstack(
                                    rx.heading(f"{elem.get('name', 'Unknown')} ({elem.get('type', 'Unknown')})", size="4"),
                                    rx.text(elem.get("description", "")),
                                    align_items="start",
                                    spacing="2",
                                ),
                                width="100%",
                                margin_bottom="0.5rem",
                            ),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    value="world_elements",
                ),
            ),
            default_value="characters",
            width="100%",
        ),

        spacing="3",
        width="100%",
        align_items="start",
    )


# Analytics Page Helpers

def calculate_analytics(project: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate project analytics"""
    books = project.get("series", {}).get("books", [])
    lore = project.get("series", {}).get("lore", {})

    total_books = len(books)
    total_chapters = sum(len(book.get("chapters", [])) for book in books)
    total_scenes = sum(
        len(ch.get("scenes", []))
        for book in books
        for ch in book.get("chapters", [])
    )
    total_words = sum(book.get("current_word_count", 0) for book in books)

    return {
        "total_books": total_books,
        "total_chapters": total_chapters,
        "total_scenes": total_scenes,
        "total_words": total_words,
        "characters": len(lore.get("characters", [])),
        "locations": len(lore.get("locations", [])),
        "world_elements": len(lore.get("world_elements", [])),
    }
