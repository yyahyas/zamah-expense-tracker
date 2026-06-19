"""
tests/test_delete_expense.py

Tests for the Delete Expense feature — POST /expenses/<int:id>/delete (Step 09).

Route interface:
  POST /expenses/<int:id>/delete  — deletes the expense if it belongs to the
                                    logged-in user; redirects to /expenses on
                                    success.

Expected behavior:
  - GET  /expenses/<id>/delete          -> 405 Method Not Allowed
  - POST (unauthenticated)              -> 302 redirect to /login
  - POST with non-existent expense id   -> 404
  - POST for another user's expense     -> 403
  - POST for own expense                -> 302 redirect to /expenses;
                                           row removed from DB;
                                           no longer visible on /expenses page
  - Delete form/button present on:
      GET /expenses, GET /dashboard, GET /profile

DB helpers used: create_expense, get_expense_by_id (database/db.py)
Route name (url_for): delete_expense
"""

import pytest

from app import app as flask_app
from database.db import init_db, get_db, create_expense, get_expense_by_id

# ------------------------------------------------------------------ #
# Constants                                                           #
# ------------------------------------------------------------------ #

TEST_EMAIL = "owner@example.com"
TEST_PASSWORD = "ownerpass1"
TEST_NAME = "Owner User"

OTHER_EMAIL = "other@example.com"
OTHER_PASSWORD = "otherpass1"
OTHER_NAME = "Other User"

SAMPLE_EXPENSE = {
    "amount": 500.00,
    "category": "Food",
    "date": "2026-05-01",
    "description": "Test meal",
}


# ------------------------------------------------------------------ #
# Fixtures                                                            #
# ------------------------------------------------------------------ #


