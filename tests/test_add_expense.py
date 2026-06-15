"""
tests/test_add_expense.py

Tests for the Add Expense feature — GET|POST /expenses/add (Step 07).

Route interface:
  GET  /expenses/add  — renders the add-expense form with today's date pre-filled
                        and the full categories list. Requires login.
  POST /expenses/add  — validates and inserts; redirects to /expenses on success,
                        or re-renders the form with the error and preserved values.

Validation rules:
  amount      : required, valid float, > 0
  category    : required, must be one of VALID_CATEGORIES
  date        : required, valid ISO date (YYYY-MM-DD)
  description : optional — may be empty or omitted entirely

DB helper: create_expense(user_id, amount, category, expense_date, description)
"""

import pytest
from datetime import date

from app import app as flask_app
from database.db import init_db, get_db


# ------------------------------------------------------------------ #
# Constants                                                           #
# ------------------------------------------------------------------ #

VALID_CATEGORIES = [
    "Food", "Transport", "Bills", "Health",
    "Entertainment", "Shopping", "Other",
]

ADD_URL = "/expenses/add"

# A minimal valid form payload — used as a baseline in many tests.
VALID_PAYLOAD = {
    "amount":      "250.00",
    "category":    "Food",
    "date":        "2026-06-01",
    "description": "Test lunch",
}


# ------------------------------------------------------------------ #
# Fixtures                                                            #
# ------------------------------------------------------------------ #

@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING":         True,
        "DATABASE":        ":memory:",
        "SECRET_KEY":      "test-secret",
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
        "email":            "testuser@example.com",
        "password":         "testpass1",
        "confirm_password": "testpass1",
    })
    client.post("/login", data={
        "email":    "testuser@example.com",
        "password": "testpass1",
    })
    return client


# ------------------------------------------------------------------ #
# Helper                                                              #
# ------------------------------------------------------------------ #

def _count_expenses(user_email: str) -> int:
    """Return the number of expense rows for the given user email."""
    db = get_db()
    row = db.execute(
        "SELECT COUNT(*) FROM expenses e "
        "JOIN users u ON u.id = e.user_id "
        "WHERE u.email = ?",
        (user_email,),
    ).fetchone()
    db.close()
    return row[0]


def _get_expenses_for_user(user_email: str):
    """Return all expense rows (as sqlite3.Row) for the given user email."""
    db = get_db()
    rows = db.execute(
        "SELECT e.* FROM expenses e "
        "JOIN users u ON u.id = e.user_id "
        "WHERE u.email = ? "
        "ORDER BY e.id DESC",
        (user_email,),
    ).fetchall()
    db.close()
    return rows


# ================================================================== #
# Auth guard                                                          #
# ================================================================== #

class TestAuthGuard:
    def test_get_unauthenticated_returns_302(self, client):
        response = client.get(ADD_URL)
        assert response.status_code == 302, (
            "Unauthenticated GET /expenses/add must redirect (302)"
        )

    def test_get_unauthenticated_location_contains_login(self, client):
        response = client.get(ADD_URL)
        assert "/login" in response.headers["Location"], (
            "Unauthenticated GET /expenses/add must redirect to /login"
        )

    def test_get_unauthenticated_follows_redirect_to_login_page(self, client):
        response = client.get(ADD_URL, follow_redirects=True)
        assert response.status_code == 200, (
            "Following the redirect must land on a 200 page"
        )
        assert b"Login" in response.data or b"login" in response.data, (
            "Following the redirect must land on the login page"
        )

    def test_post_unauthenticated_returns_302(self, client):
        response = client.post(ADD_URL, data=VALID_PAYLOAD)
        assert response.status_code == 302, (
            "Unauthenticated POST /expenses/add must redirect (302)"
        )

    def test_post_unauthenticated_location_contains_login(self, client):
        response = client.post(ADD_URL, data=VALID_PAYLOAD)
        assert "/login" in response.headers["Location"], (
            "Unauthenticated POST /expenses/add must redirect to /login"
        )


