"""
Core application views for system health and operational liveness.
"""

from django.db import DatabaseError, connections
from django.http import JsonResponse


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
