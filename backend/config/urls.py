"""
URL configuration for ClinSaarthi AI backend.
Provides cleanly versioned /api/v1/ routes with strict separation of domain apps.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.conf import settings

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint returning system status, environment, and active model IDs.
    Demonstrates thin functional views with zero business logic.
    """
    return Response({
        "status": "healthy",
        "service": "ClinSaarthi AI Backend",
        "version": "1.0.0",
        "environment": getattr(settings, 'ENVIRONMENT', 'dev'),
        "models": {
            "llm": getattr(settings, 'LLM_MODEL_ID', None),
            "embeddings": getattr(settings, 'EMBEDDING_MODEL_ID', None),
            "reranker": getattr(settings, 'RERANKER_MODEL_ID', None),
            "vector_store": getattr(settings, 'VECTOR_STORE_PROVIDER', None),
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health-check'),

    # Version 1 API domain endpoints
    path('api/v1/auth/', include('apps.accounts.urls', namespace='accounts')),
    path('api/v1/documents/', include('apps.documents.urls', namespace='documents')),
    path('api/v1/notes/', include('apps.notes.urls', namespace='notes')),
    path('api/v1/qa/', include('apps.qa.urls', namespace='qa')),
    path('api/v1/study/', include('apps.study.urls', namespace='study')),
    path('api/v1/evaluation/', include('apps.evaluation.urls', namespace='evaluation')),
]