# ================================================================== #
# GET — form rendering                                                #
# ================================================================== #

class TestGetRenderForm:
    def test_get_authenticated_returns_200(self, auth_client):
        response = auth_client.get(ADD_URL)
        assert response.status_code == 200, (
            "Authenticated GET /expenses/add must return 200"
        )

    def test_get_contains_amount_input(self, auth_client):
        response = auth_client.get(ADD_URL)
        assert b'name="amount"' in response.data, (
            "Form must contain an input with name='amount'"
        )

    def test_get_contains_category_select(self, auth_client):
        response = auth_client.get(ADD_URL)
        assert b'name="category"' in response.data, (
            "Form must contain a select with name='category'"
        )

    def test_get_contains_date_input(self, auth_client):
        response = auth_client.get(ADD_URL)
        assert b'name="date"' in response.data, (
            "Form must contain an input with name='date'"
        )

    def test_get_contains_description_textarea(self, auth_client):
        response = auth_client.get(ADD_URL)
        assert b'name="description"' in response.data, (
            "Form must contain a textarea with name='description'"
        )

    def test_get_contains_submit_button(self, auth_client):
        response = auth_client.get(ADD_URL)
        assert b"Record Expense" in response.data, (
            "Form must have a 'Record Expense' submit button"
        )

    def test_get_date_prefilled_with_today(self, auth_client):
        today = date.today().strftime("%Y-%m-%d")
        response = auth_client.get(ADD_URL)
        assert today.encode() in response.data, (
            f"Date input must be pre-filled with today's date ({today})"
        )

    def test_get_all_valid_categories_in_select(self, auth_client):
        response = auth_client.get(ADD_URL)
        for cat in VALID_CATEGORIES:
            assert cat.encode() in response.data, (
                f"Category option '{cat}' must appear in the select element"
            )

    def test_get_no_error_on_fresh_load(self, auth_client):
        response = auth_client.get(ADD_URL)
        assert b"auth-error" not in response.data, (
            "A fresh GET /expenses/add must not display any error message"
        )


# ================================================================== #
# POST — happy path                                                   #
# ================================================================== #

