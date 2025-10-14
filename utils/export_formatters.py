#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export Formatters for Fiction Pipeline

Handles export to various formats (Markdown, EPUB, etc.)
"""

import os
from datetime import datetime
from typing import Optional
from models.schema import FictionProject, Book


class MarkdownExporter:
    """Export book to Markdown format"""

    @staticmethod
    def export_book(book: Book, output_dir: str = "manuscripts", series_title: str = "") -> str:
        """
        Export a book to Markdown format

        Args:
            book: Book object to export
            output_dir: Directory to save the file
            series_title: Optional series title for metadata

        Returns:
            Path to the exported file
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Build markdown content
        lines = []

        # Title page
        lines.append(f"# {book.title}")
        lines.append("")
        if series_title:
            lines.append(f"*{series_title} - Book {book.book_number}*")
            lines.append("")
        lines.append(f"*Draft Version - Generated {datetime.now().strftime('%B %d, %Y')}*")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Table of Contents (optional)
        lines.append("## Table of Contents")
        lines.append("")
        for chapter in book.chapters:
            lines.append(f"{chapter.chapter_number}. [{chapter.title}](#chapter-{chapter.chapter_number})")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Chapters
        for chapter in book.chapters:
            # Chapter heading
            lines.append(f"## Chapter {chapter.chapter_number}: {chapter.title} {{#chapter-{chapter.chapter_number}}}")
            lines.append("")

            # Scenes
            for scene_idx, scene in enumerate(chapter.scenes):
                # Scene break (except for first scene)
                if scene_idx > 0:
                    lines.append("")
                    lines.append("* * *")
                    lines.append("")

                # Collect prose from all beats
                for beat in scene.beats:
                    if beat.prose:
                        if beat.prose.paragraphs:
                            # Use structured paragraphs
                            for para in beat.prose.paragraphs:
                                lines.append(para.content)
                                lines.append("")
                        elif beat.prose.content:
                            # Use full prose content
                            lines.append(beat.prose.content)
                            lines.append("")

            # Chapter end
            lines.append("")

        # Join all lines
        markdown_content = "\n".join(lines)

        # Generate filename
        safe_title = "".join(c for c in book.title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')
        filename = f"{safe_title}_book{book.book_number}.md"
        filepath = os.path.join(output_dir, filename)

        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        return filepath


class EPUBExporter:
    """Export book to EPUB format"""

    @staticmethod
    def export_book(book: Book, output_dir: str = "manuscripts", series_title: str = "",
                   author_name: str = "AI Generated", cover_image: Optional[str] = None) -> str:
        """
        Export a book to EPUB format

        Args:
            book: Book object to export
            output_dir: Directory to save the file
            series_title: Optional series title for metadata
            author_name: Author name for metadata
            cover_image: Optional path to cover image

        Returns:
            Path to the exported file
        """
        try:
            from ebooklib import epub
        except ImportError:
            raise ImportError("ebooklib is required for EPUB export. Install with: pip install ebooklib")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Create EPUB book
        epub_book = epub.EpubBook()

        # Set metadata
        book_id = f"{series_title}_{book.book_number}" if series_title else f"book_{book.book_number}"
        epub_book.set_identifier(book_id)
        epub_book.set_title(book.title)
        epub_book.set_language('en')
        epub_book.add_author(author_name)

        if series_title:
            epub_book.add_metadata('DC', 'description', f'{series_title} - Book {book.book_number}')

        # Add cover if provided
        if cover_image and os.path.exists(cover_image):
            with open(cover_image, 'rb') as f:
                epub_book.set_cover('cover.jpg', f.read())

        # Create chapters
        epub_chapters = []
        spine_items = ['nav']

        for chapter in book.chapters:
            # Build chapter content
            chapter_content = []
            chapter_content.append(f'<h1>Chapter {chapter.chapter_number}: {chapter.title}</h1>')

            # Scenes
            for scene_idx, scene in enumerate(chapter.scenes):
                # Scene break
                if scene_idx > 0:
                    chapter_content.append('<hr class="scene-break" />')

                # Collect prose from all beats
                for beat in scene.beats:
                    if beat.prose:
                        if beat.prose.paragraphs:
                            # Use structured paragraphs
                            for para in beat.prose.paragraphs:
                                # Escape HTML entities
                                safe_content = (para.content
                                    .replace('&', '&amp;')
                                    .replace('<', '&lt;')
                                    .replace('>', '&gt;')
                                    .replace('\n', '<br/>')
                                )
                                chapter_content.append(f'<p>{safe_content}</p>')
                        elif beat.prose.content:
                            # Use full prose content, split by paragraphs
                            paragraphs = beat.prose.content.split('\n\n')
                            for para in paragraphs:
                                if para.strip():
                                    safe_content = (para
                                        .replace('&', '&amp;')
                                        .replace('<', '&lt;')
                                        .replace('>', '&gt;')
                                        .replace('\n', '<br/>')
                                    )
                                    chapter_content.append(f'<p>{safe_content}</p>')

            # Create EPUB chapter
            epub_chapter = epub.EpubHtml(
                title=f'Chapter {chapter.chapter_number}: {chapter.title}',
                file_name=f'chapter_{chapter.chapter_number}.xhtml',
                lang='en'
            )
            epub_chapter.content = '\n'.join(chapter_content)

            # Add chapter to book
            epub_book.add_item(epub_chapter)
            epub_chapters.append(epub_chapter)
            spine_items.append(epub_chapter)

        # Add CSS
        style = '''
        @namespace epub "http://www.idpf.org/2007/ops";
        body {
            font-family: Georgia, serif;
            line-height: 1.8;
            text-align: justify;
            margin: 1em;
        }
        h1 {
            text-align: center;
            margin-top: 3em;
            margin-bottom: 2em;
            font-size: 2em;
        }
        p {
            text-indent: 2em;
            margin: 0;
            margin-bottom: 0.5em;
        }
        p:first-of-type {
            text-indent: 0;
        }
        .scene-break {
            text-align: center;
            border: none;
            margin: 2em 0;
        }
        .scene-break::after {
            content: "* * *";
        }
        '''
        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
            media_type="text/css",
            content=style
        )
        epub_book.add_item(nav_css)

        # Add navigation
        epub_book.toc = tuple(epub_chapters)
        epub_book.add_item(epub.EpubNcx())
        epub_book.add_item(epub.EpubNav())

        # Define spine
        epub_book.spine = spine_items

        # Generate filename
        safe_title = "".join(c for c in book.title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')
        filename = f"{safe_title}_book{book.book_number}.epub"
        filepath = os.path.join(output_dir, filename)

        # Write EPUB file
        epub.write_epub(filepath, epub_book)

        return filepath


def export_project_as_markdown(project: FictionProject, output_dir: str = "manuscripts") -> list:
    """
    Export all books in a project as Markdown files

    Args:
        project: FictionProject to export
        output_dir: Directory to save files

    Returns:
        List of file paths created
    """
    files_created = []

    for book in project.series.books:
        filepath = MarkdownExporter.export_book(
            book=book,
            output_dir=output_dir,
            series_title=project.series.title
        )
        files_created.append(filepath)

    return files_created


def export_project_as_epub(project: FictionProject, output_dir: str = "manuscripts",
                           author_name: str = "AI Generated") -> list:
    """
    Export all books in a project as EPUB files

    Args:
        project: FictionProject to export
        output_dir: Directory to save files
        author_name: Author name for metadata

    Returns:
        List of file paths created
    """
    files_created = []

    for book in project.series.books:
        filepath = EPUBExporter.export_book(
            book=book,
            output_dir=output_dir,
            series_title=project.series.title,
            author_name=author_name
        )
        files_created.append(filepath)

    return files_created
