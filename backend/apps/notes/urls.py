"""
URL Routing for Clinical Notes
"""
from django.urls import path
from .views import (
    ClinicalNoteListView,
    ClinicalNoteUploadView,
    ClinicalNoteDetailView,
    ClinicalNoteDiffView,
)

app_name = 'notes'

urlpatterns = [
    path('', ClinicalNoteListView.as_view(), name='note_list'),
    path('upload/', ClinicalNoteUploadView.as_view(), name='note_upload'),
    path('<uuid:pk>/', ClinicalNoteDetailView.as_view(), name='note_detail'),
    path('<uuid:pk>/diff/', ClinicalNoteDiffView.as_view(), name='note_diff'),
]
