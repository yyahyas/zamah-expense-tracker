"""
tests/test_06-date-filter-profile-page.py

Tests for the date-filter feature on GET /profile (Spec 06).

Covers:
- Auth guard
- Default current-month date range when no query params are provided
- Filter form is pre-populated with active from_date / to_date values
- Expenses within the requested range are returned; expenses outside are not
- Filtered total reflects only the returned expenses
- Empty-state message and ₨ 0.00 total when no expenses match the range
- Malformed date params fall back silently to current-month defaults
- Existing account-details and password forms remain present
- Amount formatting: ₨ X,XXX.00 (rupee symbol, comma thousands, two decimals)
- Expense-count wording (singular vs plural) in the summary line
- Data isolation: another user's expenses are never shown
"""

import pytest
import calendar
from datetime import date

from app import app as flask_app
from database.db import init_db, get_db


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def _current_month_bounds():
    """Return (first_day_str, last_day_str) for the current calendar month."""
    today = date.today()
    first = today.replace(day=1).strftime("%Y-%m-%d")
    last_day = calendar.monthrange(today.year, today.month)[1]
    last = today.replace(day=last_day).strftime("%Y-%m-%d")
    return first, last


def _insert_expense(user_id, amount, category, exp_date, description="Test expense"):
    """Insert a single expense row directly via get_db() and return its id."""
    db = get_db()
    cursor = db.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, exp_date, description),
    )
    db.commit()
    expense_id = cursor.lastrowid
    db.close()
    return expense_id


def _get_user_id_by_email(email):
    """Fetch a user's id by email."""
    db = get_db()
    row = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    db.close()
    return row["id"] if row else None


# ------------------------------------------------------------------ #
# Fixtures                                                            #
# ------------------------------------------------------------------ #

@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING": True,
        "DATABASE": ":memory:",
        "SECRET_KEY": "test-secret",
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
    """A test client that is already registered and logged in (no expenses)."""
    client.post("/register", data={
        "name": "Test User",
        "email": "testuser@example.com",
        "password": "testpass1",
        "confirm_password": "testpass1",
    })
    client.post("/login", data={
        "email": "testuser@example.com",
        "password": "testpass1",
    })
    return client


@pytest.fixture
def seeded_auth_client(app, client):
    """
    A logged-in client whose user has three expenses at known dates:
      - 500.00  on 2024-03-10  (Food)
      - 1500.00 on 2024-03-20  (Transport)
      - 3000.00 on 2024-04-05  (Bills)

    Total for March 2024: 2000.00
    Total for April 2024:  3000.00
    """
    with app.app_context():
        client.post("/register", data={
            "name": "Seeded User",
            "email": "seeded@example.com",
            "password": "seedpass1",
            "confirm_password": "seedpass1",
        })
        client.post("/login", data={
            "email": "seeded@example.com",
            "password": "seedpass1",
        })
        uid = _get_user_id_by_email("seeded@example.com")
        _insert_expense(uid, 500.00,  "Food",      "2024-03-10", "Lunch")
        _insert_expense(uid, 1500.00, "Transport", "2024-03-20", "Fuel")
        _insert_expense(uid, 3000.00, "Bills",     "2024-04-05", "Electricity")
    return client


# ------------------------------------------------------------------ #
# Auth guard                                                          #
# ------------------------------------------------------------------ #

class TestAuthGuard:
    def test_get_profile_unauthenticated_redirects_to_login(self, client):
        response = client.get("/profile")
        assert response.status_code == 302, "Expected redirect for unauthenticated request"
        assert "/login" in response.headers["Location"], "Should redirect to /login"

    def test_get_profile_unauthenticated_follows_redirect_to_login(self, client):
        response = client.get("/profile", follow_redirects=True)
        assert response.status_code == 200
        assert b"Login" in response.data or b"login" in response.data, (
            "Followed redirect should land on login page"
        )


# ------------------------------------------------------------------ #
# Default current-month date range                                    #
# ------------------------------------------------------------------ #

