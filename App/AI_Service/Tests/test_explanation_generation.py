"""
Test script for Legal Explanation Generation

Tests the explanation generator with various OCR text samples including:
- Clean text
- Noisy OCR text with artifacts
- Short and long documents
- Different legal case types
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.explaination_generation import generate_explanation


# Sample OCR texts (simulating real OCR output with various quality levels)

# Sample 1: Clean administrative case
SAMPLE_AR_ADMIN_CLEAN = """
أطلب وقف تنفيذ قرار إداري صادر من الجهة الحكومية بتاريخ 15/3/1446هـ
القرار يتعلق بإيقاف الخدمة دون مبرر واضح
تم تقديم اعتراض سابق لم يتم الرد عليه
الضرر المترتب على القرار فوري ولا يمكن تداركه
"""

# Sample 2: Noisy OCR - financial case
SAMPLE_AR_FINANCIAL_NOISY = """
اطالب  بمستحقاتي  الماليه  عن  عقد  توريد
المبلغ:  250،000  ريال
تاريخ   استحقاق:   1/12/1445
لم  يتم  السداد   رغم   المراسلات   المتكرره
ارفقت  نسخه  من  العقد   والفواتير
"""

# Sample 3: Long enforcement case
SAMPLE_AR_ENFORCEMENT_LONG = """
لدي حكم نهائي صادر من المحكمة العامة بالرياض
رقم الحكم: 12345/1/ق لعام 1445هـ
الحكم يقضي بإلزام المدعى عليه بسداد مبلغ 500,000 ريال
تم تبليغ المحكوم عليه بالحكم بتاريخ 20/5/1445هـ
مضى أكثر من ستة أشهر على صدور الحكم دون تنفيذ
تم تقديم طلب للتنفيذ لكن لم يتم اتخاذ أي إجراء
المحكوم عليه لديه أصول وممتلكات معروفة
أطلب مباشرة إجراءات التنفيذ الجبري
"""

# Sample 4: Very noisy OCR with artifacts
SAMPLE_AR_NOISY_ARTIFACTS = """
اتقدم   بطلب   الغاء   قرار   اداري
ص ادر   من   ج هة   حك وميه
بتاريخ   ١٥/٣/١٤٤٦   هـ
القرار   يتعلق   بايقاف   الخدمه
دون   مبرر   واضح   |||
تم   تقديم   اعتراض   >>>
لم   يتم   الرد   عليه   ###
"""

# Sample 5: English administrative case
SAMPLE_EN_ADMIN = """
Request to cancel administrative decision
Issued by government agency on 15/03/2024
Decision relates to service suspension without clear justification
Previous objection submitted but not responded to
Damage from decision is immediate and irreparable
"""

# Sample 6: English financial case - noisy
SAMPLE_EN_FINANCIAL_NOISY = """
Claim   for   overdue   payments   from   supply   contract
Amount:   SAR   250,000
Due   date:   01/12/2023
Payment   not   made   despite   repeated   correspondence
Attached   copy   of   contract   and   invoices   |||
"""


def test_single_case(ocr_text: str, lang: str, case_name: str):
    """Test a single OCR text sample."""
    print(f"\n{'='*80}")
    print(f"Test Case: {case_name}")
    print(f"Language: {lang}")
    print(f"{'='*80}")
    print(f"Input OCR Text (first 100 chars):")
    print(f"{ocr_text[:100]}...")
    print(f"-" * 80)
    
    result = generate_explanation(ocr_text, lang=lang)
    
    print(f"Success: {result['success']}")
    print(f"Latency: {result['latency_ms']} ms")
    print(f"Request ID: {result['request_id']}")
    print(f"Model: {result['model']}")
    
    if result['success']:
        print(f"\nGenerated Legal Text:")
        print(f"-" * 80)
        print(result['message'])
    else:
        print(f"\nFailure Reason: {result['reason']}")
    
    print(f"{'='*80}\n")
    
    return result


def main():
    """Run all test cases."""
    print("=" * 80)
    print("Legal Explanation Generation - Test Suite")
    print("=" * 80)
    
    test_cases = [
        (SAMPLE_AR_ADMIN_CLEAN, "ar", "Arabic - Clean Admin Case"),
        (SAMPLE_AR_FINANCIAL_NOISY, "ar", "Arabic - Noisy Financial Case"),
        (SAMPLE_AR_ENFORCEMENT_LONG, "ar", "Arabic - Long Enforcement Case"),
        (SAMPLE_AR_NOISY_ARTIFACTS, "ar", "Arabic - Very Noisy with Artifacts"),
        (SAMPLE_EN_ADMIN, "en", "English - Administrative Case"),
        (SAMPLE_EN_FINANCIAL_NOISY, "en", "English - Noisy Financial Case"),
    ]
    
    results = []
    for ocr_text, lang, name in test_cases:
        result = test_single_case(ocr_text, lang, name)
        results.append({
            "name": name,
            "success": result['success'],
            "latency_ms": result['latency_ms'],
        })
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    avg_latency = sum(r['latency_ms'] for r in results) / total if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Success Rate: {successful/total*100:.1f}%")
    print(f"Average Latency: {avg_latency:.0f} ms")
    print(f"{'='*80}")
    
    # List failures
    failures = [r for r in results if not r['success']]
    if failures:
        print("\nFailed Tests:")
        for r in failures:
            print(f"  - {r['name']}")


if __name__ == "__main__":
    main()
