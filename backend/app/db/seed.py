from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.add_on_service import AddOnService
from app.models.author import Author
from app.models.author_identity import AuthorIdentity
from app.models.book import Book
from app.models.escalation import Escalation
from app.models.query_log import QueryLog


FIRST_NAMES = [
    "Sara", "John", "Aisha", "Maya", "Rohan", "Neha", "Arjun", "Priya", "Kabir", "Elena",
    "Victor", "Ananya", "Farah", "Ishaan", "Nina", "Dev", "Liam", "Aarav", "Sofia", "Zara",
    "Meera", "Omar", "Ritika", "Noah", "Tara", "Rhea", "Ayaan", "Leah", "Karan", "Ira",
    "Aditi", "Rehan", "Jia", "Dhruv", "Mira", "Pooja", "Adrian", "Kiara", "Ethan", "Nora",
    "Sam", "Anvi", "Imran", "Dia", "Ravi", "Pallavi", "Ivy", "Mohan", "Alec", "Sana",
    "Yash", "Amina", "Rishi", "Tanya", "Vivian",
]

LAST_NAMES = [
    "Johnson", "Carter", "Khan", "Richardson", "Sharma", "Verma", "Malhotra", "Patel", "Roy", "Das",
    "Kapoor", "Mehta", "Sethi", "Fernandez", "Dawson", "Singh", "Nair", "Banerjee", "Ali", "Mendes",
]

GENRES = ["Romance", "Thriller", "Drama", "Fantasy", "Sci-Fi", "Business", "Poetry", "Self Help"]
COUNTRIES = ["India", "United States", "United Kingdom", "Canada", "UAE", "Singapore", "Australia"]
SUPPORT_TIERS = ["standard", "premium", "priority"]

BOOK_STATUS = ["pending", "processing", "completed", "delayed", "escalated"]
ROYALTY_STATUS = ["pending", "processing", "paid", "on_hold", "under_review"]
ADDON_STATUS = ["pending", "processing", "completed", "delayed", "escalated"]

ADDON_SERVICES = [
    ("Bestseller Package", "marketing", Decimal("149.00")),
    ("PR Campaign", "marketing", Decimal("99.00")),
    ("Literary Award Submission", "editorial", Decimal("59.00")),
    ("Social Media Promotion", "marketing", Decimal("79.00")),
    ("Fast Track Publishing", "production", Decimal("199.00")),
]

QUERY_INTENTS = ["BOOK_STATUS", "ROYALTY", "AUTHOR_COPY", "ADDON_STATUS", "DASHBOARD_ACCESS", "GENERAL_POLICY"]
CHANNELS = ["email", "whatsapp", "instagram", "web-chat"]

DASHBOARD_ISSUE_MESSAGES = [
    "I cannot log into my dashboard after password reset.",
    "My dashboard still shows submission pending after upload.",
    "Activation email was not received for dashboard access.",
    "Dashboard submission failed while uploading manuscript files.",
]

FAILED_SUBMISSION_MESSAGES = [
    "My manuscript submission failed during final validation.",
    "Cover upload keeps failing in dashboard setup.",
    "ISBN generation failed after submission.",
]


def _email_for(name: str, idx: int) -> str:
    local = name.lower().replace(" ", ".")
    return f"{local}.{idx}@bookleafauthors.com"


def _phone_for(idx: int) -> str:
    return f"+91-90000{idx:05d}"


def _wa_for(idx: int) -> str:
    return f"+91-88000{idx:05d}"


def _instagram_for(name: str, idx: int) -> str:
    handle = name.lower().replace(" ", "")
    return f"@{handle}{idx}"


def _isbn_for(idx: int) -> str:
    return f"9781000{idx:06d}"


def _book_title(idx: int, j: int) -> str:
    stems = ["Whispers", "Silent", "Broken", "Midnight", "Golden", "Hidden", "Falling", "Rising", "Lost", "Echoes"]
    suffix = ["Rain", "Path", "Moon", "Canvas", "Scripts", "Letters", "Harbor", "Blueprint", "Promise", "Dawn"]
    return f"{stems[(idx + j) % len(stems)]} of {suffix[(idx * 2 + j) % len(suffix)]}"


def _get_or_create_author(db: Session, *, full_name: str, email: str, genre: str, country: str) -> Author:
    author = db.query(Author).filter(Author.email == email).first()
    if author:
        return author
    author = Author(id=str(uuid4()), full_name=full_name, email=email, genre=genre, country=country, active=True)
    db.add(author)
    db.flush()
    return author


