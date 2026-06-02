"""
Synthetic email generator for the Nomura SSG Email Agent (Phase 1).

Produces realistic FX Trade Settlement .eml files that mirror the real
sample emails (snapshots/), plus a controlled set of ambiguous and
irrelevant noise emails, so the rule-based classifier can be tested
end-to-end without live mailbox access.

Ground truth = the 3 real emails:
    FX Trade Settlement[FXOPT-2026-00036] - USD/CAD - 26_05_26 - UTI...
    Body: Trade Details (Deal Reference, Currency Pair, Buy/Sell, Amount,
          Counterparty, Value Date) + Settlement Instructions block.

Pure Python stdlib. No third-party dependencies.

Usage:
    python generate_test_emails.py --clean
    python generate_test_emails.py --output ../data/raw_emails/inbox --seed 42
"""

import argparse
import random
import string
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import format_datetime
from pathlib import Path

# --------------------------------------------------------------------------
# Data pools
# --------------------------------------------------------------------------

SENDER = "Aastha Makkar (IND) <aastha.makkar@protivitiglobal.in>"
RECIPIENTS = (
    "Akshit Mahajan (IND) <akshit.mahajan@protivitiglobal.in>, "
    "Manav Khatri (IND) <manav.khatri@protivitiglobal.in>"
)
CC = "Satyadarshi Mohanty (IND) <satyadarshi.mohanty@protivitiglobal.in>"

CURRENCY_PAIRS = [
    "EUR/USD", "USD/JPY", "GBP/USD", "USD/CAD",
    "EUR/GBP", "AUD/USD", "USD/SGD", "USD/CHF",
]

CURRENCY_SYMBOLS = {
    "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥",
    "CAD": "C$", "AUD": "A$", "SGD": "S$", "CHF": "CHF ",
}

COUNTERPARTIES = [
    {"name": "Barclays PLC",      "pay_to": "Barclays Bank PLC",        "swift": "BARCGB22", "account": "BARC-GBP-10001"},
    {"name": "Goldman Sachs",     "pay_to": "Goldman Sachs Bank USA",   "swift": "GOLDUS33", "account": "GSIB-USD-99001"},
    {"name": "Deutsche Bank AG",  "pay_to": "Deutsche Bank AG",         "swift": "DEUTDEDB", "account": "DB-EUR-55502"},
    {"name": "HSBC Bank PLC",     "pay_to": "HSBC Bank PLC",            "swift": "MIDLGB22", "account": "HSBC-USD-77410"},
    {"name": "JPMorgan Chase",    "pay_to": "JPMorgan Chase Bank N.A.", "swift": "CHASUS33", "account": "400-123456"},
    {"name": "Société Générale", "pay_to": "Société Générale SA", "swift": "SOGEFRPP", "account": "SG-EUR-30091"},
    {"name": "BNP Paribas",       "pay_to": "BNP Paribas SA",           "swift": "BNPAFRPP", "account": "BNP-EUR-41200"},
    {"name": "Citibank NA",       "pay_to": "Citibank N.A.",            "swift": "CITIGB2L", "account": "CITI-USD-88100"},
]

PAYMENT_METHODS = ["MT103", "MT202", "MT202COV"]
BUY_SELL = ["Buy", "Sell"]

SIGNATURES = [
    {"name": "PQR", "company": "ABCD LTD",          "phone": "8756762",  "domain": "xyz.com"},
    {"name": "MPN", "company": "ABCD LTD",          "phone": "64567832", "domain": "mpn.com"},
    {"name": "XYZ", "company": "ABCD LTD",          "phone": "88567432", "domain": "xyz.com"},
    {"name": "LMN", "company": "Global Markets LLP", "phone": "77234561", "domain": "gmllp.com"},
]

TRADE_DATE = "26/05/26"          # date the trades were "executed" (matches samples)
BASE_DT = datetime(2026, 5, 26, 9, 30, 0, tzinfo=timezone.utc)

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def random_uti(trade_num: int) -> str:
    """UTI<20 random A-Z0-9><4-digit trade number>, mirroring real format."""
    body = "".join(random.choices(string.ascii_uppercase + string.digits, k=20))
    return f"UTI{body}{trade_num:04d}"


def format_amount(currency: str) -> str:
    """Match the 3 amount styles seen in the real emails."""
    value = random.randint(100_000, 50_000_000)
    cents = random.choice(["00", "00", "50", f"{random.randint(0, 99):02d}"])
    style = random.choice(["code_comma", "symbol_comma", "symbol_plain"])
    sym = CURRENCY_SYMBOLS.get(currency, currency + " ")
    if style == "code_comma":
        return f"{currency} {value:,}.{cents}"
    if style == "symbol_comma":
        return f"{sym}{value:,}.{cents}"
    return f"{sym}{value}"


