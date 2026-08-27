from django.urls import path
from .views import index, view_document

urlpatterns = [
    path('', index, name='spellbound_index'),
    path('portfolio/<slug:slug>/', view_document, name='portfolio_doc'),
    path('portfolio/<slug:slug>.html', view_document),
]