def _get_or_create_book(
    db: Session,
    *,
    author_id: str,
    title: str,
    isbn: str,
    publication_date: date,
    status: str,
    royalty_status: str,
    support_tier: str,
) -> Book:
    book = db.query(Book).filter(Book.isbn == isbn).first()
    if book:
        return book
    book = Book(
        id=str(uuid4()),
        author_id=author_id,
        title=title,
        isbn=isbn,
        publication_date=publication_date,
        status=status,
        royalty_status=royalty_status,
        support_tier=support_tier,
    )
    db.add(book)
    db.flush()
    return book


def _ensure_identity(
    db: Session,
    *,
    author_id: str,
    name_variant: str,
    email: str | None,
    instagram: str | None,
    phone: str | None = None,
    whatsapp: str | None = None,
) -> None:
    existing = (
        db.query(AuthorIdentity)
        .filter(
            AuthorIdentity.author_id == author_id,
            AuthorIdentity.name_variant == name_variant,
        )
        .first()
    )
    if existing:
        return
    db.add(
        AuthorIdentity(
            id=str(uuid4()),
            author_id=author_id,
            name_variant=name_variant,
            email=email,
            instagram=instagram,
            phone=phone,
            whatsapp=whatsapp,
            verified=True,
        )
    )


def _ensure_addon(db: Session, *, book_id: str, service_name: str, service_type: str, monthly_fee: Decimal, status: str) -> None:
    existing = db.query(AddOnService).filter(AddOnService.book_id == book_id, AddOnService.service_name == service_name).first()
    if existing:
        return
    db.add(
        AddOnService(
            id=str(uuid4()),
            book_id=book_id,
            service_name=service_name,
            service_type=service_type,
            monthly_fee=monthly_fee,
            status=status,
        )
    )


def _seed_authors_books_identities(db: Session) -> tuple[list[Author], list[Book]]:
    authors: list[Author] = []
    books: list[Book] = []

    author_count = 55
    for i in range(author_count):
        first = FIRST_NAMES[i % len(FIRST_NAMES)]
        last = LAST_NAMES[i % len(LAST_NAMES)]
        full_name = f"{first} {last}"
        email = _email_for(full_name, i)

        author = _get_or_create_author(
            db,
            full_name=full_name,
            email=email,
            genre=GENRES[i % len(GENRES)],
            country=COUNTRIES[i % len(COUNTRIES)],
        )
        authors.append(author)

        phone = _phone_for(i)
        whatsapp = _wa_for(i)
        ig = _instagram_for(full_name, i)
        dashboard_name = f"{first}.{last}".lower()
        pen_name = f"{first} {LAST_NAMES[(i + 5) % len(LAST_NAMES)]}"

        _ensure_identity(db, author_id=author.id, name_variant=full_name, email=email, instagram=ig, phone=phone, whatsapp=whatsapp)
        _ensure_identity(db, author_id=author.id, name_variant=f"{first} {last[0]}.", email=email, instagram=ig, phone=phone, whatsapp=whatsapp)
        _ensure_identity(db, author_id=author.id, name_variant=dashboard_name, email=email, instagram=ig, phone=phone, whatsapp=whatsapp)
        _ensure_identity(db, author_id=author.id, name_variant=pen_name, email=email, instagram=f"@{dashboard_name}_writes", phone=phone, whatsapp=whatsapp)

        books_for_author = 1 + (i % 2)
        for j in range(books_for_author):
            bidx = i * 2 + j
            pub_date = date(2025 + (bidx % 2), (bidx % 12) + 1, ((bidx * 3) % 27) + 1)
            status = BOOK_STATUS[bidx % len(BOOK_STATUS)]
            if bidx % 17 == 0:
                status = "failed_submission"

            book = _get_or_create_book(
                db,
                author_id=author.id,
                title=_book_title(i, j),
                isbn=_isbn_for(bidx + 100),
                publication_date=pub_date,
                status=status,
                royalty_status=ROYALTY_STATUS[(i + j) % len(ROYALTY_STATUS)],
                support_tier=SUPPORT_TIERS[(i + j) % len(SUPPORT_TIERS)],
            )
            books.append(book)

            for k, (service_name, service_type, fee) in enumerate(ADDON_SERVICES):
                if (bidx + k) % 3 == 0:
                    _ensure_addon(
                        db,
                        book_id=book.id,
                        service_name=service_name,
                        service_type=service_type,
                        monthly_fee=fee,
                        status=ADDON_STATUS[(bidx + k) % len(ADDON_STATUS)],
                    )

    # Add controlled conflicting identity signals for ambiguity queue realism.
    if len(authors) >= 6:
        shared_handle = "@bookleaffeatured"
        shared_whatsapp = "+91-8800099999"
        conflict_pairs = [(authors[1], "A. Carter"), (authors[4], "A. Sharma"), (authors[5], "A. Verma")]
        for author, alias in conflict_pairs:
            _ensure_identity(
                db,
                author_id=author.id,
                name_variant=alias,
                email=author.email,
                instagram=shared_handle,
                phone=None,
                whatsapp=shared_whatsapp,
            )

    return authors, books