class TestDefaultDateRange:
    def test_profile_no_params_returns_200(self, auth_client):
        response = auth_client.get("/profile")
        assert response.status_code == 200, "GET /profile should return 200 for logged-in user"

    def test_profile_no_params_renders_expense_history_section(self, auth_client):
        response = auth_client.get("/profile")
        assert b"Expense History" in response.data, (
            "Page should contain the Expense History section heading"
        )

    def test_profile_no_params_prepopulates_from_date_with_first_of_month(self, auth_client):
        first, _ = _current_month_bounds()
        response = auth_client.get("/profile")
        assert first.encode() in response.data, (
            f"from_date input should default to first day of current month ({first})"
        )

    def test_profile_no_params_prepopulates_to_date_with_last_of_month(self, auth_client):
        _, last = _current_month_bounds()
        response = auth_client.get("/profile")
        assert last.encode() in response.data, (
            f"to_date input should default to last day of current month ({last})"
        )


# ------------------------------------------------------------------ #
# Filter form structure                                               #
# ------------------------------------------------------------------ #

class TestFilterFormStructure:
    def test_filter_form_has_from_date_input(self, auth_client):
        response = auth_client.get("/profile")
        assert b'name="from_date"' in response.data, (
            "Filter form must contain an input with name='from_date'"
        )

    def test_filter_form_has_to_date_input(self, auth_client):
        response = auth_client.get("/profile")
        assert b'name="to_date"' in response.data, (
            "Filter form must contain an input with name='to_date'"
        )

    def test_filter_form_has_submit_button(self, auth_client):
        response = auth_client.get("/profile")
        assert b"Filter" in response.data, (
            "Filter form must have a submit button labelled 'Filter'"
        )

    def test_filter_form_method_is_get(self, auth_client):
        response = auth_client.get("/profile")
        # The form tag should use method="get"
        assert b'method="get"' in response.data, (
            "Date filter form must submit via GET so the URL is bookmarkable"
        )

    def test_valid_params_are_prepopulated_in_inputs(self, auth_client):
        response = auth_client.get("/profile?from_date=2024-03-01&to_date=2024-03-31")
        assert b'value="2024-03-01"' in response.data, (
            "from_date input must carry the submitted value as its value= attribute"
        )
        assert b'value="2024-03-31"' in response.data, (
            "to_date input must carry the submitted value as its value= attribute"
        )


# ------------------------------------------------------------------ #
# Existing forms remain present                                       #
# ------------------------------------------------------------------ #

class TestExistingFormsPresent:
    def test_account_details_form_still_present(self, auth_client):
        response = auth_client.get("/profile")
        assert b"Save changes" in response.data, (
            "Account details form with 'Save changes' button must still be present"
        )
        assert b"Account details" in response.data, (
            "Account details section heading must still be present"
        )

    def test_password_change_form_still_present(self, auth_client):
        response = auth_client.get("/profile")
        assert b"Update password" in response.data, (
            "Password change form with 'Update password' button must still be present"
        )
        assert b"Change password" in response.data, (
            "Change password section heading must still be present"
        )

    def test_account_details_form_action_targets_profile_update(self, auth_client):
        response = auth_client.get("/profile")
        assert b'action="/profile"' in response.data, (
            "Account details form action must point to /profile (POST)"
        )

    def test_password_form_action_targets_profile_password(self, auth_client):
        response = auth_client.get("/profile")
        assert b'action="/profile/password"' in response.data, (
            "Password form action must point to /profile/password"
        )


# ------------------------------------------------------------------ #
# Filtered results — correct rows returned                           #
# ------------------------------------------------------------------ #

