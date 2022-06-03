#
# This code was developed by frePPLe bv for Evoqua.
#
# Evoqua has full copyright and intellectual property rights.
# FrePPLe reserves the rights to apply the techniques and
# reuse the code for other implementations.
#

from django.urls import re_path

from .views import (
    OverviewDemandProgressReport,
    UpstreamBufferPath,
    UpstreamDemandPath,
    UpstreamItemPath,
    UpstreamOperationPath,
    UpstreamResourcePath,
    DownstreamBufferPath,
    DownstreamItemPath,
    DownstreamOperationPath,
    DownstreamResourcePath,
)

# Automatically add these URLs when the application is installed
autodiscover = True

urlpatterns = [
    re_path(r"^demandprogress/$", OverviewDemandProgressReport.as_view()),
    re_path(
        r"^supplypath/item/(.+)/$",
        UpstreamItemPath.as_view(),
        name="supplypath_item",
    ),
    re_path(
        r"^whereused/item/(.+)/$",
        DownstreamItemPath.as_view(),
        name="whereused_item",
    ),
    re_path(
        r"^supplypath/buffer/(.+)/$",
        UpstreamBufferPath.as_view(),
        name="supplypath_buffer",
    ),
    re_path(
        r"^whereused/buffer/(.+)/$",
        DownstreamBufferPath.as_view(),
        name="whereused_buffer",
    ),
    re_path(
        r"^supplypath/resource/(.+)/$",
        UpstreamResourcePath.as_view(),
        name="supplypath_resource",
    ),
    re_path(
        r"^supplypath/demand/(.+)/$",
        UpstreamDemandPath.as_view(),
        name="supplypath_demand",
    ),
    re_path(
        r"^whereused/resource/(.+)/$",
        DownstreamResourcePath.as_view(),
        name="whereused_resource",
    ),
    re_path(
        r"^supplypath/operation/(.+)/$",
        UpstreamOperationPath.as_view(),
        name="supplypath_operation",
    ),
    re_path(
        r"^whereused/operation/(.+)/$",
        DownstreamOperationPath.as_view(),
        name="whereused_operation",
    ),
]
