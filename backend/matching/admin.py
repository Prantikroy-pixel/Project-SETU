from django.contrib import admin
from .models import Match


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['id', 'need', 'resource', 'score', 'status', 'created_at']
    list_filter = ['status']
