from api.views import (AdminUserViewSet, CategoryViewSet, CommentViewSet,
                       GenreViewSet, GetTokenViewSet, ReviewViewSet,
                       TitleViewSet, UserViewSet)
from django.urls import include, path
from rest_framework import routers
from rest_framework.routers import DefaultRouter

app_name = 'api'


router = DefaultRouter()

router.register('titles', TitleViewSet, basename='titles')
router.register('genres', GenreViewSet, basename='genres')
router.register('categories', CategoryViewSet, basename='categories')

router.register(
    r'titles/(?P<title_id>\d+)/reviews',
    ReviewViewSet, basename='reviews'
)
router.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet, basename='comments'
)
router.register('users', AdminUserViewSet, basename='admin_user')

auth_router = routers.DefaultRouter()
auth_router.register('signup', UserViewSet, basename='signup')
auth_router.register('token', GetTokenViewSet, basename='token')


urlpatterns = [
    path('v1/', include(router.urls)),
    path('v1/auth/', include(auth_router.urls)),
]
