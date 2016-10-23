from django.conf.urls import include, url
from . import views

urlpatterns = [
	url(r'^$', views.entry, name='home'),
	url(r'^signup$', views.signup, name='signup'),
	url(r'^view$', views.view, name='view'),
	url(r'^restart$', views.restart, name='restart'),
	url(r'^cmd$', views.cmd, name='cmd'),
	url(r'^edit$', views.edit, name='edit'),
	url(r'^balance$', views.balance, name='balance'),
	url(r'^pay$', views.pay, name='pay'),
	url(r'^request$', views.req, name='request'),
	url(r'^payrequest$', views.payrequest, name='payrequest'),
	url(r'^viewdb$', views.viewdb, name='viewdb')
]