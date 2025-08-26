from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegistrationView, UserLoginView, UserProfileDetailView,
    GroupViewSet, UserProfileListView, GroupJoinRequestView, 
    ManageJoinRequestView, ApproveRejectJoinRequestView,
    ChatMessageViewSet, GroupChatView,
    NotificationViewSet, NotificationListView, MarkNotificationReadView,
    TestNotificationView, ClearNotificationsView, LogoutView, UserGroupsView
)

router = DefaultRouter()
router.register(r'groups', GroupViewSet, basename='group')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('notifications/clear/', ClearNotificationsView.as_view(), name='clear-notifications'),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('profile/', UserProfileListView.as_view(), name='user-profile-list'),
    path('profile/<str:identifier>/', UserProfileDetailView.as_view(), name='user-profile-detail'),
    path('groups/<int:group_id>/request-join/', GroupJoinRequestView.as_view(), name='request-join-group'), ## i used this for join request
    path('groups/join-requests/', ManageJoinRequestView.as_view(), name='list-join-requests'),
    path('groups/<int:group_id>/join-request/', GroupJoinRequestView.as_view(), name='request-join-group'),
    path('groups/<int:group_id>/requests/<str:username>/', 
         ApproveRejectJoinRequestView.as_view(), 
         name='approve-reject-request'),
    path('chat/group/<int:group_id>/', GroupChatView.as_view(), name='group-chat'),
    path('chat/rooms/<int:room_id>/messages/', 
         ChatMessageViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='room-messages'),
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/read/', MarkNotificationReadView.as_view(), name='mark-notification-read'),
    path('test-notification/', TestNotificationView.as_view(), name='test-notification'),
    path('logout/', LogoutView.as_view(), name='user-logout'),
    path('my-groups/', UserGroupsView.as_view(), name='user-groups'),
] + router.urls