#
# This code was developed by frePPLe bv for Evoqua.
#
# Evoqua has full copyright and intellectual property rights.
# FrePPLe reserves the rights to apply the techniques and
# reuse the code for other implementations.
#


from freppledb.menu import menu
from freppledb.input.models import ManufacturingOrder
from .views import OverviewDemandProgressReport

menu.addItem(
    "capacity",
    "Demand Progress",
    url="/demandprogress/",
    report=OverviewDemandProgressReport,
    index=250,
    model=ManufacturingOrder,
    dependencies=[ManufacturingOrder],
)
