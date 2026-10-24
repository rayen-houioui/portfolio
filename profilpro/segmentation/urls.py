from django.urls import path

from . import views, views_education, views_professional

urlpatterns = [
    path("health/", views.health),
    path("segmentation/profiles/", views.profiles),
    path("segmentation/predict/", views.predict),
    path("segmentation/analyze/", views.analyze),
    path("professional/clusters/", views_professional.clusters),
    path("professional/analyze/", views_professional.analyze),
    path("education/options/", views_education.options),
    path("education/predict/", views_education.predict),
    path("income/analyze/", views.income_analyze),
    path("income/report/", views.income_report),
    path("occupation/options/", views.occupation_options),
    path("occupation/analyze/", views.occupation_analyze),
    path("hours/analyze/", views.hours_analyze),
    path("salary/recommend/", views.salary_recommend),
    path("cv/analyze/", views.cv_analyze),
    path("stats/", views.stats),
    path("people/", views.people),
    path("candidates/", views.candidates_list),
    path("candidates/compare/", views.candidates_compare),
    path("candidates/<int:candidate_id>/outcome/", views.candidate_outcome),
]
