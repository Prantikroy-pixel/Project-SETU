"""
Matching models for SETU.
Defines Match join table between Need and Resource with scoring explainability breakdown.
"""

from django.db import models


class Match(models.Model):
    STATUS_PROPOSED = 'proposed'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PROPOSED, 'Proposed Match'),
        (STATUS_CONFIRMED, 'Confirmed / Allocated'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    need = models.ForeignKey(
        'core.Need',
        on_delete=models.CASCADE,
        related_name='matches'
    )
    resource = models.ForeignKey(
        'core.Resource',
        on_delete=models.CASCADE,
        related_name='matches'
    )
    score = models.FloatField(
        help_text="Composite match score computed by matching_engine (0.0 to 1.0)"
    )
    score_breakdown = models.JSONField(
        default=dict,
        help_text='Granular factors e.g. {"urgency": 0.9, "proximity": 0.85, "verification": 1.0, ...}'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PROPOSED
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score', '-created_at']
        unique_together = ('need', 'resource')

    def __str__(self):
        return f"Match #{self.pk}: Need #{self.need_id} <-> Resource #{self.resource_id} (Score: {self.score:.2f})"
