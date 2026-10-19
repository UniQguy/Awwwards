import uuid
from django.db import models


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created_at`` and ``updated_at`` fields.

    Note: QuerySet.update() and bulk_update() do not touch updated_at;
    it must be passed explicitly in bulk update queries.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """
    An abstract base class model that provides a unique UUID4
    field for tamper-proof public identification.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    class Meta:
        abstract = True


class ContactMessage(TimeStampedModel):
    """
    Customer inquiry or support message submitted via contact form (WP7).
    """

    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    resolved = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} ({self.email})"


class SupportTicket(TimeStampedModel):
    """
    Customer support and return ticket submitted via concierge portal (Phase R8).
    """

    ticket_id = models.CharField(max_length=30, unique=True, db_index=True)
    order_number = models.CharField(max_length=40, blank=True)
    email = models.EmailField()
    issue_category = models.CharField(max_length=50)
    message = models.TextField()
    resolved = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Support Ticket"
        verbose_name_plural = "Support Tickets"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ticket_id} ({self.issue_category}) - {self.email}"

