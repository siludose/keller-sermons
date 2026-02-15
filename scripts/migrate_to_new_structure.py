#!/usr/bin/env python3
"""
Migration Script: Legacy MD files -> New folder structure
Safely migrates existing sermon files to new organized structure.
"""

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import argparse

# Import our custom modules
try:
    from sermon_model import Sermon
    from md_beautifier import beautify_all
    from file_normalizer import (
        to_folder_name,
        get_legacy_md_files,
        normalize_sermon_name
    )
except ImportError:
    print("❌ Error: Cannot import required modules.")
    print("Make sure sermon_model.py, md_beautifier.py, and file_normalizer.py are in the same directory.")
    sys.exit(1)


class MigrationManager:
    """Manages the migration process with safety checks and rollback capability"""

    def __init__(self, base_dir: Path, dry_run: bool = False, smart_beautify: bool = False):
        self.base_dir = base_dir
        self.dry_run = dry_run
        self.smart_beautify = smart_beautify
        self.sermons_dir = base_dir / "sermons"
        self.backup_dir = None
        self.migration_log: List[Dict[str, Any]] = []
        self.smart_beautifier = None

        # 初始化智能美化器（如果需要）
        if smart_beautify and not dry_run:
            try:
                from smart_beautifier import ChunkedSmartBeautifier
                from translate_sermons import get_translation_backend
                backend_name, client = get_translation_backend()
                self.smart_beautifier = ChunkedSmartBeautifier(backend_name, client)
                print(f"✨ 智能美化已启用（使用 {backend_name} 后端）")
            except Exception as e:
                print(f"⚠️  智能美化器初始化失败: {e}")
                print(f"   将使用基础美化")
                self.smart_beautify = False

    def create_backup(self) -> Path:
        """Create timestamped backup of all sermon files"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_dir = self.base_dir / "backup" / f"migration_{timestamp}"

        if self.dry_run:
            print(f"[DRY RUN] Would create backup at: {backup_dir}")
            return backup_dir

        backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"📦 Creating backup at: {backup_dir}")

        # Copy all legacy MD files
        md_files = get_legacy_md_files(self.base_dir)
        for md_file in md_files:
            dest = backup_dir / md_file.name
            shutil.copy2(md_file, dest)
            print(f"  ✓ Backed up: {md_file.name}")

        print(f"✅ Backup complete: {len(md_files)} files")
        return backup_dir

    def migrate_sermon(self, md_file: Path) -> Dict[str, Any]:
        """
        Migrate a single sermon file to new structure.
        Returns migration result dict.
        """
        result = {
            "file": md_file.name,
            "success": False,
            "folder": None,
            "issues": [],
            "stats": {}
        }

        try:
            # Parse sermon
            print(f"\n📖 Processing: {md_file.name}")
            sermon = Sermon.from_legacy_md(md_file)

            # Validate
            issues = sermon.validate()
            result["issues"] = issues
            if issues:
                print(f"  ⚠️  Issues found:")
                for issue in issues:
                    print(f"     - {issue}")

            # Get stats
            result["stats"] = sermon.get_stats()

            # Beautify content
            if not self.dry_run:
                if self.smart_beautify and self.smart_beautifier:
                    print(f"  ✨ 智能美化内容（使用 LLM）...")
                    try:
                        # 智能美化转录和翻译
                        if sermon.transcript:
                            sermon.transcript = self.smart_beautifier.beautify_transcript(
                                sermon.transcript,
                                sermon.metadata.title
                            )
                        if sermon.translation:
                            sermon.translation = self.smart_beautifier.beautify_translation(
                                sermon.translation,
                                sermon.metadata.title
                            )
                        if sermon.outline:
                            sermon.outline = self.smart_beautifier.beautify_outline(
                                sermon.outline,
                                sermon.transcript
                            )
                    except Exception as e:
                        print(f"  ⚠️  智能美化失败: {e}")
                        print(f"  ⚠️  回退到基础美化")
                        sermon.outline, sermon.transcript, sermon.translation = beautify_all(
                            sermon.outline,
                            sermon.transcript,
                            sermon.translation
                        )
                else:
                    print(f"  ✨ 基础美化...")
                    sermon.outline, sermon.transcript, sermon.translation = beautify_all(
                        sermon.outline,
                        sermon.transcript,
                        sermon.translation
                    )

            # Determine folder name
            folder_name = to_folder_name(md_file.name)
            folder_path = self.sermons_dir / folder_name
            result["folder"] = folder_name

            if self.dry_run:
                print(f"  [DRY RUN] Would create: sermons/{folder_name}/")
                print(f"     - metadata.json")
                if sermon.outline:
                    print(f"     - outline.md ({len(sermon.outline)} chars)")
                print(f"     - transcript.md ({len(sermon.transcript)} chars)")
                print(f"     - translation.md ({len(sermon.translation)} chars)")
            else:
                # Write to new structure
                print(f"  📁 Creating: sermons/{folder_name}/")
                sermon.to_new_structure(folder_path)
                print(f"  ✅ Migration complete")

            result["success"] = True

        except Exception as e:
            result["success"] = False
            result["issues"].append(f"Error: {str(e)}")
            print(f"  ❌ Error: {e}")

        return result

    def migrate_all(self, md_files: List[Path]) -> None:
        """Migrate all sermon files"""
        print(f"\n🚀 Starting migration of {len(md_files)} sermons...")
        print(f"   Dry run: {self.dry_run}")
        print(f"   Target: {self.sermons_dir}")

        # Create backup
        if not self.dry_run:
            self.backup_dir = self.create_backup()

        # Create sermons directory
        if not self.dry_run:
            self.sermons_dir.mkdir(exist_ok=True)
        else:
            print(f"\n[DRY RUN] Would create: {self.sermons_dir}/")

        # Migrate each sermon
        for md_file in md_files:
            result = self.migrate_sermon(md_file)
            self.migration_log.append(result)

        # Generate report
        self.generate_report()

    def generate_report(self) -> None:
        """Generate migration report"""
        print("\n" + "="*60)
        print("📊 MIGRATION REPORT")
        print("="*60)

        total = len(self.migration_log)
        successful = sum(1 for r in self.migration_log if r["success"])
        failed = total - successful

        print(f"\nTotal sermons: {total}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")

        # Show issues
        issues_count = sum(len(r["issues"]) for r in self.migration_log)
        if issues_count > 0:
            print(f"\n⚠️  Total issues found: {issues_count}")
            print("\nSermons with issues:")
            for result in self.migration_log:
                if result["issues"]:
                    print(f"\n  {result['file']}:")
                    for issue in result["issues"]:
                        print(f"    - {issue}")

        # Show failures
        if failed > 0:
            print(f"\n❌ Failed migrations:")
            for result in self.migration_log:
                if not result["success"]:
                    print(f"  - {result['file']}")

        # Content statistics
        print(f"\n📈 Content Statistics:")
        total_outline_chars = sum(r["stats"].get("outline_length", 0) for r in self.migration_log)
        total_transcript_chars = sum(r["stats"].get("transcript_length", 0) for r in self.migration_log)
        total_translation_chars = sum(r["stats"].get("translation_length", 0) for r in self.migration_log)

        print(f"  Total outline content: {total_outline_chars:,} characters")
        print(f"  Total transcript content: {total_transcript_chars:,} characters")
        print(f"  Total translation content: {total_translation_chars:,} characters")

        # Save JSON report
        if not self.dry_run:
            report_path = self.base_dir / "migration_report.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.migration_log, f, indent=2, ensure_ascii=False)
            print(f"\n📄 Detailed report saved to: {report_path}")

        print("\n" + "="*60)

        if self.dry_run:
            print("\n💡 This was a DRY RUN. No files were modified.")
            print("   Run without --dry-run to perform actual migration.")


def rollback(base_dir: Path) -> None:
    """Rollback migration by restoring from backup"""
    backup_base = base_dir / "backup"
    if not backup_base.exists():
        print("❌ No backup directory found")
        return

    # Find most recent migration backup
    migration_backups = sorted(backup_base.glob("migration_*"), reverse=True)
    if not migration_backups:
        print("❌ No migration backups found")
        return

    latest_backup = migration_backups[0]
    print(f"🔄 Rolling back from: {latest_backup}")

    # Confirm
    response = input("This will delete sermons/ directory and restore files. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Rollback cancelled")
        return

    # Delete sermons directory
    sermons_dir = base_dir / "sermons"
    if sermons_dir.exists():
        print(f"🗑️  Deleting: {sermons_dir}")
        shutil.rmtree(sermons_dir)

    # Restore files to root
    md_files = list(latest_backup.glob("*.md"))
    print(f"📦 Restoring {len(md_files)} files...")

    for md_file in md_files:
        dest = base_dir / md_file.name
        shutil.copy2(md_file, dest)
        print(f"  ✓ Restored: {md_file.name}")

    print(f"✅ Rollback complete!")


def verify(base_dir: Path) -> None:
    """Quick verification check"""
    sermons_dir = base_dir / "sermons"

    if not sermons_dir.exists():
        print("❌ sermons/ directory not found. Run migration first.")
        return

    folders = [f for f in sermons_dir.iterdir() if f.is_dir()]
    print(f"📁 Found {len(folders)} sermon folders")

    # Check for required files
    missing_metadata = []
    missing_transcript = []
    missing_translation = []

    for folder in folders:
        if not (folder / "metadata.json").exists():
            missing_metadata.append(folder.name)
        if not (folder / "transcript.md").exists():
            missing_transcript.append(folder.name)
        if not (folder / "translation.md").exists():
            missing_translation.append(folder.name)

    # Report
    print(f"\n📊 Verification Results:")
    print(f"  Total folders: {len(folders)}")
    print(f"  Missing metadata.json: {len(missing_metadata)}")
    print(f"  Missing transcript.md: {len(missing_transcript)}")
    print(f"  Missing translation.md: {len(missing_translation)}")

    if missing_metadata or missing_transcript or missing_translation:
        print(f"\n⚠️  Issues found:")
        if missing_metadata:
            print(f"  Folders missing metadata.json:")
            for name in missing_metadata[:5]:
                print(f"    - {name}")
            if len(missing_metadata) > 5:
                print(f"    ... and {len(missing_metadata) - 5} more")

        if missing_transcript:
            print(f"  Folders missing transcript.md:")
            for name in missing_transcript[:5]:
                print(f"    - {name}")
            if len(missing_transcript) > 5:
                print(f"    ... and {len(missing_transcript) - 5} more")

        if missing_translation:
            print(f"  Folders missing translation.md:")
            for name in missing_translation[:5]:
                print(f"    - {name}")
            if len(missing_translation) > 5:
                print(f"    ... and {len(missing_translation) - 5} more")
    else:
        print(f"\n✅ All checks passed!")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate sermon MD files to new folder structure"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration without making changes"
    )
    parser.add_argument(
        "--file",
        help="Migrate a single file (for testing)"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Migrate all sermon files"
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback migration from backup"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify migrated content"
    )
    parser.add_argument(
        "--smart-beautify",
        action="store_true",
        help="Use LLM for intelligent formatting (adds subheadings, better paragraphs)"
    )

    args = parser.parse_args()

    # Determine base directory (script location's parent)
    base_dir = Path(__file__).parent.parent

    # Handle commands
    if args.rollback:
        rollback(base_dir)
        return

    if args.verify:
        verify(base_dir)
        return

    # Migration
    manager = MigrationManager(
        base_dir,
        dry_run=args.dry_run,
        smart_beautify=args.smart_beautify
    )

    if args.file:
        # Single file migration
        md_path = base_dir / f"{args.file}.md"
        if not md_path.exists():
            # Try backup directory
            md_path = base_dir / "backup" / f"{args.file}.md"
        if not md_path.exists():
            print(f"❌ File not found: {args.file}.md")
            sys.exit(1)

        manager.migrate_all([md_path])

    elif args.batch:
        # Batch migration
        # Check backup directory first
        backup_dir = base_dir / "backup"
        if backup_dir.exists():
            md_files = get_legacy_md_files(backup_dir)
            if md_files:
                print(f"📦 Found {len(md_files)} sermon files in backup/")
            else:
                md_files = get_legacy_md_files(base_dir)
        else:
            md_files = get_legacy_md_files(base_dir)

        if not md_files:
            print("❌ No sermon files found to migrate")
            sys.exit(1)

        manager.migrate_all(md_files)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