def random_value_date() -> str:
    offset = random.randint(30, 240)
    d = datetime(2026, 5, 26) + timedelta(days=offset)
    return d.strftime("%d-%b-%Y")


def _new_message(sender: str, subject: str, dt: datetime, msg_id: str,
                 to: str = RECIPIENTS, cc: str | None = CC) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    if cc:
        msg["Cc"] = cc
    msg["Subject"] = subject
    msg["Date"] = format_datetime(dt)
    msg["Message-ID"] = msg_id
    return msg


# --------------------------------------------------------------------------
# FX Trade Settlement email builder (RELEVANT)
# --------------------------------------------------------------------------


def build_trade_email(trade_num: int, dt: datetime, complete: bool = True,
                      force_trade_id: str | None = None) -> tuple[EmailMessage, str]:
    trade_id = force_trade_id or f"FXOPT-2026-{trade_num:05d}"
    pair = random.choice(CURRENCY_PAIRS)
    base_ccy = pair.split("/")[0]
    cp = random.choice(COUNTERPARTIES)
    sig = random.choice(SIGNATURES)
    uti = random_uti(trade_num)

    trade_details = {
        "Deal Reference": trade_id,
        "Currency Pair": pair,
        "Buy/Sell": random.choice(BUY_SELL),
        "Amount": format_amount(base_ccy),
        "Counterparty": cp["name"],
        "Value Date": random_value_date(),
    }
    ssi = {
        "Pay To": cp["pay_to"],
        "SWIFT Code": cp["swift"],
        "Account Number": cp["account"],
        "Beneficiary Name": cp["pay_to"],
        "Payment Method": random.choice(PAYMENT_METHODS),
    }

    # Partial emails: blank out 1-2 trade-detail fields (mirrors FXOPT-00005)
    if not complete:
        blankable = ["Currency Pair", "Counterparty", "Amount", "Value Date"]
        for field in random.sample(blankable, random.choice([1, 2])):
            trade_details[field] = ""

    # Subject: two variants seen in real samples
    if trade_details["Currency Pair"]:
        date_str = random.choice(["26_05_26", "26/05/26"])
        subject = (f"FX Trade Settlement[{trade_id}] – "
                   f"{trade_details['Currency Pair']} – {date_str} - {uti}")
    else:
        subject = f"FX Trade Settlement {trade_id} – 26/05/26 – {uti}"

    plain = _trade_plain(trade_details, ssi, sig)
    html = _trade_html(trade_details, ssi, sig)

    msg = _new_message(SENDER, subject, dt, f"<{trade_id}-{uti[:8]}@synthetic.local>")
    msg.set_content(plain)
    msg.add_alternative(html, subtype="html")
    return msg, trade_id


def _trade_plain(td: dict, ssi: dict, sig: dict) -> str:
    lines = [
        "Dear Team,",
        "",
        f"Please find below the settlement details for the FX trade executed on {TRADE_DATE}:",
        "",
        "Trade Details:",
        "",
    ]
    for k, v in td.items():
        lines.append(f"  * {k}: {v}".rstrip())
    lines += ["", "Settlement Instructions:", ""]
    for k, v in ssi.items():
        lines.append(f"  * {k}: {v}".rstrip())
    lines += [
        "",
        "Kindly confirm receipt of these instructions and advise if there are any "
        "discrepancies at the earliest to ensure timely settlement.",
        "",
        "",
        "Regards,",
        "",
        sig["name"],
        "Associate",
        sig["company"],
        sig["phone"],
        sig["domain"],
    ]
    return "\n".join(lines) + "\n"


def _trade_html(td: dict, ssi: dict, sig: dict) -> str:
    def li(items):
        return "\n".join(
            f'    <li><b>{k}:</b>&nbsp;{v}</li>' for k, v in items.items()
        )
    return f"""<html>
<head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"></head>
<body dir="ltr" style="font-family: Aptos, sans-serif; font-size: 12pt; color: rgb(36,36,36);">
<p>Dear Team,</p>
<p>Please find below the settlement details for the FX trade executed on {TRADE_DATE}:</p>
<p><b>Trade Details:</b></p>
<ul>
{li(td)}
</ul>
<p><b>Settlement Instructions:</b></p>
<ul>
{li(ssi)}
</ul>
<p>Kindly confirm receipt of these instructions and advise if there are any discrepancies at the earliest to ensure timely settlement.</p>
<p><b>Regards,</b></p>
<p>{sig['name']}</p>
<p>Associate</p>
<p>{sig['company']}</p>
<p>{sig['phone']}</p>
<p>{sig['domain']}</p>
</body>
</html>
"""