class TestFilteredResults:
    def test_expenses_in_range_appear_in_response(self, seeded_auth_client):
        response = seeded_auth_client.get(
            "/profile?from_date=2024-03-01&to_date=2024-03-31"
        )
        assert response.status_code == 200
        assert b"Lunch" in response.data, (
            "Expense 'Lunch' (2024-03-10) should appear in March filter results"
        )
        assert b"Fuel" in response.data, (
            "Expense 'Fuel' (2024-03-20) should appear in March filter results"
        )

    def test_expenses_outside_range_do_not_appear(self, seeded_auth_client):
        response = seeded_auth_client.get(
            "/profile?from_date=2024-03-01&to_date=2024-03-31"
        )
        assert b"Electricity" not in response.data, (
            "Expense 'Electricity' (2024-04-05) must not appear in March filter results"
        )

    def test_boundary_date_from_is_inclusive(self, seeded_auth_client):
        # 2024-03-10 is the exact from_date — it must be included
        response = seeded_auth_client.get(
            "/profile?from_date=2024-03-10&to_date=2024-03-31"
        )
        assert b"Lunch" in response.data, (
            "Expense on the exact from_date boundary must be included"
        )

    def test_boundary_date_to_is_inclusive(self, seeded_auth_client):
        # 2024-03-20 is the exact to_date — it must be included
        response = seeded_auth_client.get(
            "/profile?from_date=2024-03-01&to_date=2024-03-20"
        )
        assert b"Fuel" in response.data, (
            "Expense on the exact to_date boundary must be included"
        )

    def test_expense_just_before_from_date_excluded(self, seeded_auth_client):
        # from_date=2024-03-11 should exclude the 2024-03-10 Lunch expense
        response = seeded_auth_client.get(
            "/profile?from_date=2024-03-11&to_date=2024-03-31"
        )
        assert b"Lunch" not in response.data, (
            "Expense dated one day before from_date must not appear"
        )

    def test_expense_just_after_to_date_excluded(self, seeded_auth_client):
        # to_date=2024-03-19 should exclude the 2024-03-20 Fuel expense
        response = seeded_auth_client.get(
            "/profile?from_date=2024-03-01&to_date=2024-03-19"
        )
        assert b"Fuel" not in response.data, (
            "Expense dated one day after to_date must not appear"
        )

    def test_april_filter_shows_only_april_expense(self, seeded_auth_client):
        response = seeded_auth_client.get(
            "/profile?from_date=2024-04-01&to_date=2024-04-30"
        )
        assert b"Electricity" in response.data, (
            "April expense must appear in April filter range"
        )
        assert b"Lunch" not in response.data, (
            "March expense must not appear in April filter range"
        )
        assert b"Fuel" not in response.data, (
            "March expense must not appear in April filter range"
        )


# ------------------------------------------------------------------ #
# Filtered total                                                      #
# ------------------------------------------------------------------ #

class TestFilteredTotal:
    def test_filtered_total_for_march_is_correct(self, seeded_auth_client):
        # 500.00 + 1500.00 = 2,000.00
        response = seeded_auth_client.get(
            "/profile?from_date=2024-03-01&to_date=2024-03-31"
        )
        assert b"2,000.00" in response.data, (
            "Filtered total for March should be ₨ 2,000.00"
        )

    def test_filtered_total_for_april_is_correct(self, seeded_auth_client):
        # 3000.00
        response = seeded_auth_client.get(
            "/profile?from_date=2024-04-01&to_date=2024-04-30"
        )
        assert b"3,000.00" in response.data, (
            "Filtered total for April should be ₨ 3,000.00"
        )

    def test_filtered_total_reflects_only_filtered_rows(self, seeded_auth_client):
        # Filtering to a single expense: Lunch 500.00
        response = seeded_auth_client.get(
            "/profile?from_date=2024-03-10&to_date=2024-03-10"
        )
        assert b"500.00" in response.data, (
            "Total must reflect only the single matching expense (500.00)"
        )
        assert b"2,000.00" not in response.data, (
            "Full March total must not appear when filter is narrower"
        )


# ------------------------------------------------------------------ #
# Empty state                                                         #
# ------------------------------------------------------------------ #

