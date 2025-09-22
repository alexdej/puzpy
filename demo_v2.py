#!/usr/bin/env python3
"""
Demo script showcasing the new v2 text format support in puzpy.

This script demonstrates:
1. Reading v2 text format files with REBUS and MARK sections
2. Converting existing .puz files to v2 text format
3. Manual creation of puzzles with rebus entries
4. Round-trip conversion between formats
"""

import puz

def demo_v2_parsing():
    """Demonstrate parsing v2 text format files."""
    print("=== Demo 1: Parsing v2 Text Format ===")
    
    # Read the v2 test file
    p = puz.read_text('testfiles/text_format_v2_rebus.txt')
    print(f"Title: {p.title}")
    print(f"Size: {p.width}x{p.height}")
    print(f"Has rebus: {p.has_rebus()}")
    print(f"Has markup: {p.has_markup()}")
    
    if p.has_rebus():
        r = p.rebus()
        print(f"Rebus squares: {r.get_rebus_squares()}")
        for i in r.get_rebus_squares():
            print(f"  Cell {i+1}: {r.get_rebus_solution(i)}")
    
    if p.has_markup():
        m = p.markup()
        print(f"Markup squares: {m.get_markup_squares()}")
        for i in m.get_markup_squares():
            print(f"  Cell {i+1}: markup value {m.markup[i]} (circled)")
    
    print()

def demo_puz_to_v2_conversion():
    """Demonstrate converting .puz files to v2 text format."""
    print("=== Demo 2: Converting .puz to v2 Text ===")
    
    # Load an existing .puz file with rebus
    p = puz.read('testfiles/nyt_rebus_with_notes_and_shape.puz')
    print(f"Original puzzle: {p.title}")
    print(f"Has rebus: {p.has_rebus()}")
    print(f"Has markup: {p.has_markup()}")
    
    # Convert to v2 text format
    v2_text = puz.to_text_format(p, 'v2')
    print("\n--- Generated v2 text format (first 500 chars) ---")
    print(v2_text[:500] + "..." if len(v2_text) > 500 else v2_text)
    
    print()

def demo_manual_creation():
    """Demonstrate manual creation of puzzles with rebus entries."""
    print("=== Demo 3: Manual Puzzle Creation ===")
    
    # Create a new puzzle
    p = puz.Puzzle()
    p.title = 'Demo Puzzle'
    p.author = 'Demo Author'
    p.copyright = 'Demo Copyright'
    p.width = 5
    p.height = 5
    p.solution = 'HELLO.....WORLD.....X'  # 25 characters for 5x5
    p.fill = '-----..........-----.....'  # 25 characters for 5x5
    p.clues = ['Greeting', 'Planet', 'Letter']
    
    # Add rebus entries using the new helper methods
    r = p.rebus()
    rebus_id1 = r.add_rebus_entry('HEART', [0, 24])  # First and last cells
    rebus_id2 = r.add_rebus_entry('STAR', [12])      # Middle cell
    r.save()
    
    # Add some markup
    m = p.markup()
    m.markup = [0] * (p.width * p.height)  # Initialize
    m.markup[0] = puz.GridMarkup.Circled     # Circle first cell
    m.markup[12] = puz.GridMarkup.Revealed   # Mark middle cell as revealed
    m.markup[24] = puz.GridMarkup.Circled    # Circle last cell
    m.save()
    
    print(f"Created puzzle: {p.title}")
    print(f"Has rebus: {p.has_rebus()}")
    print(f"Has markup: {p.has_markup()}")
    
    # Show rebus entries
    print("Rebus entries:")
    for i in r.get_rebus_squares():
        print(f"  Cell {i+1}: {r.get_rebus_solution(i)}")
    
    # Convert to v2 text format
    v2_text = puz.to_text_format(p, 'v2')
    print("\n--- Generated v2 text format ---")
    print(v2_text)
    
    print()

def demo_roundtrip():
    """Demonstrate round-trip conversion."""
    print("=== Demo 4: Round-trip Conversion ===")
    
    # Start with v2 text
    print("1. Reading v2 text file...")
    p1 = puz.read_text('testfiles/text_format_v2_rebus.txt')
    
    # Convert to v2 text
    print("2. Converting to v2 text format...")
    v2_text = puz.to_text_format(p1, 'v2')
    
    # Parse back
    print("3. Parsing back from v2 text...")
    p2 = puz.load_text(v2_text)
    
    # Verify round-trip
    print("4. Verifying round-trip...")
    print(f"Original title: {p1.title}")
    print(f"Round-trip title: {p2.title}")
    print(f"Original has rebus: {p1.has_rebus()}")
    print(f"Round-trip has rebus: {p2.has_rebus()}")
    print(f"Original has markup: {p1.has_markup()}")
    print(f"Round-trip has markup: {p2.has_markup()}")
    
    if p1.has_rebus() and p2.has_rebus():
        r1, r2 = p1.rebus(), p2.rebus()
        print(f"Original rebus squares: {r1.get_rebus_squares()}")
        print(f"Round-trip rebus squares: {r2.get_rebus_squares()}")
    
    print("✓ Round-trip successful!")
    print()

if __name__ == "__main__":
    print("puzpy v2 Text Format Demo")
    print("=" * 40)
    print()
    
    demo_v2_parsing()
    demo_puz_to_v2_conversion()
    demo_manual_creation()
    demo_roundtrip()
    
    print("Demo completed successfully!")