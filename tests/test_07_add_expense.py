"""
tests/test_07_add_expense.py

Pytest tests for the Add Expense feature (Spec 07) — GET|POST /expenses/add.

Spec summary
------------
Route:        GET|POST /expenses/add  (login required)
On GET:       Render add.html with amount, category (dropdown), date, description
              fields. Date defaults to today (YYYY-MM-DD). PKR symbol ₨ visible.
On POST:      Validate; on success insert expense row and redirect to /expenses.
              On error re-render form with inline error and preserved field values.

Validation rules
----------------
  amount      : required; must be a parseable float; must be > 0
  category    : required; must be one of the 7 canonical categories
  date        : required; must be a valid ISO-8601 date (YYYY-MM-DD)
  description : optional — empty string or omitted key must succeed

DB helper: create_expense(user_id, amount, category, expense_date, description)
Redirect target: /expenses (url_for('expense_list'))
"""

import pytest
from datetime import date

from app import app as flask_app
from database.db import init_db, get_db


# ------------------------------------------------------------------ #
# Constants                                                           #
# ------------------------------------------------------------------ #

VALID_CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
]

ADD_URL = "/expenses/add"

# Baseline valid payload — used as a starting point in most tests.
VALID_PAYLOAD = {
    "amount":      "250.00",
    "category":    "Food",
    "date":        "2026-06-01",
    "description": "Test lunch",
}

TEST_EMAIL    = "testuser@example.com"
TEST_PASSWORD = "testpass1"


# ------------------------------------------------------------------ #
# Fixtures                                                            #
# ------------------------------------------------------------------ #

