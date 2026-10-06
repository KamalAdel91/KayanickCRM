"""Account screens for the mobile app: change my password, and admin password reset."""
import frappe
from frappe import _
from frappe.utils import cint, today

from kayanick_crm.perms import can_reset_passwords

MIN_LENGTH = 8
MAX_LENGTH = 512


def _require_login():
    if frappe.session.user == "Guest":
        frappe.throw(_("Please log in"), frappe.PermissionError)


def _can_reset(user=None):
    return can_reset_passwords(user)


def _require_admin():
    _require_login()
    if not _can_reset():
        frappe.throw(_("Only admins can reset other users' passwords"), frappe.PermissionError)


def _check_new_password(user, password):
    """Basic length rules plus the site's password policy (System Settings), if enabled."""
    from frappe.core.doctype.user.user import test_password_strength

    if len(password) < MIN_LENGTH:
        frappe.throw(_("Password must be at least {0} characters").format(MIN_LENGTH))
    if len(password) > MAX_LENGTH:
        frappe.throw(_("Password is too long"))

    user_data = frappe.db.get_value("User", user, ["first_name", "middle_name", "last_name", "email", "birth_date"])
    result = test_password_strength(password, user_data=user_data) or {}
    feedback = result.get("feedback")
    if feedback and not feedback.get("password_policy_validation_passed", False):
        parts = [feedback.get("warning") or ""] + list(feedback.get("suggestions") or [])
        msg = "\n".join(p for p in parts if p) or _("Password is too weak. Add a few more letters or another word")
        frappe.throw(msg, title=_("Password too weak"))


def _set_password(user, password):
    from frappe.utils.password import update_password

    update_password(user, password)
    frappe.db.set_value("User", user, "last_password_reset_date", today())


@frappe.whitelist()
def get_account():
    _require_login()
    user = frappe.session.user
    full_name = frappe.db.get_value("User", user, "full_name") or user
    return {"user": user, "full_name": full_name, "can_reset_passwords": _can_reset(user)}


@frappe.whitelist(methods=["POST"])
def change_password(old_password, new_password, logout_others=0):
    """The logged-in user changes his own password. The current session stays signed in."""
    from frappe.sessions import clear_sessions
    from frappe.utils.password import check_password

    _require_login()
    user = frappe.session.user
    if not old_password or not new_password:
        frappe.throw(_("Enter your current and new password"))
    if old_password == new_password:
        frappe.throw(_("New password must be different from the current one"))

    try:
        check_password(user, old_password)
    except frappe.AuthenticationError:
        # don't let this surface as a 401: the app would treat it as an expired session
        frappe.clear_messages()
        frappe.throw(_("Current password is incorrect"))

    _check_new_password(user, new_password)
    _set_password(user, new_password)

    if cint(logout_others) or cint(frappe.get_system_settings("logout_on_password_reset")):
        clear_sessions(user=user, keep_current=True, force=True)
    return {"ok": True}


@frappe.whitelist()
def search_users(text=""):
    """Users an admin can reset a password for (enabled, not Administrator/Guest, not himself)."""
    _require_admin()
    text = (text or "").strip()[:60]
    kw = dict(
        filters={"enabled": 1, "name": ["not in", ["Administrator", "Guest", frappe.session.user]]},
        fields=["name", "full_name"], order_by="full_name asc", limit_page_length=100,
    )
    if text:
        kw["or_filters"] = [["full_name", "like", "%" + text + "%"], ["name", "like", "%" + text + "%"]]
    return frappe.get_all("User", **kw)


@frappe.whitelist(methods=["POST"])
def admin_reset_password(user, new_password, logout_all=1):
    """An admin sets a new password for another user (no old password needed)."""
    from frappe.sessions import clear_sessions

    _require_admin()
    if user in ("Administrator", "Guest"):
        frappe.throw(_("This user's password can't be reset from the app"))
    if user == frappe.session.user:
        frappe.throw(_("Use Change password for your own account"))
    if not frappe.db.exists("User", {"name": user, "enabled": 1}):
        frappe.throw(_("User {0} not found or disabled").format(user))
    if not new_password:
        frappe.throw(_("Enter the new password"))

    _check_new_password(user, new_password)
    _set_password(user, new_password)

    if cint(logout_all):
        clear_sessions(user=user, force=True)

    frappe.get_doc("User", user).add_comment(
        "Info", _("Password reset from Kayanick CRM by {0}").format(frappe.session.user)
    )
    return {"ok": True}
