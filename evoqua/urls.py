#
# This code was developed by frePPLe bv for Evoqua.
#
# Evoqua has full copyright and intellectual property rights.
# FrePPLe reserves the rights to apply the techniques and
# reuse the code for other implementations.
#

from django.urls import re_path

from .views import OverviewDemandProgressReport

# Automatically add these URLs when the application is installed
autodiscover = True

urlpatterns = [
    re_path(r"^demandprogress/$", OverviewDemandProgressReport.as_view()),
]
