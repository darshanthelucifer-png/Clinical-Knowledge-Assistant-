"""
URL Routing for Q&A
"""
from django.urls import path
from .views import (
    ConversationListView,
    ConversationDetailView,
    ConversationExportView,
    RetrieveDebugView,
    AskQuestionView,
)

app_name = 'qa'

urlpatterns = [
    path('conversations/', ConversationListView.as_view(), name='conversation_list'),
    path('conversations/<uuid:pk>/', ConversationDetailView.as_view(), name='conversation_detail'),
    path('conversations/<uuid:pk>/export/', ConversationExportView.as_view(), name='conversation_export'),
    path('retrieve/', RetrieveDebugView.as_view(), name='retrieve_debug'),
    path('ask/', AskQuestionView.as_view(), name='ask_question'),
]