class TestPostHappyPath:
    def test_valid_post_returns_302(self, auth_client):
        response = auth_client.post(ADD_URL, data=VALID_PAYLOAD)
        assert response.status_code == 302, (
            "Valid POST /expenses/add must return 302 redirect"
        )

    def test_valid_post_redirects_to_expenses(self, auth_client):
        response = auth_client.post(ADD_URL, data=VALID_PAYLOAD)
        assert "/expenses" in response.headers["Location"], (
            "Valid POST must redirect to /expenses"
        )

    def test_valid_post_expense_list_returns_200(self, auth_client):
        auth_client.post(ADD_URL, data=VALID_PAYLOAD)
        response = auth_client.get("/expenses")
        assert response.status_code == 200, (
            "GET /expenses after a successful add must return 200"
        )

    def test_valid_post_category_appears_on_expense_list(self, auth_client):
        auth_client.post(ADD_URL, data=VALID_PAYLOAD)
        response = auth_client.get("/expenses")
        assert b"Food" in response.data, (
            "The submitted category must appear on the /expenses list page"
        )

    def test_valid_post_description_appears_on_expense_list(self, auth_client):
        auth_client.post(ADD_URL, data=VALID_PAYLOAD)
        response = auth_client.get("/expenses")
        assert b"Test lunch" in response.data, (
            "The submitted description must appear on the /expenses list page"
        )

    def test_valid_post_date_appears_on_expense_list(self, auth_client):
        auth_client.post(ADD_URL, data=VALID_PAYLOAD)
        response = auth_client.get("/expenses")
        assert b"2026-06-01" in response.data, (
            "The submitted date must appear on the /expenses list page"
        )

    def test_valid_post_inserts_exactly_one_row_in_db(self, app, auth_client):
        with app.app_context():
            before = _count_expenses("testuser@example.com")
        auth_client.post(ADD_URL, data=VALID_PAYLOAD)
        with app.app_context():
            after = _count_expenses("testuser@example.com")
        assert after - before == 1, (
            "Exactly one expense row must be inserted on a valid POST"
        )

    def test_valid_post_db_amount_is_correct(self, app, auth_client):
        auth_client.post(ADD_URL, data=VALID_PAYLOAD)
        with app.app_context():
            rows = _get_expenses_for_user("testuser@example.com")
        assert len(rows) == 1, "Expected one expense in the DB"
        assert rows[0]["amount"] == pytest.approx(250.00), (
            "The stored amount must match the submitted value"
        )

    def test_valid_post_db_category_is_correct(self, app, auth_client):
        auth_client.post(ADD_URL, data=VALID_PAYLOAD)
        with app.app_context():
            rows = _get_expenses_for_user("testuser@example.com")
        assert rows[0]["category"] == "Food", (
            "The stored category must match the submitted value"
        )

    def test_valid_post_db_date_is_correct(self, app, auth_client):
        auth_client.post(ADD_URL, data=VALID_PAYLOAD)
        with app.app_context():
            rows = _get_expenses_for_user("testuser@example.com")
        assert rows[0]["date"] == "2026-06-01", (
            "The stored date must match the submitted value"
        )

    def test_valid_post_db_description_is_correct(self, app, auth_client):
        auth_client.post(ADD_URL, data=VALID_PAYLOAD)
        with app.app_context():
            rows = _get_expenses_for_user("testuser@example.com")
        assert rows[0]["description"] == "Test lunch", (
            "The stored description must match the submitted value"
        )

    def test_valid_post_follows_redirect_to_expenses_page(self, auth_client):
        response = auth_client.post(ADD_URL, data=VALID_PAYLOAD, follow_redirects=True)
        assert response.status_code == 200, (
            "Following the redirect after a valid POST must return 200"
        )
        assert b"My Expenses" in response.data, (
            "The expense list page heading must be present after a successful add"
        )


# ================================================================== #
# POST — no description (optional field)                              #
# ================================================================== #

class TestPostNoDescription:
    def test_no_description_returns_302(self, auth_client):
        payload = {**VALID_PAYLOAD, "description": ""}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 302, (
            "POST with empty description must still succeed (302)"
        )

    def test_no_description_redirects_to_expenses(self, auth_client):
        payload = {**VALID_PAYLOAD, "description": ""}
        response = auth_client.post(ADD_URL, data=payload)
        assert "/expenses" in response.headers["Location"], (
            "POST with empty description must redirect to /expenses"
        )

    def test_no_description_row_inserted_in_db(self, app, auth_client):
        payload = {**VALID_PAYLOAD, "description": ""}
        auth_client.post(ADD_URL, data=payload)
        with app.app_context():
            rows = _get_expenses_for_user("testuser@example.com")
        assert len(rows) == 1, (
            "One expense row must be inserted when description is omitted"
        )

    def test_no_description_db_description_is_none_or_empty(self, app, auth_client):
        payload = {**VALID_PAYLOAD, "description": ""}
        auth_client.post(ADD_URL, data=payload)
        with app.app_context():
            rows = _get_expenses_for_user("testuser@example.com")
        # create_expense stores empty string as None (description or None)
        assert rows[0]["description"] is None or rows[0]["description"] == "", (
            "Description stored in DB must be None or empty when not provided"
        )

    def test_description_key_omitted_entirely_still_succeeds(self, auth_client):
        """POST without the description key at all must succeed."""
        payload = {
            "amount":   VALID_PAYLOAD["amount"],
            "category": VALID_PAYLOAD["category"],
            "date":     VALID_PAYLOAD["date"],
        }
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 302, (
            "POST without a description key must succeed (302)"
        )


# ================================================================== #
# POST — amount validation                                            #
# ================================================================== #

