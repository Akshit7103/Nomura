"""Entry point for the Phase 1 Email Agent."""

from agent.email_agent import EmailAgentRunner
from classifier.rule_classifier import RuleClassifier
from config.settings import EmailAgentConfig
from connectors.local_connector import LocalEmailConnector
from storage.db_index import DBIndex
from storage.file_store import FileStore
from utils.logger import setup_logging


def main() -> None:
    cfg = EmailAgentConfig()
    setup_logging(cfg.log_dir)

    connector = LocalEmailConnector(cfg.inbox_path)
    classifier = RuleClassifier(cfg)
    store = FileStore(cfg.processed_path)
    db = DBIndex(cfg.db_path)

    runner = EmailAgentRunner(cfg, connector, classifier, store, db)
    runner.run()
    db.close()


if __name__ == "__main__":
    main()
