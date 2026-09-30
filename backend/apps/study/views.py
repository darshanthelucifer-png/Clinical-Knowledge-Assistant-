"""
Study Mode Views
"""
from rest_framework import generics, permissions
from .models import Quiz, FlashcardSet
from .serializers import QuizSerializer, FlashcardSetSerializer

class QuizListView(generics.ListCreateAPIView):
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class QuizDetailView(generics.RetrieveAPIView):
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user)

class FlashcardSetListView(generics.ListCreateAPIView):
    serializer_class = FlashcardSetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FlashcardSet.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FlashcardSetDetailView(generics.RetrieveAPIView):
    serializer_class = FlashcardSetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FlashcardSet.objects.filter(user=self.request.user)
