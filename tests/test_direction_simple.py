"""Simple test for DirectionToggle widget."""
from app import DirectionToggle

def test_initial_state():
    widget = DirectionToggle()
    assert widget.direction == "ja_to_en"

if __name__ == "__main__":
    test_initial_state()
