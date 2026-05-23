import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    from core.ats_service import ats_service
    from core.cv_parser import cv_parser
    from main import app

    print(f"Imported FastAPI app: {app.title}")

    samples = [
        WORKSPACE_ROOT / "test" / "Abdelrahman_Abdo_Mansour_CV_c.pdf",
        WORKSPACE_ROOT / "test" / "business analyst.pdf",
        WORKSPACE_ROOT / "test" / "devops.pdf",
    ]
    existing_samples = [sample for sample in samples if sample.exists()]
    if not existing_samples:
        print("No local sample CVs found; import smoke check passed.")
        return 0

    for sample in existing_samples:
        text = cv_parser.parse(sample)
        if len(text) < 80:
            raise AssertionError(f"Extracted too little text from {sample.name}")

        ats = ats_service.evaluate(text)
        required_breakdown = {"job_alignment", "skills_coverage", "cv_structure", "impact_evidence"}
        if not 0 <= ats.score <= 100:
            raise AssertionError(f"ATS score out of range for {sample.name}: {ats.score}")
        if set(ats.score_breakdown) != required_breakdown:
            raise AssertionError(f"Unexpected ATS breakdown keys for {sample.name}: {ats.score_breakdown}")

        print(f"{sample.name}: parsed {len(text)} chars, ATS {ats.score} ({ats.label})")

    print("Smoke check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