def _make_query_meta(*, confidence: float, escalated: bool, escalation_reason: str | None, retrieval_source: str, workflow_status: str) -> dict:
    return {
        "confidence": round(confidence, 3),
        "escalated": escalated,
        "escalation_reason": escalation_reason,
        "retrieval_source": retrieval_source,
        "workflow_status": workflow_status,
        "retrieval_confidence": round(min(0.99, confidence + 0.08), 3),
    }


def _seed_query_logs_and_escalations(db: Session, authors: list[Author], books: list[Book]) -> None:
    existing_logs = db.query(QueryLog).count()
    if existing_logs >= 120:
        return

    now = datetime.now(timezone.utc)
    escalation_patterns = [
        "low_confidence",
        "ambiguous_identity",
        "delayed_publishing",
        "failed_dashboard_access",
    ]

    for i in range(160):
        author = authors[i % len(authors)]
        author_books = [b for b in books if b.author_id == author.id]
        book = author_books[i % len(author_books)] if author_books else None
        intent = QUERY_INTENTS[i % len(QUERY_INTENTS)]
        channel = CHANNELS[i % len(CHANNELS)]

        if intent == "DASHBOARD_ACCESS":
            message = DASHBOARD_ISSUE_MESSAGES[i % len(DASHBOARD_ISSUE_MESSAGES)]
        elif intent == "BOOK_STATUS" and i % 9 == 0:
            message = FAILED_SUBMISSION_MESSAGES[i % len(FAILED_SUBMISSION_MESSAGES)]
        elif intent == "ROYALTY":
            message = f"Can you confirm royalty payout status for {book.title if book else 'my title'}?"
        elif intent == "AUTHOR_COPY":
            message = f"Please share author copy dispatch update for {book.title if book else 'my book'}."
        elif intent == "ADDON_STATUS":
            message = "What is the status of my add-on services and campaign progress?"
        else:
            message = "I need help understanding publishing policy for my current submission."

        escalated = i % 7 == 0 or (book is not None and book.status in {"delayed", "escalated", "failed_submission"})
        escalation_reason = None
        confidence = 0.92 - ((i % 10) * 0.04)
        confidence = max(0.31, min(0.97, confidence))
        if escalated:
            confidence = min(confidence, 0.72)
            reason_key = escalation_patterns[i % len(escalation_patterns)]
            reason_map = {
                "low_confidence": "Confidence below automation threshold",
                "ambiguous_identity": "Multiple author identities matched request",
                "delayed_publishing": "Book workflow is delayed and needs manual intervention",
                "failed_dashboard_access": "Dashboard access attempts failed after retries",
            }
            escalation_reason = reason_map[reason_key]

        retrieval_source = "PostgreSQL + Knowledge Base" if i % 4 != 0 else "PostgreSQL"
        workflow_status = "escalated" if escalated else "resolved"
        response_time_ms = 650 + (i % 13) * 95

        log = QueryLog(
            id=str(uuid4()),
            author_id=author.id,
            book_id=book.id if book else None,
            channel=channel,
            customer_name=author.full_name,
            customer_email=author.email,
            message=message,
            intent=intent,
            status=workflow_status,
            response_time_ms=response_time_ms,
            meta=_make_query_meta(
                confidence=confidence,
                escalated=escalated,
                escalation_reason=escalation_reason,
                retrieval_source=retrieval_source,
                workflow_status=workflow_status,
            ),
            created_at=now - timedelta(hours=i * 3),
            updated_at=now - timedelta(hours=i * 3),
        )
        db.add(log)

        if escalated:
            db.flush()
            if not db.query(Escalation).filter(Escalation.query_id == log.id).first():
                db.add(
                    Escalation(
                        id=str(uuid4()),
                        query_id=log.id,
                        escalation_level=1 if i % 3 else 2,
                        reason=escalation_reason or "Manual review required",
                        assigned_to="support.ops@bookleaf.ai" if i % 2 == 0 else "senior.support@bookleaf.ai",
                        priority="high" if i % 5 == 0 else "medium",
                        status="open" if i % 6 else "in_progress",
                    )
                )


def seed_mock_data(db: Session) -> None:
    authors, books = _seed_authors_books_identities(db)
    _seed_query_logs_and_escalations(db, authors, books)
    db.commit()
