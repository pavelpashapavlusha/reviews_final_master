from api.permissions import (IsAdminModeratorAuthorOrReadOnly,
                             IsAdminOrReadOnly, IsAdminOrSuperUser)
from api.serializers import (FullUserSerializer, UserEmailCodeSerializer,
                             UserSerializer)
from django.conf import settings
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (filters, mixins, pagination, permissions, status,
                            viewsets)
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from reviews.models import Category, Comment, Genre, Review, Title
from users.models import User

from .filter import TitlesFilter
from .mixins import CreateListDestroyViewSet
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, ReviewSerializer,
                          TitleGetSerializer, TitlePostSerializer)
from .utils import email_code, send_email


class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = FullUserSerializer
    filter_backends = (filters.SearchFilter,)
    lookup_field = 'username'
    permission_classes = (IsAdminOrSuperUser,)
    pagination_class = pagination.LimitOffsetPagination
    search_fields = ('username',)

    @action(
        detail=False, url_path='me', methods=['GET', 'PATCH'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def user_get_patch_page(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save(role=user.role, partial=True)
            return Response(serializer.data, status=status.HTTP_200_OK)


class UserViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_200_OK, headers=headers
        )

    def perform_create(self, serializer):
        code = email_code()
        send_email(serializer.validated_data.get('email'), code)
        serializer.save(confirmation_code=code)


class GetTokenViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserEmailCodeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        headers = self.get_success_headers(serializer.data)
        user = get_object_or_404(
            User, username=serializer.data.get('username')
        )
        user.confirmation_code = settings.RESET_CONFIRMATION_CODE
        user.save()
        token = AccessToken.for_user(user)
        return Response(
            {'token': str(token)}, status=status.HTTP_200_OK, headers=headers
        )


class GenreViewSet(CreateListDestroyViewSet):
    queryset = Genre.objects.all()
    pagination_class = pagination.LimitOffsetPagination
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly, ]
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class CategoryViewSet(CreateListDestroyViewSet):
    queryset = Category.objects.all()
    pagination_class = pagination.LimitOffsetPagination
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly, ]
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.annotate(
        rating=Avg('reviews__score')
    ).order_by('id')
    pagination_class = pagination.LimitOffsetPagination
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitlesFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TitleGetSerializer
        return TitlePostSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAdminModeratorAuthorOrReadOnly, ]

    def get_queryset(self):
        queryset = Review.objects.filter(title=self.get_title()).all()
        return queryset

    def get_title(self):
        title = get_object_or_404(Title, pk=self.kwargs['title_id'])
        return title

    def perform_create(self, serializer):
        queryset = self.get_queryset().filter(author=self.request.user)
        if queryset.exists():
            raise ValidationError({'detail': 'Такой обзор уже существует'})
        serializer.save(author=self.request.user, title=self.get_title())


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAdminModeratorAuthorOrReadOnly, ]
    pagination_class = pagination.LimitOffsetPagination

    def get_queryset(self):
        queryset = Comment.objects.all()
        review = get_object_or_404(Review, pk=self.kwargs['review_id'])
        if review is not None:
            queryset = Comment.objects.filter(
                review=self.kwargs.get('review_id')
            )
        return queryset

    def perform_create(self, serializer):
        review = get_object_or_404(Review, id=self.kwargs['review_id'])
        serializer.save(author=self.request.user, review=review)
