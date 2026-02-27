"""
PDF processing service - converts PDFs to page images.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()


class PDFProcessor:
    """
    Processes PDF files into individual page images for analysis.
    Uses pdf2image (which requires poppler).
    """
    
    def __init__(
        self,
        dpi: int = 150,
        image_format: str = "PNG",
        output_dir: Optional[Path] = None,
    ):
        """
        Initialize the PDF processor.
        
        Args:
            dpi: Resolution for conversion (150 sufficient for forms, reduces cost)
            image_format: Output format (PNG recommended)
            output_dir: Directory to save images (temp dir if None)
        """
        self.dpi = dpi
        self.image_format = image_format
        self.output_dir = output_dir
        self._temp_dir: Optional[tempfile.TemporaryDirectory] = None
    
    def _ensure_output_dir(self) -> Path:
        """Ensure output directory exists."""
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            return self.output_dir
        else:
            # Create temp directory
            if self._temp_dir is None:
                self._temp_dir = tempfile.TemporaryDirectory()
            return Path(self._temp_dir.name)
    
    def convert_pdf_to_images(
        self,
        pdf_path: Path,
        prefix: str = "page",
        start_page: int = 1,
        end_page: Optional[int] = None,
    ) -> list[Path]:
        """
        Convert a PDF to individual page images.
        
        Args:
            pdf_path: Path to the PDF file
            prefix: Prefix for output filenames
            start_page: First page to convert (1-indexed)
            end_page: Last page to convert (1-indexed, None = last page)
            
        Returns:
            List of paths to generated images
        """
        try:
            from pdf2image import convert_from_path
        except ImportError:
            raise ImportError(
                "pdf2image is not installed. Install it with: pip install pdf2image\n"
                "You also need poppler installed on your system:\n"
                "  - macOS: brew install poppler\n"
                "  - Ubuntu: sudo apt-get install poppler-utils\n"
                "  - Windows: Download from https://github.com/oschwartz10612/poppler-windows"
            )
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        output_dir = self._ensure_output_dir()
        
        page_range_str = f"pages {start_page}-{end_page}" if end_page else f"pages {start_page}-end"
        console.print(f"[cyan]Converting PDF to images...[/cyan]")
        console.print(f"  Source: {pdf_path}")
        console.print(f"  Page range: {page_range_str}")
        console.print(f"  DPI: {self.dpi}")
        
        # Convert PDF to images with page range
        try:
            convert_kwargs = {
                "dpi": self.dpi,
                "fmt": self.image_format.lower(),
                "first_page": start_page,
            }
            if end_page is not None:
                convert_kwargs["last_page"] = end_page
            
            images = convert_from_path(pdf_path, **convert_kwargs)
        except Exception as e:
            raise RuntimeError(
                f"Failed to convert PDF: {e}\n"
                "Make sure poppler is installed on your system."
            )
        
        # Save images - number them starting from 1 (relative to extracted range)
        image_paths: list[Path] = []
        
        for i, image in enumerate(images, start=1):
            # Use relative page number for filename
            filename = f"{prefix}_{i:03d}.{self.image_format.lower()}"
            image_path = output_dir / filename
            image.save(str(image_path), self.image_format)
            image_paths.append(image_path)
            # Show actual page number in PDF for reference
            actual_page = start_page + i - 1
            console.print(f"  [dim]Saved: {filename} (PDF page {actual_page})[/dim]")
        
        console.print(f"[green]Converted {len(images)} pages[/green]")
        
        return image_paths
    
    def load_images_from_folder(
        self,
        folder_path: Path,
        extensions: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".gif", ".webp"),
    ) -> list[Path]:
        """
        Load existing page images from a folder.
        
        Args:
            folder_path: Path to folder containing images
            extensions: Allowed image extensions
            
        Returns:
            List of image paths, sorted by name
        """
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        if not folder_path.is_dir():
            raise ValueError(f"Path is not a directory: {folder_path}")
        
        # Find all image files
        image_paths: list[Path] = []
        
        for ext in extensions:
            image_paths.extend(folder_path.glob(f"*{ext}"))
            image_paths.extend(folder_path.glob(f"*{ext.upper()}"))
        
        # Sort by name to ensure correct page order
        image_paths = sorted(set(image_paths), key=lambda p: p.name)
        
        if not image_paths:
            raise ValueError(
                f"No images found in {folder_path}. "
                f"Looking for extensions: {extensions}"
            )
        
        console.print(f"[green]Found {len(image_paths)} images in folder[/green]")
        
        return image_paths
    
    def get_page_count(self, pdf_path: Path) -> int:
        """
        Get the number of pages in a PDF without converting.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Number of pages
        """
        try:
            from pdf2image import pdfinfo_from_path
            info = pdfinfo_from_path(str(pdf_path))
            return info.get("Pages", 0)
        except ImportError:
            # Fallback: convert and count
            images = self.convert_pdf_to_images(pdf_path)
            return len(images)
        except Exception:
            return 0
    
    def cleanup(self) -> None:
        """Clean up temporary directory if used."""
        if self._temp_dir:
            self._temp_dir.cleanup()
            self._temp_dir = None
