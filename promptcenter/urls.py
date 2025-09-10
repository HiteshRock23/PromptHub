from django.urls import path

from . import views


urlpatterns = [
    # Make Hub the landing page
    path('', views.hub_view, name='hub-page'),
    path('hub/', views.hub_view),
    path('hub/p/<int:pid>/', views.xml_prompt_detail, name='xml-prompt-detail'),
    path('contribute/', views.contribution_view, name='contribution-page'),
    path('api/prompts/', views.prompts_api, name='prompts-api'),
    path('api/xml-prompts/', views.xml_prompts_api, name='xml-prompts-api'),
]