@pytest.fixture
def app():
    flask_app.config.update(
        {
            "TESTING": True,
            "DATABASE": ":memory:",
            "SECRET_KEY": "test-secret",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with flask_app.app_context():
        init_db()
        yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """A test client already registered and logged in as the primary user."""
    client.post(
        "/register",
        data={
            "name": TEST_NAME,
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "confirm_password": TEST_PASSWORD,
        },
    )
    client.post(
        "/login",
        data={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )
    return client


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #


def _get_user_id_by_email(email: str) -> int:
    """Return the user id for the given email, or None."""
    db = get_db()
    row = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    db.close()
    return row["id"] if row else None


def _insert_expense_for_email(email: str) -> int:
    """Register (if needed) and insert one sample expense; return the expense id."""
    db = get_db()
    row = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    db.close()
    if row is None:
        raise RuntimeError(f"User {email!r} not found — register first")
    user_id = row["id"]
    return create_expense(
        user_id,
        SAMPLE_EXPENSE["amount"],
        SAMPLE_EXPENSE["category"],
        SAMPLE_EXPENSE["date"],
        SAMPLE_EXPENSE["description"],
    )


def _expense_exists(expense_id: int) -> bool:
    """Return True if the expense row still exists in the DB."""
    return get_expense_by_id(expense_id) is not None


def _delete_url(expense_id: int) -> str:
    return f"/expenses/{expense_id}/delete"


# ================================================================== #
# Method guard — GET must be 405                                      #
# ================================================================== #


class TestGetMethodNotAllowed:
    def test_get_to_delete_route_returns_405(self, app, auth_client):
        """GET /expenses/<id>/delete is not a supported method."""
        with app.app_context():
            expense_id = _insert_expense_for_email(TEST_EMAIL)
        response = auth_client.get(_delete_url(expense_id))
        assert (
            response.status_code == 405
        ), "GET /expenses/<id>/delete must return 405 Method Not Allowed"

    def test_get_to_nonexistent_id_still_returns_405(self, auth_client):
        """
        Even for an ID that does not exist, GET must be refused with 405
        before any expense lookup occurs.
        """
        response = auth_client.get(_delete_url(999999))
        assert (
            response.status_code == 405
        ), "GET /expenses/<id>/delete for a missing id must still return 405"


# ================================================================== #
# Auth guard                                                          #
# ================================================================== #


class TestAuthGuard:
    def test_post_unauthenticated_returns_302(self, client):
        response = client.post(_delete_url(1))
        assert (
            response.status_code == 302
        ), "Unauthenticated POST /expenses/<id>/delete must redirect (302)"

    def test_post_unauthenticated_redirects_to_login(self, client):
        response = client.post(_delete_url(1))
        assert (
            "/login" in response.headers["Location"]
        ), "Unauthenticated POST must redirect to /login"

    def test_post_unauthenticated_follows_redirect_to_login_page(self, client):
        response = client.post(_delete_url(1), follow_redirects=True)
        assert (
            response.status_code == 200
        ), "Following the redirect must land on a 200 page"
        assert (
            b"Login" in response.data or b"login" in response.data
        ), "Following the unauthenticated redirect must render the login page"


# ================================================================== #
# 404 — non-existent expense                                          #
# ================================================================== #


class TestNotFound:
    def test_post_nonexistent_id_returns_404(self, auth_client):
        """Deleting an expense that does not exist must return 404."""
        response = auth_client.post(_delete_url(999999))
        assert (
            response.status_code == 404
        ), "POST /expenses/999999/delete must return 404 for a missing expense"

    def test_post_id_zero_returns_404(self, auth_client):
        """ID 0 is never a valid auto-increment primary key."""
        response = auth_client.post(_delete_url(0))
        assert response.status_code in (
            404,
            405,
        ), "POST /expenses/0/delete must return 404 (or 405 if Flask rejects it)"


# ================================================================== #
# 403 — expense belongs to another user                               #
# ================================================================== #


class TestForbidden:
    def test_post_other_users_expense_returns_403(self, app, auth_client, client):
        """
        When the logged-in user (owner) tries to delete an expense that was
        created by a different user, the route must return 403 Forbidden.

        Setup: register 'other' user, insert an expense for them, then use
        'auth_client' (logged-in as owner) to attempt the delete.
        """
        with app.app_context():
            # Register the other user directly via the DB so we can insert an expense.
            from database.db import create_user

            create_user(OTHER_NAME, OTHER_EMAIL, OTHER_PASSWORD)
            other_expense_id = _insert_expense_for_email(OTHER_EMAIL)

        response = auth_client.post(_delete_url(other_expense_id))
        assert (
            response.status_code == 403
        ), "POST to delete another user's expense must return 403 Forbidden"

    def test_post_other_users_expense_does_not_delete_row(
        self, app, auth_client, client
    ):
        """
        A 403 response must not have silently deleted the other user's expense.
        """
        with app.app_context():
            from database.db import create_user

            create_user(OTHER_NAME, OTHER_EMAIL, OTHER_PASSWORD)
            other_expense_id = _insert_expense_for_email(OTHER_EMAIL)

        auth_client.post(_delete_url(other_expense_id))

        with app.app_context():
            assert _expense_exists(
                other_expense_id
            ), "The other user's expense must still exist after a 403 attempt"


# ================================================================== #
# Happy path                                                          #
# ================================================================== #


class TestHappyPath:
    def test_valid_delete_returns_302(self, app, auth_client):
        with app.app_context():
            expense_id = _insert_expense_for_email(TEST_EMAIL)
        response = auth_client.post(_delete_url(expense_id))
        assert (
            response.status_code == 302
        ), "POST delete for own expense must return 302 redirect"

    def test_valid_delete_redirects_to_expenses(self, app, auth_client):
        with app.app_context():
            expense_id = _insert_expense_for_email(TEST_EMAIL)
        response = auth_client.post(_delete_url(expense_id))
        assert (
            "/expenses" in response.headers["Location"]
        ), "Redirect after delete must point to /expenses"

    def test_valid_delete_follows_redirect_returns_200(self, app, auth_client):
        with app.app_context():
            expense_id = _insert_expense_for_email(TEST_EMAIL)
        response = auth_client.post(_delete_url(expense_id), follow_redirects=True)
        assert (
            response.status_code == 200
        ), "Following the redirect after delete must return 200"

    def test_valid_delete_removes_row_from_db(self, app, auth_client):
        """After a successful delete the DB row must no longer exist."""
        with app.app_context():
            expense_id = _insert_expense_for_email(TEST_EMAIL)

        auth_client.post(_delete_url(expense_id))

        with app.app_context():
            assert not _expense_exists(
                expense_id
            ), "The expense row must be gone from the DB after a successful delete"

    def test_valid_delete_expense_not_on_expense_list(self, app, auth_client):
        """After delete, the deleted expense's description must not appear on /expenses."""
        with app.app_context():
            expense_id = _insert_expense_for_email(TEST_EMAIL)

        auth_client.post(_delete_url(expense_id))
        response = auth_client.get("/expenses")

        assert (
            SAMPLE_EXPENSE["description"].encode() not in response.data
        ), "Deleted expense must not appear on the /expenses list page"

    def test_valid_delete_expense_list_still_returns_200(self, app, auth_client):
        with app.app_context():
            expense_id = _insert_expense_for_email(TEST_EMAIL)
        auth_client.post(_delete_url(expense_id))
        response = auth_client.get("/expenses")
        assert (
            response.status_code == 200
        ), "GET /expenses after delete must still return 200"


# ================================================================== #
# Isolation — only the targeted row is deleted                        #
# ================================================================== #


class TestIsolation:
    def test_delete_one_expense_leaves_other_expenses_intact(self, app, auth_client):
        """
        When a user has two expenses and deletes one, the other must remain
        in the DB untouched.
        """
        with app.app_context():
            uid = _get_user_id_by_email(TEST_EMAIL)
            expense_id_to_delete = create_expense(
                uid, 100.00, "Food", "2026-01-01", "To be deleted"
            )
            expense_id_to_keep = create_expense(
                uid, 200.00, "Transport", "2026-01-02", "To be kept"
            )

        auth_client.post(_delete_url(expense_id_to_delete))

        with app.app_context():
            assert not _expense_exists(
                expense_id_to_delete
            ), "The targeted expense must be deleted"
            assert _expense_exists(
                expense_id_to_keep
            ), "The other expense belonging to the same user must still exist"

    def test_delete_does_not_affect_other_users_expenses(self, app, auth_client):
        """
        Deleting one user's expense must leave the other user's expenses
        completely unchanged.
        """
        with app.app_context():
            from database.db import create_user

            create_user(OTHER_NAME, OTHER_EMAIL, OTHER_PASSWORD)
            owner_expense_id = _insert_expense_for_email(TEST_EMAIL)
            other_expense_id = _insert_expense_for_email(OTHER_EMAIL)

        auth_client.post(_delete_url(owner_expense_id))

        with app.app_context():
            assert _expense_exists(
                other_expense_id
            ), "Another user's expense must not be removed when deleting one's own"


# ================================================================== #
# Delete button/form presence in rendered templates                   #
# ================================================================== #


class TestDeleteButtonPresence:
    """
    Verify that authenticated pages include delete forms pointing at the
    correct route pattern for each expense row.  We rely on a seeded expense
    so there is at least one row to render.
    """

    @pytest.fixture
    def seeded_auth_client(self, app, auth_client):
        """auth_client with one expense already inserted."""
        with app.app_context():
            expense_id = _insert_expense_for_email(TEST_EMAIL)
        return auth_client, expense_id

    def test_expenses_page_contains_delete_form(self, seeded_auth_client):
        """GET /expenses must render a form that posts to the delete route."""
        client, expense_id = seeded_auth_client
        response = client.get("/expenses")
        assert response.status_code == 200, "GET /expenses must return 200"
        delete_url_fragment = f"/expenses/{expense_id}/delete".encode()
        assert (
            delete_url_fragment in response.data
        ), f"GET /expenses must include a form action pointing to {delete_url_fragment!r}"

    def test_expenses_page_delete_form_uses_post(self, seeded_auth_client):
        """The delete form on /expenses must use method POST."""
        client, expense_id = seeded_auth_client
        response = client.get("/expenses")
        # The form must declare method="post" (case-insensitive in HTML)
        assert (
            b'method="post"' in response.data.lower()
            or b"method='post'" in response.data.lower()
        ), "The delete form on /expenses must use method POST"

    def test_dashboard_page_contains_delete_form(self, seeded_auth_client):
        """GET /dashboard must render a form that posts to the delete route."""
        client, expense_id = seeded_auth_client
        response = client.get("/dashboard")
        assert response.status_code == 200, "GET /dashboard must return 200"
        delete_url_fragment = f"/expenses/{expense_id}/delete".encode()
        assert (
            delete_url_fragment in response.data
        ), f"GET /dashboard must include a form action pointing to {delete_url_fragment!r}"

    def test_profile_page_contains_delete_form(self, seeded_auth_client):
        """GET /profile?period=all must render a form that posts to the delete route."""
        client, expense_id = seeded_auth_client
        response = client.get("/profile?period=all")
        assert response.status_code == 200, "GET /profile must return 200"
        delete_url_fragment = f"/expenses/{expense_id}/delete".encode()
        assert (
            delete_url_fragment in response.data
        ), f"GET /profile must include a form action pointing to {delete_url_fragment!r}"

    def test_expenses_page_no_delete_forms_when_no_expenses(self, auth_client):
        """
        When the user has no expenses, no delete form action should appear on
        the /expenses page (guard against phantom markup).
        """
        response = auth_client.get("/expenses")
        assert response.status_code == 200
        assert (
            b"/delete" not in response.data
        ), "No delete form actions should appear when the user has no expenses"


# ================================================================== #
# Double-delete — idempotency / second attempt                        #
# ================================================================== #


class TestDoubleDelete:
    def test_second_delete_of_same_expense_returns_404(self, app, auth_client):
        """
        After a successful delete, attempting to delete the same expense ID
        again must return 404 (the row is gone).
        """
        with app.app_context():
            expense_id = _insert_expense_for_email(TEST_EMAIL)

        auth_client.post(_delete_url(expense_id))  # first delete — success
        response = auth_client.post(_delete_url(expense_id))  # second delete — gone

        assert (
            response.status_code == 404
        ), "A second POST to delete the same (already-deleted) expense must return 404"
