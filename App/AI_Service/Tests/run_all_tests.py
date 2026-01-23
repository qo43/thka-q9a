"""
Batch test script for all test cases in test_cases.json
"""
import json
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.classifier import classify_with_ollama


def load_test_cases(json_path: Path) -> List[Dict]:
    """Load test cases from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_single_test(test_case: Dict, lang: str = "ar") -> Dict:
    """Run a single test case and return results."""
    test_id = test_case.get("id", "UNKNOWN")
    text = test_case.get("text", "")
    expected = test_case.get("expected", {})
    
    print(f"\n{'='*80}")
    print(f"Test ID: {test_id}")
    print(f"Input: {text[:80]}..." if len(text) > 80 else f"Input: {text}")
    print(f"Expected: {expected}")
    print("-" * 80)
    
    # Classify
    result = classify_with_ollama(text, lang=lang)
    
    # Compare
    actual = {
        "case_type": result.get("case_type"),
        "urgency": result.get("urgency"),
        "handling_unit": result.get("handling_unit"),
    }
    
    # Check if match
    match = actual == expected
    status = "✓ PASS" if match else "✗ FAIL"
    
    print(f"Actual: {actual}")
    print(f"Confidence: {result.get('confidence'):.2f}")
    print(f"Reason: {result.get('reason')}")
    print(f"Latency: {result.get('latency_ms')} ms")
    print(f"Status: {status}")
    
    return {
        "test_id": test_id,
        "passed": match,
        "expected": expected,
        "actual": actual,
        "confidence": result.get("confidence"),
        "reason": result.get("reason"),
        "latency_ms": result.get("latency_ms"),
    }


def main():
    """Run all test cases and generate summary."""
    test_file = Path(__file__).parent / "test_cases.json"
    
    if not test_file.exists():
        print(f"Error: Test file not found: {test_file}")
        sys.exit(1)
    
    print(f"Loading test cases from: {test_file}")
    test_cases = load_test_cases(test_file)
    print(f"Loaded {len(test_cases)} test cases\n")
    
    # Run all tests
    results = []
    for test_case in test_cases:
        result = run_single_test(test_case, lang="ar")
        results.append(result)
    
    # Summary
    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed
    pass_rate = (passed / len(results) * 100) if results else 0
    avg_confidence = sum(r["confidence"] for r in results) / len(results) if results else 0
    avg_latency = sum(r["latency_ms"] for r in results) / len(results) if results else 0
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    print(f"Average Confidence: {avg_confidence:.2f}")
    print(f"Average Latency: {avg_latency:.0f} ms")
    print(f"{'='*80}")
    
    # Show failed tests
    if failed > 0:
        print("\nFailed Tests:")
        for r in results:
            if not r["passed"]:
                print(f"  {r['test_id']}: Expected {r['expected']}, Got {r['actual']}")
    
    # Save results to file
    output_file = Path(__file__).parent / "test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    main()