class TestEmptyState:
    def test_empty_range_shows_empty_state_message(self, seeded_auth_client):
        # A range that contains no expenses
        response = seeded_auth_client.get(
            "/profile?from_date=2020-01-01&to_date=2020-01-31"
        )
        assert b"No expenses found for this period." in response.data, (
            "Empty-state message must appear when no expenses match the filter"
        )

    def test_empty_range_shows_zero_total(self, seeded_auth_client):
        response = seeded_auth_client.get(
            "/profile?from_date=2020-01-01&to_date=2020-01-31"
        )
        assert b"0.00" in response.data, (
            "Filtered total must be 0.00 when no expenses match"
        )

    def test_new_user_default_view_shows_empty_state(self, auth_client):
        # auth_client has no expenses at all
        response = auth_client.get("/profile")
        assert b"No expenses found for this period." in response.data, (
            "User with no expenses should see the empty-state message on default load"
        )

    def test_new_user_default_view_shows_zero_total(self, auth_client):
        response = auth_client.get("/profile")
        assert b"0.00" in response.data, (
            "User with no expenses should see a total of 0.00"
        )

    def test_empty_range_shows_zero_expense_count(self, seeded_auth_client):
        response = seeded_auth_client.get(
            "/profile?from_date=2020-01-01&to_date=2020-01-31"
        )
        assert b"0 expenses" in response.data or b"across 0" in response.data, (
            "Summary line must report 0 expenses for an empty filter result"
        )


# ------------------------------------------------------------------ #
# Malformed date params — silent fallback                             #
# ------------------------------------------------------------------ #

class TestMalformedDateParams:
    def test_malformed_from_date_returns_200_without_error(self, auth_client):
        response = auth_client.get("/profile?from_date=abc&to_date=2024-03-31")
        assert response.status_code == 200, (
            "Malformed from_date must not cause a 400/500 — should silently fall back"
        )
        assert b"error" not in response.data.lower() or b"auth-error" not in response.data, (
            "Malformed from_date must not display an error message to the user"
        )

    def test_malformed_from_date_falls_back_to_current_month_first_day(self, auth_client):
        first, _ = _current_month_bounds()
        response = auth_client.get("/profile?from_date=abc&to_date=2024-03-31")
        assert first.encode() in response.data, (
            "Malformed from_date must fall back to first day of current month"
        )

    def test_malformed_to_date_returns_200_without_error(self, auth_client):
        response = auth_client.get("/profile?from_date=2024-03-01&to_date=not-a-date")
        assert response.status_code == 200, (
            "Malformed to_date must not cause a 400/500 — should silently fall back"
        )

    def test_malformed_to_date_falls_back_to_current_month_last_day(self, auth_client):
        _, last = _current_month_bounds()
        response = auth_client.get("/profile?from_date=2024-03-01&to_date=not-a-date")
        assert last.encode() in response.data, (
            "Malformed to_date must fall back to last day of current month"
        )

    def test_both_params_malformed_falls_back_to_current_month(self, auth_client):
        first, last = _current_month_bounds()
        response = auth_client.get("/profile?from_date=bad&to_date=worse")
        assert response.status_code == 200, (
            "Both params malformed must still return a valid page"
        )
        assert first.encode() in response.data, (
            "from_date must fall back to first day of current month"
        )
        assert last.encode() in response.data, (
            "to_date must fall back to last day of current month"
        )

    def test_empty_string_params_fall_back_to_current_month(self, auth_client):
        first, last = _current_month_bounds()
        response = auth_client.get("/profile?from_date=&to_date=")
        assert response.status_code == 200
        assert first.encode() in response.data, (
            "Empty from_date param must fall back to first day of current month"
        )
        assert last.encode() in response.data, (
            "Empty to_date param must fall back to last day of current month"
        )

    @pytest.mark.parametrize("bad_date", [
        "2024-13-01",   # month 13 does not exist
        "2024-00-15",   # month 0 does not exist
        "not-a-date",
        "abc",
        "12345",
        "2024/03/01",   # wrong separator
        " ",
    ])
    def test_various_malformed_from_dates_do_not_crash(self, auth_client, bad_date):
        response = auth_client.get(f"/profile?from_date={bad_date}&to_date=2024-03-31")
        assert response.status_code == 200, (
            f"from_date='{bad_date}' must not crash the page"
        )


# ------------------------------------------------------------------ #
# Amount formatting                                                   #
# ------------------------------------------------------------------ #

