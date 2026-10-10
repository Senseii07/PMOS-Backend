from django.urls import path

from .views import (
    AdminHealthSummaryView,
    MealLogDetailView,
    MealLogListCreateView,
    SymptomLogDetailView,
    SymptomLogListCreateView,
    WaterLogListCreateView,
    WeightLogListCreateView,
)

urlpatterns = [
    path("meals/", MealLogListCreateView.as_view(), name="meal-list-create"),
    path("meals/<int:pk>/", MealLogDetailView.as_view(), name="meal-detail"),
    path("symptoms/", SymptomLogListCreateView.as_view(), name="symptom-list-create"),
    path("symptoms/<int:pk>/", SymptomLogDetailView.as_view(), name="symptom-detail"),
    path("water/", WaterLogListCreateView.as_view(), name="water-list-create"),
    path("weight/", WeightLogListCreateView.as_view(), name="weight-list-create"),
    path("admin/summary/", AdminHealthSummaryView.as_view(), name="admin-health-summary"),
]