class TestPostAmountValidation:
    def test_empty_amount_returns_200(self, auth_client):
        payload = {**VALID_PAYLOAD, "amount": ""}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 200, (
            "POST with empty amount must re-render the form (200)"
        )

    def test_empty_amount_shows_error(self, auth_client):
        payload = {**VALID_PAYLOAD, "amount": ""}
        response = auth_client.post(ADD_URL, data=payload)
        assert b"auth-error" in response.data or b"required" in response.data.lower(), (
            "POST with empty amount must display an error message"
        )

    def test_empty_amount_does_not_insert_db_row(self, app, auth_client):
        payload = {**VALID_PAYLOAD, "amount": ""}
        auth_client.post(ADD_URL, data=payload)
        with app.app_context():
            assert _count_expenses("testuser@example.com") == 0, (
                "No DB row must be created when amount is empty"
            )

    @pytest.mark.parametrize("bad_amount", [
        "abc",       # alphabetic
        "12.34.56",  # double decimal
        "one",       # word
        "--5",       # double negative
        "1e999",     # overflow-style notation handled by float() but let's see
        " ",         # whitespace only
    ])
    def test_non_numeric_amount_returns_200(self, auth_client, bad_amount):
        payload = {**VALID_PAYLOAD, "amount": bad_amount}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 200, (
            f"Non-numeric amount '{bad_amount}' must re-render the form (200)"
        )

    @pytest.mark.parametrize("bad_amount", [
        "abc",
        "one",
        "12.34.56",
        " ",
    ])
    def test_non_numeric_amount_shows_error(self, auth_client, bad_amount):
        payload = {**VALID_PAYLOAD, "amount": bad_amount}
        response = auth_client.post(ADD_URL, data=payload)
        assert b"auth-error" in response.data, (
            f"Non-numeric amount '{bad_amount}' must show an error element"
        )

    @pytest.mark.parametrize("zero_or_negative", [
        "0",
        "0.00",
        "-1",
        "-0.01",
        "-100",
    ])
    def test_amount_not_greater_than_zero_returns_200(self, auth_client, zero_or_negative):
        payload = {**VALID_PAYLOAD, "amount": zero_or_negative}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 200, (
            f"Amount '{zero_or_negative}' must re-render the form (200)"
        )

    @pytest.mark.parametrize("zero_or_negative", [
        "0",
        "0.00",
        "-1",
        "-100",
    ])
    def test_amount_not_greater_than_zero_shows_error(self, auth_client, zero_or_negative):
        payload = {**VALID_PAYLOAD, "amount": zero_or_negative}
        response = auth_client.post(ADD_URL, data=payload)
        assert b"auth-error" in response.data, (
            f"Amount '{zero_or_negative}' must show an error element"
        )

    @pytest.mark.parametrize("zero_or_negative", [
        "0",
        "0.00",
        "-1",
        "-100",
    ])
    def test_amount_not_greater_than_zero_does_not_insert(self, app, auth_client, zero_or_negative):
        payload = {**VALID_PAYLOAD, "amount": zero_or_negative}
        auth_client.post(ADD_URL, data=payload)
        with app.app_context():
            assert _count_expenses("testuser@example.com") == 0, (
                f"No DB row must be created when amount is '{zero_or_negative}'"
            )

    def test_valid_integer_amount_succeeds(self, auth_client):
        """An integer amount like '500' (no decimal) must be accepted."""
        payload = {**VALID_PAYLOAD, "amount": "500"}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 302, (
            "Integer amount '500' must be accepted and redirect"
        )

    def test_valid_decimal_amount_succeeds(self, auth_client):
        """A decimal amount like '1250.75' must be accepted."""
        payload = {**VALID_PAYLOAD, "amount": "1250.75"}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 302, (
            "Decimal amount '1250.75' must be accepted and redirect"
        )


# ================================================================== #
# POST — category validation                                          #
# ================================================================== #

