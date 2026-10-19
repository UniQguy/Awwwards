"""
Core application views for system health, legal policy pages, error handlers, and request helpers.
"""

from django.conf import settings
from django.db import DatabaseError, connections
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render


def health_check(request):
    """
    Operational health check endpoint.
    Actively verifies default database connectivity before returning status ok.
    """
    try:
        connection = connections["default"]
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse(
            {"status": "ok", "service": "electrocart", "database": "healthy"},
            status=200,
        )
    except DatabaseError as exc:
        return JsonResponse(
            {
                "status": "error",
                "service": "electrocart",
                "database": "unhealthy",
                "detail": str(exc),
            },
            status=503,
        )


def is_json_request(request) -> bool:
    """
    Detects if client expects a JSON response (for AJAX progressive enhancement).
    """
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in request.headers.get("Accept", "")
    )


# ==============================================================================
# LEGAL & EDITORIAL STATIC PAGES
# ==============================================================================

def legal_terms(request):
    return render(request, "pages/terms.html")


def legal_privacy(request):
    return render(request, "pages/privacy.html")


def legal_shipping(request):
    return render(request, "pages/shipping.html")


def legal_refunds(request):
    return render(request, "pages/refunds.html")


def about(request):
    return render(request, "pages/about.html")


def contact_us(request):
    """
    Customer inquiry and feedback submission form (WP7).
    Saves message to database as ContactMessage and alerts staff in admin.
    """
    from django.contrib import messages
    from django.shortcuts import redirect
    from django_ratelimit.decorators import ratelimit
    from .models import ContactMessage

    if getattr(request, "limited", False):
        return error_429(request)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        subject = request.POST.get("subject", "").strip()
        message = request.POST.get("message", "").strip()

        if not name or not email or not message:
            messages.error(request, "Please provide your name, a valid email address, and message.")
            return render(
                request,
                "pages/contact.html",
                {"name": name, "email": email, "subject": subject, "message": message},
            )

        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject or "General Inquiry",
            message=message,
        )
        messages.success(request, "Thank you for reaching out. Your message has been recorded.")
        return redirect("contact")

    return render(request, "pages/contact.html")


def support_concierge(request):
    """
    Dedicated Customer Service & Support Concierge portal (Phase R8).
    Includes Support Ticket Form, 7-Day DOA Matrix, and Interactive FAQs.
    """
    import secrets
    from django.contrib import messages
    from django.core.mail import EmailMultiAlternatives
    from .models import SupportTicket

    ticket_id = None
    success = False

    if request.method == "POST":
        order_number = request.POST.get("order_number", "").strip().upper()
        email = request.POST.get("email", "").strip()
        issue_category = request.POST.get("issue_category", "Technical Support").strip()
        message = request.POST.get("message", "").strip()

        if not email or not message:
            messages.error(request, "Please enter a valid email address and inquiry description.")
        else:
            ticket_id = f"TKT-2026-{secrets.token_hex(3).upper()}"
            ticket = SupportTicket.objects.create(
                ticket_id=ticket_id,
                order_number=order_number,
                email=email,
                issue_category=issue_category,
                message=message,
            )
            success = True

            # Send email confirmation
            from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "support@electrocart.local")
            subject = f"Support Ticket Logged: #{ticket_id}"
            body_text = (
                f"Your support inquiry #{ticket_id} has been registered.\n\n"
                f"Category: {issue_category}\n"
                f"Order Number: {order_number or 'N/A'}\n"
                f"Message: {message}\n\n"
                f"Our engineering support team in Ahmedabad will review and reply within 24 hours.\n\n"
                f"ElectroCart Customer Concierge"
            )
            html_text = (
                f"<div style='font-family: sans-serif; max-width: 600px; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;'>"
                f"<h2 style='color: #0f172a; margin-top: 0;'>Support Ticket #{ticket_id} Registered</h2>"
                f"<p style='color: #475569;'>We have received your support request regarding <strong>{issue_category}</strong>.</p>"
                f"<p style='color: #475569;'>Order Number: <strong>{order_number or 'Not Specified'}</strong></p>"
                f"<p style='color: #475569;'>Our engineering and concierge team in Ahmedabad will investigate and follow up promptly.</p>"
                f"<p style='color: #94a3b8; font-size: 12px; margin-bottom: 0;'>ElectroCart Ahmedabad &middot; Honest Hardware Support</p>"
                f"</div>"
            )
            try:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=body_text,
                    from_email=from_email,
                    to=[email],
                )
                msg.attach_alternative(html_text, "text/html")
                msg.send(fail_silently=False)
            except Exception:
                pass

    context = {
        "ticket_id": ticket_id,
        "success": success,
        "breadcrumbs": [{"title": "Support Concierge", "url": "/support/"}],
    }
    return render(request, "pages/support.html", context)



def robots_txt(request):
    site_url = getattr(settings, "SITE_URL", "http://localhost:8000").rstrip("/")
    admin_slug = getattr(settings, "ADMIN_URL", "admin/").strip("/")
    lines = [
        "User-agent: *",
        "Disallow: /cart/",
        "Disallow: /checkout/",
        "Disallow: /account/",
        "Disallow: /orders/",
        f"Disallow: /{admin_slug}/",
        "Disallow: /search/",
        "",
        f"Sitemap: {site_url}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


# ==============================================================================
# CUSTOM ERROR HANDLERS (WP1)
# ==============================================================================

def csrf_failure(request, reason=""):
    """
    Renders custom 403 CSRF page with calm retry copy.
    """
    retry_url = request.META.get("HTTP_REFERER") or "/cart/"
    return render(
        request,
        "403_csrf.html",
        {
            "retry_url": retry_url,
            "reason": reason,
        },
        status=403,
    )


def error_400(request, exception=None):
    return render(request, "400.html", status=400)


def error_403(request, exception=None):
    if exception and "Ratelimited" in type(exception).__name__:
        return error_429(request, exception)
    return render(request, "403.html", status=403)


def error_404(request, exception=None):
    return render(request, "404.html", status=404)


def error_500(request):
    """
    500 error handler. Must not query database or depend on global context processors.
    """
    return render(request, "500.html", status=500)


def error_429(request, exception=None):
    """
    HTTP 429 Too Many Requests rate-limit failure view.
    """
    return render(request, "429.html", status=429)