class TestAmountFormatting:
    def test_rupee_symbol_present_in_summary_line(self, seeded_auth_client):
        response = seeded_auth_client.get(
            "/profile?from_date=2024-03-01&to_date=2024-03-31"
        )
        # The rupee symbol ₨ is U+20A8; check its UTF-8 encoding
        assert "₨".encode("utf-8") in response.data, (
            "₨ symbol must appear in the filtered total summary line"
        )

    def test_expense_amounts_formatted_with_two_decimal_places(self, seeded_auth_client):
        response = seeded_auth_client.get(
            "/profile?from_date=2024-03-01&to_date=2024-03-31"
        )
        # 500.00 and 1500.00 must appear with exactly two decimal places
        assert b"500.00" in response.data, (
            "Expense amount must be formatted with two decimal places"
        )
        assert b"1,500.00" in response.data, (
            "Expense amount must use comma as thousands separator and two decimal places"
        )

    def test_total_formatted_with_thousands_separator(self, seeded_auth_client):
        # March total is 2000.00 — should render as 2,000.00
        response = seeded_auth_client.get(
            "/profile?from_date=2024-03-01&to_date=2024-03-31"
        )
        assert b"2,000.00" in response.data, (
            "Filtered total must use a thousands comma separator"
        )

    def test_zero_total_formatted_as_zero_point_zero_zero(self, auth_client):
        response = auth_client.get("/profile?from_date=2020-01-01&to_date=2020-01-31")
        assert b"0.00" in response.data, (
            "Zero total must be rendered as 0.00, not 0 or 0.0"
        )


# ------------------------------------------------------------------ #
# Expense count wording                                               #
# ------------------------------------------------------------------ #

class TestExpenseCountWording:
    def test_summary_shows_plural_expenses_for_multiple(self, seeded_auth_client):
        # Two expenses in March
        response = seeded_auth_client.get(
            "/profile?from_date=2024-03-01&to_date=2024-03-31"
        )
        assert b"expenses" in response.data, (
            "Summary line must use plural 'expenses' when there are multiple results"
        )

    def test_summary_shows_singular_expense_for_one(self, seeded_auth_client):
        # Only the Lunch expense on 2024-03-10
        response = seeded_auth_client.get(
            "/profile?from_date=2024-03-10&to_date=2024-03-10"
        )
        # "1 expense" not "1 expenses"
        assert b"1 expense" in response.data, (
            "Summary line must use singular 'expense' when exactly one result is shown"
        )
        assert b"1 expenses" not in response.data, (
            "Summary line must not use plural 'expenses' for a single result"
        )


# ------------------------------------------------------------------ #
# Data isolation — other users' expenses never shown                  #
# ------------------------------------------------------------------ #

class TestDataIsolation:
    def test_other_users_expenses_not_shown(self, app, client):
        """
        Two separate users each with an expense in the same date range.
        User A's filter response must not contain User B's expense description.
        """
        with app.app_context():
            # Register and log in User A
            client.post("/register", data={
                "name": "User A",
                "email": "usera@example.com",
                "password": "passwordA1",
                "confirm_password": "passwordA1",
            })
            client.post("/login", data={
                "email": "usera@example.com",
                "password": "passwordA1",
            })
            uid_a = _get_user_id_by_email("usera@example.com")
            _insert_expense(uid_a, 999.00, "Food", "2024-06-15", "UserA-Only-Expense")

            # Register User B (do NOT log in as B yet)
            from database.db import create_user
            uid_b = create_user("User B", "userb@example.com", "passwordB1")
            _insert_expense(uid_b, 888.00, "Transport", "2024-06-15", "UserB-Only-Expense")

        # We are still logged in as User A — filter over the shared date
        response = client.get("/profile?from_date=2024-06-01&to_date=2024-06-30")
        assert b"UserA-Only-Expense" in response.data, (
            "Logged-in user's own expense must appear"
        )
        assert b"UserB-Only-Expense" not in response.data, (
            "Another user's expense must never appear in the filtered results"
        )