# --------------------------------------------------------------------------
# AMBIGUOUS emails (settlement-adjacent, no clear FX trade context)
# --------------------------------------------------------------------------

AMBIGUOUS_EMAILS = [
    {
        "from": "Operations Desk <ops.desk@protivitiglobal.in>",
        "subject": "Settlement query – account reconciliation",
        "body": (
            "Hi team,\n\n"
            "Could you please confirm the status of the pending settlement we "
            "discussed yesterday? Need to close out the reconciliation before EOD.\n\n"
            "Thanks,\nOps"
        ),
    },
    {
        "from": "Rahul Verma <rahul.verma@protivitiglobal.in>",
        "subject": "Re: Confirmation needed",
        "body": (
            "Hello,\n\n"
            "Just following up – can you confirm the details we went over on the "
            "call? Want to make sure everything matches before we proceed.\n\n"
            "Regards,\nRahul"
        ),
    },
    {
        "from": "Finance Shared Services <fss@protivitiglobal.in>",
        "subject": "Pending transaction follow-up",
        "body": (
            "Team,\n\n"
            "There is an outstanding item on the books that needs review. Please "
            "advise on next steps when you get a chance.\n\n"
            "Best,\nFSS"
        ),
    },
]


# --------------------------------------------------------------------------
# IRRELEVANT noise emails
# --------------------------------------------------------------------------

IRRELEVANT_EMAILS = [
    # personal
    {
        "from": "Priya Sharma <priya.sharma@protivitiglobal.in>",
        "subject": "Happy Birthday Akshit! \U0001f382",
        "body": "Wishing you a fantastic birthday Akshit! Hope you have a great day. "
                "Cake in the pantry at 4pm \U0001f389\n\nCheers,\nPriya",
    },
    {
        "from": "HR Team <hr@protivitiglobal.in>",
        "subject": "5 Years at Protiviti – Congratulations Manav!",
        "body": "Dear Manav,\n\nCongratulations on completing 5 wonderful years with us! "
                "Thank you for your dedication and contributions.\n\nWarm regards,\nHR Team",
    },
    {
        "from": "Dheeraj Khatri <dheeraj.khatri@protivitiglobal.in>",
        "subject": "Great work on the Q1 presentation!",
        "body": "Hi all,\n\nJust wanted to say well done on the Q1 client presentation. "
                "Excellent effort from everyone involved.\n\nBest,\nDheeraj",
    },
    # corporate
    {
        "from": "IT Support <itsupport@protivitiglobal.in>",
        "subject": "[IT Support] Your request #TKT-44821 has been resolved",
        "body": "Hello,\n\nYour IT support ticket #TKT-44821 regarding VPN access has been "
                "resolved and closed. Please reopen if the issue persists.\n\nIT Support",
    },
    {
        "from": "HR Team <hr@protivitiglobal.in>",
        "subject": "Updated Remote Work Policy – Effective June 2026",
        "body": "Dear All,\n\nPlease find attached the updated remote work policy effective "
                "1 June 2026. Kindly review and acknowledge.\n\nRegards,\nHR Team",
    },
    {
        "from": "Internal Comms <comms@protivitiglobal.in>",
        "subject": "Protiviti Monthly Update – May 2026",
        "body": "Hello everyone,\n\nHere is your monthly roundup of company news, events, "
                "and highlights for May 2026. Read on for more!\n\nInternal Comms",
    },
    {
        "from": "IT Security <security@protivitiglobal.in>",
        "subject": "Action Required: Reset your VPN password by 30-May",
        "body": "Dear User,\n\nAs part of our routine security policy, please reset your VPN "
                "password before 30 May 2026 to avoid account lockout.\n\nIT Security",
    },
    # OOO / meeting / social
    {
        "from": "Satyadarshi Mohanty (IND) <satyadarshi.mohanty@protivitiglobal.in>",
        "subject": "Out of Office: Satyadarshi Mohanty (returns 2-Jun-2026)",
        "body": "I am currently out of office and will return on 2 June 2026. For urgent "
                "matters please contact the operations desk.\n\nThanks,\nSatya",
    },
    {
        "from": "Aastha Makkar (IND) <aastha.makkar@protivitiglobal.in>",
        "subject": "Team Sync – Phase 1 Review – Friday 3pm",
        "body": "Hi team,\n\nLet's sync on Friday at 3pm to review Phase 1 progress. "
                "Calendar invite to follow.\n\nThanks,\nAastha",
    },
    {
        "from": "Manav Khatri (IND) <manav.khatri@protivitiglobal.in>",
        "subject": "Lunch this Friday at 1pm – Sector 18",
        "body": "Hey all,\n\nPlanning a team lunch this Friday at 1pm in Sector 18. "
                "Let me know if you're in!\n\nManav",
    },
]