class TestPostCategoryValidation:
    def test_empty_category_returns_200(self, auth_client):
        payload = {**VALID_PAYLOAD, "category": ""}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 200, (
            "POST with empty category must re-render the form (200)"
        )

    def test_empty_category_shows_error(self, auth_client):
        payload = {**VALID_PAYLOAD, "category": ""}
        response = auth_client.post(ADD_URL, data=payload)
        assert b"auth-error" in response.data, (
            "POST with empty category must show an error element"
        )

    def test_empty_category_does_not_insert(self, app, auth_client):
        payload = {**VALID_PAYLOAD, "category": ""}
        auth_client.post(ADD_URL, data=payload)
        with app.app_context():
            assert _count_expenses("testuser@example.com") == 0, (
                "No DB row must be created when category is empty"
            )

    @pytest.mark.parametrize("bad_category", [
        "Groceries",         # close but not in the list
        "food",              # wrong capitalisation
        "FOOD",              # all caps
        "InvalidCategory",
        "1 OR 1=1",          # SQL-injection-style string
        "'; DROP TABLE expenses; --",
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
        "InvalidCategory",
    ])
    def test_invalid_category_shows_error(self, auth_client, bad_category):
        payload = {**VALID_PAYLOAD, "category": bad_category}
        response = auth_client.post(ADD_URL, data=payload)
        assert b"auth-error" in response.data, (
            f"Invalid category '{bad_category}' must show an error element"
        )

    @pytest.mark.parametrize("bad_category", [
        "Groceries",
        "food",
        "InvalidCategory",
    ])
    def test_invalid_category_does_not_insert(self, app, auth_client, bad_category):
        payload = {**VALID_PAYLOAD, "category": bad_category}
        auth_client.post(ADD_URL, data=payload)
        with app.app_context():
            assert _count_expenses("testuser@example.com") == 0, (
                f"No DB row must be created for invalid category '{bad_category}'"
            )

    @pytest.mark.parametrize("valid_category", VALID_CATEGORIES)
    def test_all_valid_categories_are_accepted(self, auth_client, valid_category):
        """Each of the 7 canonical categories must be accepted individually."""
        payload = {**VALID_PAYLOAD, "category": valid_category}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 302, (
            f"Valid category '{valid_category}' must be accepted (302)"
        )


# ================================================================== #
# POST — date validation                                              #
# ================================================================== #

