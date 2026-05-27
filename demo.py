"""
Self-contained demo for the Phase 1 Email Agent.

Resets state for a clean, repeatable run, then walks through:
  1. The incoming mixed mailbox (FX trades + office noise)
  2. Live classification by the agent
  3. The structured case output handed off to Phase 2
  4. A second run proving deduplication (no double-processing)

Run from the email_agent/ folder:
    python demo.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

from agent.email_agent import EmailAgentRunner
from classifier.rule_classifier import RuleClassifier
from config.settings import EmailAgentConfig
from connectors.local_connector import LocalEmailConnector
from storage.db_index import DBIndex
from storage.file_store import FileStore
from utils.logger import setup_logging

BAR = "=" * 64


def banner(text: str) -> None:
    print(f"\n{BAR}\n  {text}\n{BAR}", flush=True)


def step(text: str) -> None:
    print(f"\n>>> {text}\n", flush=True)


def reset_state(cfg: EmailAgentConfig) -> None:
    """Fresh inbox + wiped output so the demo is repeatable."""
    subprocess.run(
        [sys.executable, str(Path("tools") / "generate_test_emails.py"), "--clean"],
        check=True,
    )
    processed = Path(cfg.processed_path)
    if processed.exists():
        shutil.rmtree(processed)
    db = Path(cfg.db_path)
    if db.exists():
        db.unlink()


def preview_inbox(cfg: EmailAgentConfig) -> None:
    emails = LocalEmailConnector(cfg.inbox_path).fetch_emails()
    print(f"   {len(emails)} emails landed in the shared mailbox — a realistic mix:\n", flush=True)
    samples = [
        "FX Trade Settlement[FXOPT-2026-00047]",
        "FXOPT-2026-00055",
        "Settlement query",
        "Happy Birthday",
        "IT Support",
        "Out of Office",
    ]
    for needle in samples:
        match = next((e for e in emails if needle in e["subject"]), None)
        if match:
            print(f"     • {match['subject']}", flush=True)
    print("\n   The agent must keep the real FX trades and discard the noise.", flush=True)


def show_output(cfg: EmailAgentConfig) -> None:
    processed = Path(cfg.processed_path)
    cases = sorted(p for p in processed.iterdir() if p.is_dir())
    print(f"   {len(cases)} structured case folders created in {processed}/\n", flush=True)
    for c in cases[:4]:
        print(f"     • {c.name}/", flush=True)
        print("         email_body.txt, email_metadata.json, manifest.json", flush=True)
    if len(cases) > 4:
        print(f"     • ... and {len(cases) - 4} more", flush=True)

    sample = cases[0] / "manifest.json"
    print(f"\n   Sample handoff manifest ({sample.parent.name}/manifest.json):\n", flush=True)
    import json
    m = json.loads(sample.read_text(encoding="utf-8"))
    print(f"       trade_id            : {m['trade_id']}", flush=True)
    print(f"       asset_class         : {m['asset_class']}", flush=True)
    print(f"       label / confidence  : {m['classification']['label']} ({m['classification']['confidence']})", flush=True)
    print(f"       ready_for_extraction: {m['ready_for_extraction']}", flush=True)


def build_runner(cfg: EmailAgentConfig) -> EmailAgentRunner:
    return EmailAgentRunner(
        cfg,
        LocalEmailConnector(cfg.inbox_path),
        RuleClassifier(cfg),
        FileStore(cfg.processed_path),
        DBIndex(cfg.db_path),
    )


def main() -> None:
    cfg = EmailAgentConfig()
    setup_logging(cfg.log_dir)

    banner("NOMURA SSG  —  EMAIL AGENT (PHASE 1)  DEMO")

    step("[1/4] Preparing a clean run (regenerating inbox, wiping prior output)")
    reset_state(cfg)

    step("[2/4] Incoming mailbox")
    preview_inbox(cfg)

    step("[3/4] Running the Email Agent — live classification")
    runner = build_runner(cfg)
    stats = runner.run()
    runner.db.close()

    step("[4/4] Output — structured cases ready for Phase 2 (Extraction Agent)")
    show_output(cfg)

    step("Re-running to prove deduplication — nothing gets processed twice")
    runner2 = build_runner(cfg)
    stats2 = runner2.run()
    runner2.db.close()

    banner("DEMO COMPLETE")
    print(f"  First run : {stats.relevant} stored, "
          f"{stats.ambiguous} ambiguous, {stats.irrelevant} irrelevant, "
          f"{stats.duplicate} duplicate", flush=True)
    print(f"  Second run: {stats2.relevant} stored, "
          f"{stats2.already_processed} already processed "
          f"(deduplication working)\n", flush=True)


if __name__ == "__main__":
    main()
