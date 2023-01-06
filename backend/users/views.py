from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import Follow
from users.permissions import IsAdminOrReadOnly
from users.serializers import CustomUserSerializer, FollowerSerializer

YOUSELF_SUBSCRIBE_MSG = 'Нельзя подписаться на самого себя!'
NO_UNIQUE_SUBSCRIBE_MSG = 'Вы уже подписаны на этого автора!'
YOUSELF_SUBSCRIBE_DEL_MSG = 'Нельзя отписаться от самого себя!'
NO_SUBSCIBE_MSG = 'Вы не подписаны на этого автора!'

User = get_user_model()


class SubsctiptionUserViewSet(UserViewSet):
    """Набор представлений для подписки."""

    permission_classes = [IsAdminOrReadOnly]
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = LimitOffsetPagination

    def perform_create(self, serializer):
        hash_pwd = make_password(serializer.validated_data.get('password'))
        serializer.save(password=hash_pwd)

    @action(methods=['post'], detail=True,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        """Функция подписки на автора."""

        user = request.user
        author = get_object_or_404(User, pk=id)

        if user == author:
            return Response({
                'errors': YOUSELF_SUBSCRIBE_MSG
            }, status=status.HTTP_400_BAD_REQUEST)

        if Follow.objects.filter(user=user, author=author).exists():
            return Response({
                'errors': NO_UNIQUE_SUBSCRIBE_MSG
            }, status=status.HTTP_400_BAD_REQUEST)

        Follow.objects.create(
            user=user, author=author
        )
        serializer = FollowerSerializer(
            author, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        """Функции отписки от автора."""

        user = request.user
        author = get_object_or_404(User, pk=id)

        if user == author:
            return Response({
                'errors': YOUSELF_SUBSCRIBE_DEL_MSG
            }, status=status.HTTP_400_BAD_REQUEST)

        subscribe = Follow.objects.filter(user=user, author=author)

        if not subscribe.exists():
            return Response({
                'errors': NO_SUBSCIBE_MSG
            }, status=status.HTTP_400_BAD_REQUEST)
        subscribe.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticated], url_path='subscriptions')
    def subscriptions(self, request):
        subscriptions = User.objects.filter(following__user=self.request.user)
        page = self.paginate_queryset(subscriptions)
        serializer = FollowerSerializer(page, many=True,
                                        context={'request': request})

        return self.get_paginated_response(serializer.data)