def build_simple_email(spec: dict, dt: datetime, idx: int) -> EmailMessage:
    msg = _new_message(
        spec["from"], spec["subject"], dt,
        f"<noise-{idx}@synthetic.local>",
        to=RECIPIENTS, cc=None,
    )
    msg.set_content(spec["body"] + "\n")
    return msg


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic test emails for the Email Agent.")
    parser.add_argument("--output", default=str(Path(__file__).resolve().parents[1] / "data" / "raw_emails" / "inbox"),
                        help="Output folder for .eml files")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--complete", type=int, default=8, help="Number of complete RELEVANT emails")
    parser.add_argument("--partial", type=int, default=4, help="Number of partial RELEVANT emails")
    parser.add_argument("--duplicates", type=int, default=2, help="Number of duplicate trade-ID emails")
    parser.add_argument("--clean", action="store_true", help="Delete existing .eml files in output first")
    args = parser.parse_args()

    random.seed(args.seed)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    if args.clean:
        removed = 0
        for f in out.glob("*.eml"):
            f.unlink()
            removed += 1
        print(f"[clean] removed {removed} existing .eml files")

    step = timedelta(minutes=3)
    counts = {"relevant_complete": 0, "relevant_partial": 0,
              "ambiguous": 0, "irrelevant": 0, "duplicate": 0}
    trade_num = 47
    generated_ids: list[str] = []
    messages: list[EmailMessage] = []

    # RELEVANT - complete
    for _ in range(args.complete):
        msg, tid = build_trade_email(trade_num, BASE_DT, complete=True)
        messages.append(msg)
        generated_ids.append(tid)
        counts["relevant_complete"] += 1
        trade_num += 1

    # RELEVANT - partial
    for _ in range(args.partial):
        msg, tid = build_trade_email(trade_num, BASE_DT, complete=False)
        messages.append(msg)
        generated_ids.append(tid)
        counts["relevant_partial"] += 1
        trade_num += 1

    # AMBIGUOUS
    for i, spec in enumerate(AMBIGUOUS_EMAILS):
        messages.append(build_simple_email(spec, BASE_DT, f"amb-{i}"))
        counts["ambiguous"] += 1

    # IRRELEVANT
    for i, spec in enumerate(IRRELEVANT_EMAILS):
        messages.append(build_simple_email(spec, BASE_DT, f"noise-{i}"))
        counts["irrelevant"] += 1

    # DUPLICATES (reuse already-generated trade IDs, fresh Message-ID)
    for tid in random.sample(generated_ids, min(args.duplicates, len(generated_ids))):
        num = int(tid.split("-")[-1])
        msg, _ = build_trade_email(num, BASE_DT, complete=True, force_trade_id=tid)
        messages.append(msg)
        counts["duplicate"] += 1

    # Shuffle so the inbox looks like a real, unsorted mailbox: categories are
    # interleaved rather than clustered. The category is decided by the agent at
    # runtime — it is never leaked by the filename or by the ordering on disk.
    random.shuffle(messages)

    # Assign sequential received-times in the shuffled order, then write with
    # plain numeric names (1.eml, 2.eml, ...).
    dt = BASE_DT
    for i, msg in enumerate(messages, start=1):
        if msg["Date"]:
            msg.replace_header("Date", format_datetime(dt))
        else:
            msg["Date"] = format_datetime(dt)
        (out / f"{i}.eml").write_bytes(msg.as_bytes())
        dt += step

    total = sum(counts.values())
    print("\n[Synthetic Email Generation Complete]")
    print(f"  Output folder:        {out}")
    print(f"  RELEVANT (complete):  {counts['relevant_complete']}")
    print(f"  RELEVANT (partial):   {counts['relevant_partial']}")
    print(f"  AMBIGUOUS:            {counts['ambiguous']}")
    print(f"  IRRELEVANT (noise):   {counts['irrelevant']}")
    print(f"  DUPLICATE:            {counts['duplicate']}")
    print(f"  TOTAL:                {total}")


if __name__ == "__main__":
    main()
