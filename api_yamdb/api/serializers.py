import datetime

from django.conf import settings
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from reviews.models import Category, Comment, Genre, Review, Title
from users.models import User


class FullUserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'first_name', 'last_name', 'username',
            'bio', 'role', 'email'
        )
        model = User


class UserEmailCodeSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, max_length=128)
    confirmation_code = serializers.IntegerField(required=True)

    def validate(self, data):
        confirmation_code = data['confirmation_code']
        user = get_object_or_404(User, username=data['username'])
        if confirmation_code == settings.RESET_CONFIRMATION_CODE:
            raise serializers.ValidationError(
                ('Данный код подтверждения уже был использован.')
            )
        if user.confirmation_code != confirmation_code:
            raise serializers.ValidationError('Неверный код подтверждения')
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email')

    def validate(self, data):
        if data['username'] == 'me':
            raise serializers.ValidationError('Username "me" уже занято.')
        return data


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('name', 'slug')
        model = Genre
        lookup_field = 'slug'


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('name', 'slug')
        model = Category
        lookup_field = 'slug'


class TitlePostSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        required=True,
        queryset=Category.objects.all(),
        slug_field='slug'
    )
    genre = serializers.SlugRelatedField(
        required=True,
        many=True,
        queryset=Genre.objects.all(),
        slug_field='slug'
    )

    class Meta:
        fields = '__all__'
        model = Title

    def validate_year(self, value):
        year = datetime.datetime.now().year
        if not (value <= year):
            raise serializers.ValidationError('Year cant be more current year')
        return value


class TitleGetSerializer(serializers.ModelSerializer):
    category = CategorySerializer(required=True)
    genre = GenreSerializer(many=True, required=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = (
            'id',
            'genre',
            'name',
            'description',
            'year',
            'category',
            'rating'
        )


class ReviewSerializer(serializers.ModelSerializer):
    title = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True
    )
    author = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Review
        fields = '__all__'

    def validate(self, data):
        request = self.context.get('request')
        if request.method != 'POST':
            return data
        title = self.context.get('view').kwargs.get('title_id')
        if Review.objects.filter(author=request.user, title=title).exists():
            raise serializers.ValidationError(
                'Нельзя создавать больше одного обзора'
            )
        return data


class CommentSerializer(serializers.ModelSerializer):
    review = serializers.SlugRelatedField(
        slug_field='text',
        read_only=True
    )
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Comment
        fields = '__all__'
