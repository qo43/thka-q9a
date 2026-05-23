"""
Simple PDF to JPG Converter - Easy to Use

Just put your PDF file in the AI_Service folder and run this script!
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pdf_converter import convert_pdf_to_jpg, get_pdf_info

def main():
    print("=" * 60)
    print("PDF to JPG Converter")
    print("=" * 60)
    
    # Check if user provided a PDF file path
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
    else:
        # Ask user to enter the PDF filename
        print("\nEnter the path to your PDF file:")
        print("(You can drag and drop the file here)")
        pdf_file = input("> ").strip().strip('"')
    
    # Check if file exists
    pdf_path = Path(pdf_file)
    if not pdf_path.exists():
        print(f"\n❌ Error: File not found: {pdf_file}")
        print("\nMake sure the file exists and try again.")
        return
    
    if not pdf_file.lower().endswith('.pdf'):
        print(f"\n❌ Error: File is not a PDF: {pdf_file}")
        return
    
    print(f"\n📄 PDF File: {pdf_path.name}")
    
    # Get PDF info
    try:
        info = get_pdf_info(pdf_path)
        print(f"📊 Pages: {info['page_count']}")
        print(f"💾 Size: {info['file_size_mb']} MB")
    except Exception as e:
        print(f"⚠️  Warning: Could not read PDF info: {e}")
    
    # Ask for output directory
    print("\nWhere to save JPG files? (press Enter for 'output' folder)")
    output_dir = input("> ").strip().strip('"')
    if not output_dir:
        output_dir = "output"
    
    print(f"\n🔄 Converting to JPG...")
    print(f"   Output folder: {output_dir}")
    
    try:
        # Convert PDF to JPG
        output_files = convert_pdf_to_jpg(
            pdf_path=pdf_path,
            output_dir=output_dir,
            dpi=200,      # Good quality
            quality=85,   # Good JPG quality
        )
        
        print(f"\n✅ Success! Generated {len(output_files)} image(s):")
        for i, file in enumerate(output_files, 1):
            file_size = Path(file).stat().st_size / 1024  # KB
            print(f"   {i}. {Path(file).name} ({file_size:.1f} KB)")
        
        print(f"\n📁 Files saved to: {Path(output_dir).absolute()}")
        
    except Exception as e:
        print(f"\n❌ Error during conversion: {e}")
        print("\n⚠️  Common issues:")
        print("   - Poppler not installed (required for PDF processing)")
        print("   - PDF is password-protected or corrupted")
        print("   - Insufficient disk space")
        return

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
    input("\nPress Enter to exit...")
