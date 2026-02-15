#!/usr/bin/env python3
"""
Migration Verification Script
Comprehensive checks for migrated sermon content integrity.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import argparse


class MigrationVerifier:
    """Verifies the integrity of migrated sermon content"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.sermons_dir = base_dir / "sermons"
        self.issues: List[Dict[str, Any]] = []

    def check_structure(self) -> bool:
        """Verify sermons directory exists"""
        if not self.sermons_dir.exists():
            self.issues.append({
                "severity": "critical",
                "category": "structure",
                "message": "sermons/ directory does not exist"
            })
            return False
        return True

    def get_sermon_folders(self) -> List[Path]:
        """Get all sermon folders"""
        if not self.sermons_dir.exists():
            return []
        return [f for f in self.sermons_dir.iterdir() if f.is_dir()]

    def verify_sermon_folder(self, folder: Path) -> Dict[str, Any]:
        """Verify a single sermon folder"""
        result = {
            "folder": folder.name,
            "valid": True,
            "issues": []
        }

        # Check for required files
        required_files = {
            "metadata.json": "Metadata file",
            "transcript.md": "English transcript",
            "translation.md": "Chinese translation"
        }

        for filename, description in required_files.items():
            file_path = folder / filename
            if not file_path.exists():
                result["valid"] = False
                result["issues"].append(f"Missing {description} ({filename})")

        # Check metadata.json
        metadata_path = folder / "metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                # Check required fields
                if not metadata.get("title"):
                    result["issues"].append("Metadata missing title")

                if not metadata.get("speaker"):
                    result["issues"].append("Metadata missing speaker")

            except json.JSONDecodeError as e:
                result["valid"] = False
                result["issues"].append(f"Invalid metadata.json: {e}")
            except Exception as e:
                result["valid"] = False
                result["issues"].append(f"Error reading metadata.json: {e}")

        # Check transcript.md
        transcript_path = folder / "transcript.md"
        if transcript_path.exists():
            try:
                content = transcript_path.read_text(encoding='utf-8')
                if len(content) < 500:
                    result["issues"].append(f"Transcript suspiciously short ({len(content)} chars)")

                # Check for encoding issues
                if '�' in content or '\ufffd' in content:
                    result["valid"] = False
                    result["issues"].append("Transcript contains encoding errors")

            except Exception as e:
                result["valid"] = False
                result["issues"].append(f"Error reading transcript.md: {e}")

        # Check translation.md
        translation_path = folder / "translation.md"
        if translation_path.exists():
            try:
                content = translation_path.read_text(encoding='utf-8')
                if len(content) < 500:
                    result["issues"].append(f"Translation suspiciously short ({len(content)} chars)")

                # Check for encoding issues
                if '�' in content or '\ufffd' in content:
                    result["valid"] = False
                    result["issues"].append("Translation contains encoding errors")

                # Check for Chinese characters
                has_chinese = any('\u4e00' <= char <= '\u9fff' for char in content)
                if not has_chinese:
                    result["issues"].append("Translation appears to have no Chinese characters")

            except Exception as e:
                result["valid"] = False
                result["issues"].append(f"Error reading translation.md: {e}")

        # Check outline.md (optional)
        outline_path = folder / "outline.md"
        if outline_path.exists():
            try:
                content = outline_path.read_text(encoding='utf-8')
                if not content.strip():
                    result["issues"].append("Outline file is empty")
            except Exception as e:
                result["issues"].append(f"Error reading outline.md: {e}")

        return result

    def verify_all(self) -> Dict[str, Any]:
        """Run all verification checks"""
        report = {
            "timestamp": str(Path(__file__).stat().st_mtime),
            "base_dir": str(self.base_dir),
            "structure_valid": False,
            "total_folders": 0,
            "valid_folders": 0,
            "folders_with_issues": 0,
            "critical_issues": 0,
            "warnings": 0,
            "details": []
        }

        # Check structure
        if not self.check_structure():
            print("❌ Critical: sermons/ directory not found")
            report["critical_issues"] += 1
            return report

        report["structure_valid"] = True
        print("✅ Structure: sermons/ directory exists")

        # Get folders
        folders = self.get_sermon_folders()
        report["total_folders"] = len(folders)
        print(f"📁 Found {len(folders)} sermon folders")

        if len(folders) == 0:
            print("⚠️  Warning: No sermon folders found")
            report["warnings"] += 1
            return report

        # Verify each folder
        print(f"\n🔍 Verifying {len(folders)} sermons...")
        for folder in folders:
            result = self.verify_sermon_folder(folder)
            report["details"].append(result)

            if result["valid"]:
                report["valid_folders"] += 1
                print(f"  ✅ {folder.name}")
            else:
                report["folders_with_issues"] += 1
                report["critical_issues"] += 1
                print(f"  ❌ {folder.name}")
                for issue in result["issues"]:
                    print(f"     - {issue}")

            # Count warnings (non-critical issues)
            if result["issues"] and result["valid"]:
                report["warnings"] += len(result["issues"])

        return report

    def print_summary(self, report: Dict[str, Any]) -> None:
        """Print verification summary"""
        print("\n" + "="*60)
        print("📊 VERIFICATION SUMMARY")
        print("="*60)

        print(f"\n✅ Valid folders: {report['valid_folders']}/{report['total_folders']}")
        print(f"⚠️  Folders with issues: {report['folders_with_issues']}")
        print(f"❌ Critical issues: {report['critical_issues']}")
        print(f"⚠️  Warnings: {report['warnings']}")

        # Show folders with issues
        if report["folders_with_issues"] > 0:
            print(f"\n⚠️  Folders requiring attention:")
            for detail in report["details"]:
                if not detail["valid"] or detail["issues"]:
                    print(f"\n  {detail['folder']}:")
                    for issue in detail["issues"]:
                        icon = "❌" if not detail["valid"] else "⚠️ "
                        print(f"    {icon} {issue}")

        # Overall status
        print("\n" + "="*60)
        if report["critical_issues"] == 0 and report["warnings"] == 0:
            print("🎉 All checks passed! Migration successful.")
            print("="*60)
            return True
        elif report["critical_issues"] == 0:
            print(f"✅ No critical issues, but {report['warnings']} warnings found.")
            print("   Review warnings above for potential improvements.")
            print("="*60)
            return True
        else:
            print(f"❌ {report['critical_issues']} critical issues found.")
            print("   Migration may have failed for some sermons.")
            print("="*60)
            return False

    def save_report(self, report: Dict[str, Any], output_path: Path) -> None:
        """Save verification report to JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Detailed report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Verify migrated sermon content"
    )
    parser.add_argument(
        "--output",
        help="Save verification report to file (JSON)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output for all sermons"
    )

    args = parser.parse_args()

    # Determine base directory
    base_dir = Path(__file__).parent.parent

    # Run verification
    verifier = MigrationVerifier(base_dir)
    report = verifier.verify_all()

    # Print summary
    success = verifier.print_summary(report)

    # Save report if requested
    if args.output:
        output_path = Path(args.output)
        verifier.save_report(report, output_path)
    else:
        # Save to default location
        default_output = base_dir / "verification_report.json"
        verifier.save_report(report, default_output)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