class TestPostDateValidation:
    def test_empty_date_returns_200(self, auth_client):
        payload = {**VALID_PAYLOAD, "date": ""}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 200, (
            "POST with empty date must re-render the form (200)"
        )

    def test_empty_date_shows_error(self, auth_client):
        payload = {**VALID_PAYLOAD, "date": ""}
        response = auth_client.post(ADD_URL, data=payload)
        assert b"auth-error" in response.data, (
            "POST with empty date must show an error element"
        )

    def test_empty_date_does_not_insert(self, app, auth_client):
        payload = {**VALID_PAYLOAD, "date": ""}
        auth_client.post(ADD_URL, data=payload)
        with app.app_context():
            assert _count_expenses("testuser@example.com") == 0, (
                "No DB row must be created when date is empty"
            )

    @pytest.mark.parametrize("bad_date", [
        "01-06-2026",       # DD-MM-YYYY — wrong order
        "06/01/2026",       # slash separator
        "2026/06/01",       # ISO digits but slash separator
        "not-a-date",       # alphabetic
        "2026-13-01",       # month 13 — out of range
        "2026-00-15",       # month 0  — out of range
        "20260601",         # no separators
        "tomorrow",         # word
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
            f"Invalid date '{bad_date}' must show an error element"
        )

    @pytest.mark.parametrize("bad_date", [
        "01-06-2026",
        "not-a-date",
        "2026-13-01",
    ])
    def test_invalid_date_does_not_insert(self, app, auth_client, bad_date):
        payload = {**VALID_PAYLOAD, "date": bad_date}
        auth_client.post(ADD_URL, data=payload)
        with app.app_context():
            assert _count_expenses("testuser@example.com") == 0, (
                f"No DB row must be created for invalid date '{bad_date}'"
            )

    def test_valid_past_date_accepted(self, auth_client):
        payload = {**VALID_PAYLOAD, "date": "2025-01-15"}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 302, (
            "A valid past ISO date must be accepted"
        )

    def test_valid_future_date_accepted(self, auth_client):
        """The route does not restrict future dates — they should be accepted."""
        payload = {**VALID_PAYLOAD, "date": "2030-12-31"}
        response = auth_client.post(ADD_URL, data=payload)
        assert response.status_code == 302, (
            "A valid future ISO date must be accepted"
        )


# ================================================================== #
# POST — field preservation on validation error                       #
# ================================================================== #

class TestPostFieldPreservation:
    def test_error_preserves_category_value(self, auth_client):
        """When amount is invalid, the submitted category must be echoed back."""
        payload = {
            "amount":      "bad",
            "category":    "Transport",
            "date":        "2026-06-01",
            "description": "Bus ticket",
        }
        response = auth_client.post(ADD_URL, data=payload)
        assert b"Transport" in response.data, (
            "The submitted category must be preserved in the form on error"
        )

    def test_error_preserves_date_value(self, auth_client):
        """When amount is invalid, the submitted date must be echoed back."""
        payload = {
            "amount":      "bad",
            "category":    "Food",
            "date":        "2026-05-20",
            "description": "Lunch",
        }
        response = auth_client.post(ADD_URL, data=payload)
        assert b"2026-05-20" in response.data, (
            "The submitted date must be preserved in the form on error"
        )

    def test_error_preserves_description_value(self, auth_client):
        """When amount is invalid, the submitted description must be echoed back."""
        payload = {
            "amount":      "bad",
            "category":    "Food",
            "date":        "2026-06-01",
            "description": "Preserved description text",
        }
        response = auth_client.post(ADD_URL, data=payload)
        assert b"Preserved description text" in response.data, (
            "The submitted description must be preserved in the form on error"
        )

    def test_error_preserves_amount_string(self, auth_client):
        """When category is invalid, the submitted amount string must be echoed back."""
        payload = {
            "amount":      "750",
            "category":    "NotACategory",
            "date":        "2026-06-01",
            "description": "",
        }
        response = auth_client.post(ADD_URL, data=payload)
        assert b"750" in response.data, (
            "The submitted amount must be preserved in the form on error"
        )

    def test_error_renders_all_category_options(self, auth_client):
        """On error the select element must still contain all valid options."""
        payload = {**VALID_PAYLOAD, "amount": "bad"}
        response = auth_client.post(ADD_URL, data=payload)
        for cat in VALID_CATEGORIES:
            assert cat.encode() in response.data, (
                f"Category option '{cat}' must still be rendered in the form on error"
            )


# ================================================================== #
# POST — multiple consecutive submissions (independence check)        #
# ================================================================== #

class TestMultipleSubmissions:
    def test_two_valid_posts_insert_two_rows(self, app, auth_client):
        payload_1 = {**VALID_PAYLOAD, "description": "First expense"}
        payload_2 = {**VALID_PAYLOAD, "amount": "999", "description": "Second expense"}
        auth_client.post(ADD_URL, data=payload_1)
        auth_client.post(ADD_URL, data=payload_2)
        with app.app_context():
            assert _count_expenses("testuser@example.com") == 2, (
                "Two valid POSTs must insert two separate expense rows"
            )

    def test_failed_post_does_not_prevent_subsequent_success(self, app, auth_client):
        bad_payload  = {**VALID_PAYLOAD, "amount": "bad"}
        good_payload = {**VALID_PAYLOAD, "amount": "100"}
        auth_client.post(ADD_URL, data=bad_payload)   # should fail
        auth_client.post(ADD_URL, data=good_payload)  # should succeed
        with app.app_context():
            assert _count_expenses("testuser@example.com") == 1, (
                "A failed POST must not block a subsequent valid POST"
            )
