"""
URL Routing for Documents & Chunks
"""
from django.urls import path
from .views import (
    DocumentListCreateView,
    DocumentDetailView,
    DocumentChunksListView,
    DocumentIngestTriggerView,
    IngestJobDetailView
)

app_name = 'documents'

urlpatterns = [
    path('', DocumentListCreateView.as_view(), name='document_list_create'),
    path('<uuid:pk>/', DocumentDetailView.as_view(), name='document_detail'),
    path('<uuid:pk>/ingest/', DocumentIngestTriggerView.as_view(), name='document_ingest'),
    path('<uuid:document_id>/chunks/', DocumentChunksListView.as_view(), name='document_chunks'),
    path('jobs/<uuid:pk>/', IngestJobDetailView.as_view(), name='ingest_job_detail'),
]
