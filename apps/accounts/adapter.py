"""
Custom account adapter for ELECTROCART (WP2 / R7).
Stores pending verification email in session for masked display and resend functionality.
"""

from allauth.account.adapter import DefaultAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom allauth adapter that tracks the newly registered user's email
    for masked display and resend flows on verification_sent page.
    """

    def respond_email_verification_sent(self, request, user):
        if user and getattr(user, "email", None):
            request.session["account_verification_email"] = user.email
            request.session["account_verification_user_id"] = user.pk
        return super().respond_email_verification_sent(request, user)
