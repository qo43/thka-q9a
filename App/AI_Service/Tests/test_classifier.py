"""
Test the classifier with both Arabic and English inputs.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.classifier import classify_with_ollama

def test_arabic_classification():
    """Test Arabic case classification."""
    text = "أطلب وقف تنفيذ قرار إداري صادر بحقي لأنه يسبب ضررًا مباشرًا."
    
    print("Testing Arabic classification...")
    print(f"Input text: {text}")
    print("-" * 80)
    
    result = classify_with_ollama(text, lang="ar")
    
    print(f"Request ID: {result.get('request_id')}")
    print(f"Model: {result.get('model')}")
    print(f"Latency: {result.get('latency_ms')} ms")
    print(f"Case Type: {result.get('case_type')}")
    print(f"Urgency: {result.get('urgency')}")
    print(f"Handling Unit: {result.get('handling_unit')}")
    print(f"Confidence: {result.get('confidence')}")
    print(f"Reason: {result.get('reason')}")
    print(f"Highlights: {result.get('highlights')}")
    print()

def test_english_classification():
    """Test English case classification."""
    text = "I request an urgent injunction to stop an administrative decision that causes me direct harm."
    
    print("Testing English classification...")
    print(f"Input text: {text}")
    print("-" * 80)
    
    result = classify_with_ollama(text, lang="en")
    
    print(f"Request ID: {result.get('request_id')}")
    print(f"Model: {result.get('model')}")
    print(f"Latency: {result.get('latency_ms')} ms")
    print(f"Case Type: {result.get('case_type')}")
    print(f"Urgency: {result.get('urgency')}")
    print(f"Handling Unit: {result.get('handling_unit')}")
    print(f"Confidence: {result.get('confidence')}")
    print(f"Reason: {result.get('reason')}")
    print(f"Highlights: {result.get('highlights')}")
    print()

if __name__ == "__main__":
    test_arabic_classification()
    test_english_classification()
