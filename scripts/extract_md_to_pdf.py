#!/usr/bin/env python3
"""
Extract Markdown cells from Jupyter Notebook and convert to PDF using Pandoc.

This script reads a Jupyter Notebook (.ipynb) file, extracts only the markdown cells,
saves them as a .md file, and then converts that .md file to PDF using Pandoc.

Usage:
    python extract_md_to_pdf.py notebook.ipynb output.pdf [options]

Dependencies:
    - Python 3.8+
    - nbformat
    - Pandoc installed on system PATH
"""

import argparse
import sys
import subprocess
import shutil
from pathlib import Path
import tempfile
import os

try:
    import nbformat
except ImportError:
    print("Error: nbformat is required. Install with: pip install nbformat")
    sys.exit(1)


def check_pandoc():
    """Check if Pandoc is installed and accessible."""
    if not shutil.which("pandoc"):
        print("Error: Pandoc is not installed or not in PATH.")
        print("Please install Pandoc from: https://pandoc.org/installing.html")
        return False
    return True


def extract_markdown_cells(notebook_path):
    """
    Extract markdown cells from a Jupyter notebook.
    
    Args:
        notebook_path (str): Path to the .ipynb file
        
    Returns:
        str: Combined markdown content from all markdown cells
        
    Raises:
        FileNotFoundError: If notebook file doesn't exist
        ValueError: If notebook format is invalid
    """
    notebook_path = Path(notebook_path)
    
    if not notebook_path.exists():
        raise FileNotFoundError(f"Notebook file not found: {notebook_path}")
    
    if not notebook_path.suffix.lower() == '.ipynb':
        raise ValueError(f"File must be a .ipynb notebook: {notebook_path}")
    
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = nbformat.read(f, as_version=4)
    except Exception as e:
        raise ValueError(f"Failed to read notebook: {e}")
    
    markdown_content = []
    
    for cell in notebook.cells:
        if cell.cell_type == 'markdown':
            markdown_content.append(cell.source)
    
    if not markdown_content:
        print("Warning: No markdown cells found in the notebook.")
        return ""
    
    return '\n\n'.join(markdown_content)


def write_markdown_file(content, output_path):
    """
    Write markdown content to a file.
    
    Args:
        content (str): Markdown content
        output_path (str): Path for the .md file
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        raise IOError(f"Failed to write markdown file: {e}")


def convert_to_pdf(md_path, pdf_path, pandoc_options=None):
    """
    Convert markdown file to PDF using Pandoc.
    
    Args:
        md_path (str): Path to the .md file
        pdf_path (str): Path for the output .pdf file
        pandoc_options (list): Additional Pandoc options
        
    Raises:
        subprocess.CalledProcessError: If Pandoc conversion fails
    """
    cmd = ["pandoc", str(md_path), "-o", str(pdf_path)]
    
    # Add default options for better PDF output
    default_options = [
        "--pdf-engine=xelatex",  # Better Unicode support
        "--variable", "geometry:margin=1in",  # Set margins
        "--variable", "fontsize=12pt",  # Set font size
    ]
    
    # Use xelatex if available, fallback to default engine
    try:
        subprocess.run(["xelatex", "--version"], 
                      capture_output=True, check=True)
        cmd.extend(default_options)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to default PDF engine
        cmd.extend([
            "--variable", "geometry:margin=1in",
            "--variable", "fontsize=12pt",
        ])
    
    # Add custom options if provided
    if pandoc_options:
        cmd.extend(pandoc_options)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result
    except subprocess.CalledProcessError as e:
        error_msg = f"Pandoc conversion failed:\n"
        error_msg += f"Command: {' '.join(cmd)}\n"
        error_msg += f"Return code: {e.returncode}\n"
        if e.stderr:
            error_msg += f"Error output: {e.stderr}\n"
        raise subprocess.CalledProcessError(e.returncode, cmd, error_msg)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract markdown cells from Jupyter Notebook and convert to PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python extract_md_to_pdf.py notebook.ipynb output.pdf
    python extract_md_to_pdf.py notebook.ipynb output.pdf --keep-md
    python extract_md_to_pdf.py notebook.ipynb output.pdf --pandoc-options "--toc --number-sections"
        """
    )
    
    parser.add_argument(
        "notebook",
        help="Input Jupyter notebook file (.ipynb)"
    )
    
    parser.add_argument(
        "output",
        help="Output PDF file (.pdf)"
    )
    
    parser.add_argument(
        "--keep-md",
        action="store_true",
        help="Keep the intermediate markdown file"
    )
    
    parser.add_argument(
        "--pandoc-options",
        type=str,
        help="Additional Pandoc options (space-separated, in quotes)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_arguments()
    
    # Check if Pandoc is available
    if not check_pandoc():
        sys.exit(1)
    
    # Validate input file
    notebook_path = Path(args.notebook)
    if not notebook_path.exists():
        print(f"Error: Notebook file not found: {notebook_path}")
        sys.exit(1)
    
    # Prepare output path
    output_path = Path(args.output)
    if not output_path.suffix.lower() == '.pdf':
        output_path = output_path.with_suffix('.pdf')
    
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare markdown file path
    if args.keep_md:
        md_path = output_path.with_suffix('.md')
        temp_md = False
    else:
        # Use temporary file
        temp_fd, md_path = tempfile.mkstemp(suffix='.md')
        os.close(temp_fd)
        temp_md = True
    
    try:
        if args.verbose:
            print(f"Reading notebook: {notebook_path}")
        
        # Extract markdown cells
        markdown_content = extract_markdown_cells(notebook_path)
        
        if not markdown_content.strip():
            print("Warning: No markdown content found. Creating empty PDF.")
            markdown_content = "# No Markdown Content\n\nThis notebook contains no markdown cells."
        
        if args.verbose:
            print(f"Writing markdown to: {md_path}")
        
        # Write markdown file
        write_markdown_file(markdown_content, md_path)
        
        # Parse additional Pandoc options
        pandoc_options = []
        if args.pandoc_options:
            pandoc_options = args.pandoc_options.split()
        
        if args.verbose:
            print(f"Converting to PDF: {output_path}")
        
        # Convert to PDF
        convert_to_pdf(md_path, output_path, pandoc_options)
        
        print(f"Successfully created PDF: {output_path}")
        
        if args.keep_md:
            print(f"Markdown file saved: {md_path}")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    finally:
        # Clean up temporary markdown file
        if temp_md and Path(md_path).exists():
            try:
                os.unlink(md_path)
            except OSError:
                pass


if __name__ == "__main__":
    main() 