@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING":          True,
        "DATABASE":         ":memory:",
        "SECRET_KEY":       "test-secret",
        "WTF_CSRF_ENABLED": False,
    })
    with flask_app.app_context():
        init_db()
        yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """A test client that is already registered and logged in."""
    client.post("/register", data={
        "name":             "Test User",
        "email":            TEST_EMAIL,
        "password":         TEST_PASSWORD,
        "confirm_password": TEST_PASSWORD,
    })
    client.post("/login", data={
        "email":    TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    return client


# ------------------------------------------------------------------ #
# DB query helpers — used only in DB side-effect assertions           #
# ------------------------------------------------------------------ #

def _count_expenses_for_user(email: str) -> int:
    """Return the number of expense rows belonging to the given user email."""
    db = get_db()
    row = db.execute(
        "SELECT COUNT(*) FROM expenses e "
        "JOIN users u ON u.id = e.user_id "
        "WHERE u.email = ?",
        (email,),
    ).fetchone()
    db.close()
    return row[0]


def _get_expenses_for_user(email: str):
    """Return all expense rows for the given user email, newest first by id."""
    db = get_db()
    rows = db.execute(
        "SELECT e.* FROM expenses e "
        "JOIN users u ON u.id = e.user_id "
        "WHERE u.email = ? "
        "ORDER BY e.id DESC",
        (email,),
    ).fetchall()
    db.close()
    return rows


# ================================================================== #
# 1. Auth guard                                                       #
# ================================================================== #

class TestAuthGuard:
    """Unauthenticated requests to /expenses/add must redirect to /login."""

    def test_get_unauthenticated_returns_302(self, client):
        response = client.get(ADD_URL)
        assert response.status_code == 302, (
            "Unauthenticated GET /expenses/add must return 302"
        )

    def test_get_unauthenticated_redirects_to_login(self, client):
        response = client.get(ADD_URL)
        assert "/login" in response.headers["Location"], (
            "Unauthenticated GET /expenses/add must redirect to /login"
        )

    def test_get_unauthenticated_follow_redirect_lands_on_login_page(self, client):
        response = client.get(ADD_URL, follow_redirects=True)
        assert response.status_code == 200, (
            "Following the unauthenticated redirect must reach a 200 page"
        )
        assert b"Login" in response.data or b"login" in response.data, (
            "Followed redirect must land on the login page"
        )

    def test_post_unauthenticated_returns_302(self, client):
        response = client.post(ADD_URL, data=VALID_PAYLOAD)
        assert response.status_code == 302, (
            "Unauthenticated POST /expenses/add must return 302"
        )

    def test_post_unauthenticated_redirects_to_login(self, client):
        response = client.post(ADD_URL, data=VALID_PAYLOAD)
        assert "/login" in response.headers["Location"], (
            "Unauthenticated POST /expenses/add must redirect to /login"
        )


# ================================================================== #
# 2. GET — form rendering                                             #
# ================================================================== #

class TestGetFormRendering:
    """GET /expenses/add (authenticated) must render the correct form."""

    def test_get_authenticated_returns_200(self, auth_client):
        response = auth_client.get(ADD_URL)
        assert response.status_code == 200, (
            "Authenticated GET /expenses/add must return 200"
        )

    def test_get_contains_amount_field(self, auth_client):
        response = auth_client.get(ADD_URL)
        assert b'name="amount"' in response.data, (
            "Form must contain a field with name='amount'"
        )

    def test_get_contains_category_field(self, auth_client):
        response = auth_client.get(ADD_URL)
        assert b'name="category"' in response.data, (
            "Form must contain a select with name='category'"
        )

    def test_get_contains_date_field(self, auth_client):
        response = auth_client.get(ADD_URL)
        assert b'name="date"' in response.data, (
            "Form must contain an input with name='date'"
        )

    def test_get_contains_description_field(self, auth_client):
        response = auth_client.get(ADD_URL)
        assert b'name="description"' in response.data, (
            "Form must contain a field with name='description'"
        )

    def test_get_date_defaults_to_today(self, auth_client):
        today = date.today().strftime("%Y-%m-%d")
        response = auth_client.get(ADD_URL)
        assert today.encode() in response.data, (
            f"Date field must be pre-filled with today's date ({today})"
        )

    def test_get_all_valid_categories_present_in_select(self, auth_client):
        response = auth_client.get(ADD_URL)
        for category in VALID_CATEGORIES:
            assert category.encode() in response.data, (
                f"Category option '{category}' must appear in the dropdown"
            )

    def test_get_pkr_symbol_present(self, auth_client):
        response = auth_client.get(ADD_URL)
        assert "₨".encode("utf-8") in response.data, (
            "PKR symbol ₨ must appear next to the amount field"
        )

    def test_get_no_error_on_fresh_load(self, auth_client):
        response = auth_client.get(ADD_URL)
        # A fresh GET must not show any error state
        assert b"auth-error" not in response.data, (
            "Fresh GET /expenses/add must not render any error element"
        )


# ================================================================== #
# 3. POST — happy path with description                               #
# ================================================================== #

class TestPostHappyPath:
    """Valid form submission must insert a row and redirect to /expenses."""

    def test_valid_post_returns_302(self, auth_client):
        response = auth_client.post(ADD_URL, data=VALID_PAYLOAD)
        assert response.status_code == 302, (
            "Valid POST must return a 302 redirect"
        )

    def test_valid_post_redirects_to_expenses(self, auth_client):
        response = auth_client.post(ADD_URL, data=VALID_PAYLOAD)
        assert "/expenses" in response.headers["Location"], (
            "Valid POST must redirect to /expenses"
        )

    def test_valid_post_follow_redirect_reaches_expense_list(self, auth_client):
        response = auth_client.post(ADD_URL, data=VALID_PAYLOAD, follow_redirects=True)
        assert response.status_code == 200, (
            "Following the redirect after a valid POST must return 200"
        )

    def test_valid_post_expense_appears_on_list_page(self, auth_client):
        auth_client.post(ADD_URL, data=VALID_PAYLOAD)
        response = auth_client.get("/expenses")
        assert b"Food" in response.data, (
            "Submitted category must appear on /expenses after a valid POST"
        )
        assert b"Test lunch" in response.data, (
            "Submitted description must appear on /expenses after a valid POST"
        )

    def test_valid_post_date_appears_on_list_page(self, auth_client):
        auth_client.post(ADD_URL, data=VALID_PAYLOAD)
        response = auth_client.get("/expenses")
        assert b"2026-06-01" in response.data, (
            "Submitted date must appear on /expenses after a valid POST"
        )

    def test_valid_post_inserts_exactly_one_db_row(self, app, auth_client):
        with app.app_context():
            before = _count_expenses_for_user(TEST_EMAIL)
        auth_client.post(ADD_URL, data=VALID_PAYLOAD)
        with app.app_context():
            after = _count_expenses_for_user(TEST_EMAIL)
        assert after - before == 1, (
            "Exactly one expense row must be inserted on a valid POST"
        )

    def test_valid_post_db_row_amount_is_correct(self, app, auth_client):
        auth_client.post(ADD_URL, data=VALID_PAYLOAD)
        with app.app_context():
            rows = _get_expenses_for_user(TEST_EMAIL)
        assert len(rows) == 1, "Expected exactly one expense row in the DB"
        assert rows[0]["amount"] == pytest.approx(250.00), (
            "Stored amount must equal the submitted value"
        )

    def test_valid_post_db_row_category_is_correct(self, app, auth_client):
        auth_client.post(ADD_URL, data=VALID_PAYLOAD)
        with app.app_context():
            rows = _get_expenses_for_user(TEST_EMAIL)
        assert rows[0]["category"] == "Food", (
            "Stored category must match the submitted value"
        )

    def test_valid_post_db_row_date_is_correct(self, app, auth_client):
        auth_client.post(ADD_URL, data=VALID_PAYLOAD)
        with app.app_context():
            rows = _get_expenses_for_user(TEST_EMAIL)
        assert rows[0]["date"] == "2026-06-01", (
            "Stored date must match the submitted value"
        )

    def test_valid_post_db_row_description_is_correct(self, app, auth_client):
        auth_client.post(ADD_URL, data=VALID_PAYLOAD)
        with app.app_context():
            rows = _get_expenses_for_user(TEST_EMAIL)
        assert rows[0]["description"] == "Test lunch", (
            "Stored description must match the submitted value"
        )

    def test_new_expense_appears_at_top_of_list(self, app, auth_client):
        """
        When two expenses are submitted, the most recently added one
        (highest id, or newest by date) must appear first on /expenses.
        The list is ordered by date DESC; use distinct dates to guarantee order.
        """
        auth_client.post(ADD_URL, data={**VALID_PAYLOAD, "date": "2026-05-01", "description": "OlderExpense"})
        auth_client.post(ADD_URL, data={**VALID_PAYLOAD, "date": "2026-06-10", "description": "NewerExpense"})
        response = auth_client.get("/expenses")
        data = response.data.decode("utf-8")
        idx_newer = data.find("NewerExpense")
        idx_older = data.find("OlderExpense")
        assert idx_newer != -1, "NewerExpense must appear on /expenses"
        assert idx_older != -1, "OlderExpense must appear on /expenses"
        assert idx_newer < idx_older, (
            "The expense with the later date must appear before the older one on /expenses"
        )


# ================================================================== #
# 4. POST — no description (optional field)                           #
# ================================================================== #

class TestPostNoDescription:
    """Description is optional — empty or omitted must still succeed."""

    def test_empty_description_returns_302(self, auth_client):
        payload = {**VALID_PAYLOAD, "description": ""}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 302, (
            "POST with an empty description must succeed (302 redirect)"
        )

    def test_empty_description_redirects_to_expenses(self, auth_client):
        payload = {**VALID_PAYLOAD, "description": ""}
        response = auth_client.post(ADD_URL, data=payload)
        assert "/expenses" in response.headers["Location"], (
            "POST with an empty description must redirect to /expenses"
        )

    def test_empty_description_inserts_row_in_db(self, app, auth_client):
        payload = {**VALID_PAYLOAD, "description": ""}
        auth_client.post(ADD_URL, data=payload)
        with app.app_context():
            assert _count_expenses_for_user(TEST_EMAIL) == 1, (
                "One expense row must be inserted when description is an empty string"
            )

    def test_empty_description_db_value_is_none_or_empty(self, app, auth_client):
        payload = {**VALID_PAYLOAD, "description": ""}
        auth_client.post(ADD_URL, data=payload)
        with app.app_context():
            rows = _get_expenses_for_user(TEST_EMAIL)
        assert rows[0]["description"] is None or rows[0]["description"] == "", (
            "DB description must be None or '' when an empty string was submitted"
        )

    def test_description_key_omitted_entirely_succeeds(self, auth_client):
        payload = {
            "amount":   VALID_PAYLOAD["amount"],
            "category": VALID_PAYLOAD["category"],
            "date":     VALID_PAYLOAD["date"],
            # description key is intentionally absent
        }
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 302, (
            "POST without a description key at all must succeed (302 redirect)"
        )

    def test_description_key_omitted_inserts_row_in_db(self, app, auth_client):
        payload = {
            "amount":   VALID_PAYLOAD["amount"],
            "category": VALID_PAYLOAD["category"],
            "date":     VALID_PAYLOAD["date"],
        }
        auth_client.post(ADD_URL, data=payload)
        with app.app_context():
            assert _count_expenses_for_user(TEST_EMAIL) == 1, (
                "One expense row must be inserted when the description key is absent"
            )


# ================================================================== #
# 5. POST — amount validation                                         #
# ================================================================== #

class TestPostAmountValidation:
    """Amount must be present, numeric, and strictly greater than zero."""

    # -- Empty amount --

    def test_empty_amount_returns_200(self, auth_client):
        payload = {**VALID_PAYLOAD, "amount": ""}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 200, (
            "POST with an empty amount must re-render the form (200)"
        )

    def test_empty_amount_shows_error(self, auth_client):
        payload = {**VALID_PAYLOAD, "amount": ""}
        response = auth_client.post(ADD_URL, data=payload)
        assert b"auth-error" in response.data or b"required" in response.data.lower(), (
            "POST with an empty amount must display an inline error"
        )

    def test_empty_amount_does_not_insert_row(self, app, auth_client):
        payload = {**VALID_PAYLOAD, "amount": ""}
        auth_client.post(ADD_URL, data=payload)
        with app.app_context():
            assert _count_expenses_for_user(TEST_EMAIL) == 0, (
                "No DB row must be created when amount is empty"
            )

    # -- Non-numeric amount --

    @pytest.mark.parametrize("bad_amount", [
        "abc",
        "12.34.56",
        "one",
        "--5",
        " ",
        "!@#",
        "1,000",  # comma-formatted numbers are not accepted as raw input
    ])
    def test_non_numeric_amount_returns_200(self, auth_client, bad_amount):
        payload = {**VALID_PAYLOAD, "amount": bad_amount}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 200, (
            f"Non-numeric amount '{bad_amount}' must re-render the form (200)"
        )

    @pytest.mark.parametrize("bad_amount", [
        "abc",
        "twelve",
        "12.34.56",
        " ",
    ])
    def test_non_numeric_amount_shows_error(self, auth_client, bad_amount):
        payload = {**VALID_PAYLOAD, "amount": bad_amount}
        response = auth_client.post(ADD_URL, data=payload)
        assert b"auth-error" in response.data, (
            f"Non-numeric amount '{bad_amount}' must show the error element"
        )

    @pytest.mark.parametrize("bad_amount", [
        "abc",
        "one",
        "12.34.56",
    ])
    def test_non_numeric_amount_does_not_insert_row(self, app, auth_client, bad_amount):
        payload = {**VALID_PAYLOAD, "amount": bad_amount}
        auth_client.post(ADD_URL, data=payload)
        with app.app_context():
            assert _count_expenses_for_user(TEST_EMAIL) == 0, (
                f"No DB row must be created for non-numeric amount '{bad_amount}'"
            )

    # -- Amount <= 0 --

    @pytest.mark.parametrize("zero_or_negative", [
        "0",
        "0.00",
        "-1",
        "-0.01",
        "-100",
        "-999.99",
    ])
    def test_amount_not_positive_returns_200(self, auth_client, zero_or_negative):
        payload = {**VALID_PAYLOAD, "amount": zero_or_negative}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 200, (
            f"Amount '{zero_or_negative}' (not > 0) must re-render the form (200)"
        )

    @pytest.mark.parametrize("zero_or_negative", [
        "0",
        "0.00",
        "-1",
        "-100",
    ])
    def test_amount_not_positive_shows_error(self, auth_client, zero_or_negative):
        payload = {**VALID_PAYLOAD, "amount": zero_or_negative}
        response = auth_client.post(ADD_URL, data=payload)
        assert b"auth-error" in response.data, (
            f"Amount '{zero_or_negative}' must show the error element"
        )

    @pytest.mark.parametrize("zero_or_negative", [
        "0",
        "0.00",
        "-1",
        "-100",
    ])
    def test_amount_not_positive_does_not_insert_row(self, app, auth_client, zero_or_negative):
        payload = {**VALID_PAYLOAD, "amount": zero_or_negative}
        auth_client.post(ADD_URL, data=payload)
        with app.app_context():
            assert _count_expenses_for_user(TEST_EMAIL) == 0, (
                f"No DB row must be created when amount is '{zero_or_negative}'"
            )

    # -- Valid amounts (positive) --

    def test_integer_amount_is_accepted(self, auth_client):
        payload = {**VALID_PAYLOAD, "amount": "500"}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 302, (
            "Integer amount '500' must be accepted (302 redirect)"
        )

    def test_decimal_amount_is_accepted(self, auth_client):
        payload = {**VALID_PAYLOAD, "amount": "1250.75"}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 302, (
            "Decimal amount '1250.75' must be accepted (302 redirect)"
        )

    def test_small_positive_amount_is_accepted(self, auth_client):
        payload = {**VALID_PAYLOAD, "amount": "0.01"}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 302, (
            "Amount '0.01' (smallest valid positive) must be accepted (302 redirect)"
        )


# ================================================================== #
# 6. POST — category validation                                       #
# ================================================================== #

class TestPostCategoryValidation:
    """Category must be present and must match one of the 7 canonical values exactly."""

    def test_empty_category_returns_200(self, auth_client):
        payload = {**VALID_PAYLOAD, "category": ""}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 200, (
            "POST with an empty category must re-render the form (200)"
        )

    def test_empty_category_shows_error(self, auth_client):
        payload = {**VALID_PAYLOAD, "category": ""}
        response = auth_client.post(ADD_URL, data=payload)
        assert b"auth-error" in response.data, (
            "POST with an empty category must show the error element"
        )

    def test_empty_category_does_not_insert_row(self, app, auth_client):
        payload = {**VALID_PAYLOAD, "category": ""}
        auth_client.post(ADD_URL, data=payload)
        with app.app_context():
            assert _count_expenses_for_user(TEST_EMAIL) == 0, (
                "No DB row must be created when category is empty"
            )

    @pytest.mark.parametrize("bad_category", [
        "Groceries",                        # plausible but not in the list
        "food",                             # wrong capitalisation
        "FOOD",                             # all-caps
        "InvalidCategory",
        "Random",
        "1 OR 1=1",                         # SQL-injection-style string
        "'; DROP TABLE expenses; --",       # classic injection attempt
    ])
    def test_invalid_category_returns_200(self, auth_client, bad_category):
        payload = {**VALID_PAYLOAD, "category": bad_category}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 200, (
            f"Invalid category '{bad_category}' must re-render the form (200)"
        )

    @pytest.mark.parametrize("bad_category", [
        "Groceries",
        "food",
        "FOOD",
        "InvalidCategory",
    ])
    def test_invalid_category_shows_error(self, auth_client, bad_category):
        payload = {**VALID_PAYLOAD, "category": bad_category}
        response = auth_client.post(ADD_URL, data=payload)
        assert b"auth-error" in response.data, (
            f"Invalid category '{bad_category}' must show the error element"
        )

    @pytest.mark.parametrize("bad_category", [
        "Groceries",
        "food",
        "InvalidCategory",
    ])
    def test_invalid_category_does_not_insert_row(self, app, auth_client, bad_category):
        payload = {**VALID_PAYLOAD, "category": bad_category}
        auth_client.post(ADD_URL, data=payload)
        with app.app_context():
            assert _count_expenses_for_user(TEST_EMAIL) == 0, (
                f"No DB row must be created for invalid category '{bad_category}'"
            )

    @pytest.mark.parametrize("valid_category", VALID_CATEGORIES)
    def test_each_valid_category_is_accepted(self, auth_client, valid_category):
        """Every one of the 7 canonical categories must be accepted individually."""
        payload = {**VALID_PAYLOAD, "category": valid_category}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 302, (
            f"Valid category '{valid_category}' must be accepted (302 redirect)"
        )


# ================================================================== #
# 7. POST — date validation                                           #
# ================================================================== #

class TestPostDateValidation:
    """Date must be present and in valid ISO-8601 format (YYYY-MM-DD)."""

    def test_empty_date_returns_200(self, auth_client):
        payload = {**VALID_PAYLOAD, "date": ""}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 200, (
            "POST with an empty date must re-render the form (200)"
        )

    def test_empty_date_shows_error(self, auth_client):
        payload = {**VALID_PAYLOAD, "date": ""}
        response = auth_client.post(ADD_URL, data=payload)
        assert b"auth-error" in response.data, (
            "POST with an empty date must show the error element"
        )

    def test_empty_date_does_not_insert_row(self, app, auth_client):
        payload = {**VALID_PAYLOAD, "date": ""}
        auth_client.post(ADD_URL, data=payload)
        with app.app_context():
            assert _count_expenses_for_user(TEST_EMAIL) == 0, (
                "No DB row must be created when date is empty"
            )

    @pytest.mark.parametrize("bad_date", [
        "01-06-2026",       # DD-MM-YYYY (wrong order)
        "06/01/2026",       # slash separator (US format)
        "2026/06/01",       # ISO digits with slash separators
        "not-a-date",       # alphabetic
        "2026-13-01",       # month 13 is out of range
        "2026-00-15",       # month 0 is out of range
        "20260601",         # no separators at all
        "tomorrow",         # English word
        "2026-06-32",       # day 32 is invalid
    ])
    def test_invalid_date_returns_200(self, auth_client, bad_date):
        payload = {**VALID_PAYLOAD, "date": bad_date}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 200, (
            f"Invalid date '{bad_date}' must re-render the form (200)"
        )

    @pytest.mark.parametrize("bad_date", [
        "01-06-2026",
        "not-a-date",
        "2026-13-01",
        "2026-00-15",
    ])
    def test_invalid_date_shows_error(self, auth_client, bad_date):
        payload = {**VALID_PAYLOAD, "date": bad_date}
        response = auth_client.post(ADD_URL, data=payload)
        assert b"auth-error" in response.data, (
            f"Invalid date '{bad_date}' must show the error element"
        )

    @pytest.mark.parametrize("bad_date", [
        "01-06-2026",
        "not-a-date",
        "2026-13-01",
    ])
    def test_invalid_date_does_not_insert_row(self, app, auth_client, bad_date):
        payload = {**VALID_PAYLOAD, "date": bad_date}
        auth_client.post(ADD_URL, data=payload)
        with app.app_context():
            assert _count_expenses_for_user(TEST_EMAIL) == 0, (
                f"No DB row must be created for invalid date '{bad_date}'"
            )

    def test_valid_past_date_is_accepted(self, auth_client):
        payload = {**VALID_PAYLOAD, "date": "2020-01-15"}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 302, (
            "A valid past ISO date must be accepted (302 redirect)"
        )

    def test_valid_future_date_is_accepted(self, auth_client):
        """The route must not reject future dates."""
        payload = {**VALID_PAYLOAD, "date": "2030-12-31"}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 302, (
            "A valid future ISO date must be accepted (302 redirect)"
        )

    def test_valid_today_date_is_accepted(self, auth_client):
        today = date.today().strftime("%Y-%m-%d")
        payload = {**VALID_PAYLOAD, "date": today}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 302, (
            "Today's date as an ISO string must be accepted (302 redirect)"
        )


# ================================================================== #
# 8. POST — field preservation on validation error                    #
# ================================================================== #

class TestFieldPreservationOnError:
    """
    When a POST fails validation, the form must echo the user's entered
    values back into the re-rendered fields so they are not lost.
    """

    def test_invalid_amount_preserves_category(self, auth_client):
        payload = {
            "amount":      "bad",
            "category":    "Transport",
            "date":        "2026-06-01",
            "description": "Bus ticket",
        }
        response = auth_client.post(ADD_URL, data=payload)
        assert b"Transport" in response.data, (
            "Category must be preserved in the re-rendered form when amount is invalid"
        )

    def test_invalid_amount_preserves_date(self, auth_client):
        payload = {
            "amount":      "bad",
            "category":    "Food",
            "date":        "2026-05-20",
            "description": "Lunch",
        }
        response = auth_client.post(ADD_URL, data=payload)
        assert b"2026-05-20" in response.data, (
            "Date must be preserved in the re-rendered form when amount is invalid"
        )

    def test_invalid_amount_preserves_description(self, auth_client):
        payload = {
            "amount":      "bad",
            "category":    "Food",
            "date":        "2026-06-01",
            "description": "UniqueDescriptionToPreserve",
        }
        response = auth_client.post(ADD_URL, data=payload)
        assert b"UniqueDescriptionToPreserve" in response.data, (
            "Description must be preserved in the re-rendered form when amount is invalid"
        )

    def test_invalid_category_preserves_amount(self, auth_client):
        payload = {
            "amount":      "750",
            "category":    "NotACategory",
            "date":        "2026-06-01",
            "description": "",
        }
        response = auth_client.post(ADD_URL, data=payload)
        assert b"750" in response.data, (
            "Amount must be preserved in the re-rendered form when category is invalid"
        )

    def test_error_response_still_renders_all_category_options(self, auth_client):
        """On a validation error all 7 category options must still be present."""
        payload = {**VALID_PAYLOAD, "amount": "bad"}
        response = auth_client.post(ADD_URL, data=payload)
        for category in VALID_CATEGORIES:
            assert category.encode() in response.data, (
                f"Category option '{category}' must still appear in the form after a validation error"
            )


# ================================================================== #
# 9. POST — PKR symbol on form page                                   #
# ================================================================== #

class TestPkrSymbol:
    """₨ must appear on both the blank GET form and the error re-render."""

    def test_pkr_symbol_on_get_form(self, auth_client):
        response = auth_client.get(ADD_URL)
        assert "₨".encode("utf-8") in response.data, (
            "₨ symbol must be present on the GET /expenses/add form"
        )

    def test_pkr_symbol_preserved_on_error_rerender(self, auth_client):
        payload = {**VALID_PAYLOAD, "amount": "bad"}
        response = auth_client.post(ADD_URL, data=payload)
        assert "₨".encode("utf-8") in response.data, (
            "₨ symbol must remain present on the form after a validation error"
        )


# ================================================================== #
# 10. Multiple submissions — independence                             #
# ================================================================== #

class TestMultipleSubmissions:
    """Back-to-back submissions must be fully independent."""

    def test_two_valid_posts_insert_two_rows(self, app, auth_client):
        auth_client.post(ADD_URL, data={**VALID_PAYLOAD, "description": "First"})
        auth_client.post(ADD_URL, data={**VALID_PAYLOAD, "amount": "999", "description": "Second"})
        with app.app_context():
            assert _count_expenses_for_user(TEST_EMAIL) == 2, (
                "Two valid POSTs must produce two separate expense rows in the DB"
            )

    def test_failed_post_does_not_block_subsequent_valid_post(self, app, auth_client):
        auth_client.post(ADD_URL, data={**VALID_PAYLOAD, "amount": "bad"})   # fails
        auth_client.post(ADD_URL, data={**VALID_PAYLOAD, "amount": "100"})   # succeeds
        with app.app_context():
            assert _count_expenses_for_user(TEST_EMAIL) == 1, (
                "A failed POST must not prevent a subsequent valid POST from inserting a row"
            )

    def test_failed_post_followed_by_invalid_category_still_zero_rows(self, app, auth_client):
        auth_client.post(ADD_URL, data={**VALID_PAYLOAD, "amount": "bad"})
        auth_client.post(ADD_URL, data={**VALID_PAYLOAD, "category": "Groceries"})
        with app.app_context():
            assert _count_expenses_for_user(TEST_EMAIL) == 0, (
                "Two failed POSTs must leave the DB with zero expense rows"
            )
