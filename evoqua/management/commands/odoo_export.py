#
# This code was developed by frePPLe bv for Evoqua.
#
# Evoqua has full copyright and intellectual property rights.
# FrePPLe reserves the rights to apply the techniques and
# reuse the code for other implementations.
#

from datetime import datetime, timedelta
import jwt
import time
from xml.sax.saxutils import quoteattr

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from freppledb.input.models import ManufacturingOrder, DistributionOrder, PurchaseOrder

from freppledb.odoo.management.commands import Command as StdCommand


class Command(StdCommand):

    def generateDataToPublish(self):
        yield "--%s\r" % self.boundary
        yield 'Content-Disposition: form-data; name="webtoken"\r'
        yield "\r"
        yield "%s\r" % jwt.encode(
            {"exp": round(time.time()) + 600, "user": self.odoo_user},
            settings.DATABASES[self.database].get(
                "SECRET_WEBTOKEN_KEY", settings.SECRET_KEY
            ),
            algorithm="HS256",
        ).decode("ascii")
        yield "--%s\r" % self.boundary
        yield 'Content-Disposition: form-data; name="database"\r'
        yield "\r"
        yield "%s\r" % self.odoo_db
        yield "--%s\r" % self.boundary
        yield 'Content-Disposition: form-data; name="language"\r'
        yield "\r"
        yield "%s\r" % self.odoo_language
        yield "--%s\r" % self.boundary
        yield 'Content-Disposition: form-data; name="company"\r'
        yield "\r"
        yield "%s\r" % self.odoo_company
        yield "--%s\r" % self.boundary
        yield 'Content-Disposition: file; name="frePPLe plan"; filename="frepple_plan.xml"\r'
        yield "Content-Type: application/xml\r"
        yield "\r"
        yield '<?xml version="1.0" encoding="UTF-8" ?>'
        yield '<plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        yield "<operationplans>"
        today = datetime.today()

        # COMMENTED OUT SOME OF THE STANDARD EXPORT

        # # Purchase orders to export
        # for i in (
        #     PurchaseOrder.objects.using(self.database)
        #     .filter(
        #         status="proposed",
        #         item__source__startswith="odoo",
        #         startdate__lte=today + timedelta(days=7),
        #     )
        #     .order_by("startdate")
        #     .select_related("location", "item", "supplier")
        # ):
        #     if (
        #         i.status not in ("proposed", "approved")
        #         or not i.item
        #         or not i.item.source
        #         or not i.item.subcategory
        #         or not i.location.subcategory
        #         or not i.item.source.startswith("odoo")
        #         or i.supplier.name == "Unknown supplier"
        #     ):
        #         continue
        #     self.exported.append(i)
        #     yield '<operationplan reference=%s ordertype="PO" item=%s location=%s supplier=%s start="%s" end="%s" quantity="%s" location_id=%s item_id=%s criticality="%d" batch=%s/>' % (
        #         quoteattr(i.reference),
        #         quoteattr(i.item.name),
        #         quoteattr(i.location.name),
        #         quoteattr(i.supplier.name),
        #         i.startdate,
        #         i.enddate,
        #         i.quantity,
        #         quoteattr(i.location.subcategory),
        #         quoteattr(i.item.subcategory),
        #         int(i.criticality),
        #         quoteattr(i.batch or ""),
        #     )

        # # Distribution orders to export
        # for i in (
        #     DistributionOrder.objects.using(self.database)
        #     .filter(
        #         status="proposed",
        #         item__source__startswith="odoo",
        #         startdate__lte=today + timedelta(days=7),
        #     )
        #     .order_by("startdate")
        #     .select_related("item", "origin", "destination")
        # ):
        #     if (
        #         i.status not in ("proposed", "approved")
        #         or not i.item
        #         or not i.item.source
        #         or not i.item.subcategory
        #         or not i.origin.subcategory
        #         or not i.destination.subcategory
        #         or not i.item.source.startswith("odoo")
        #     ):
        #         continue
        #     self.exported.append(i)
        #     yield '<operationplan status="%s" reference=%s ordertype="DO" item=%s origin=%s destination=%s start="%s" end="%s" quantity="%s" origin_id=%s destination_id=%s item_id=%s criticality="%d" batch=%s/>' % (
        #         i.status,
        #         quoteattr(i.reference),
        #         quoteattr(i.item.name),
        #         quoteattr(i.origin.name),
        #         quoteattr(i.destination.name),
        #         i.startdate,
        #         i.enddate,
        #         i.quantity,
        #         quoteattr(i.origin.subcategory),
        #         quoteattr(i.destination.subcategory),
        #         quoteattr(i.item.subcategory),
        #         int(i.criticality),
        #         quoteattr(i.batch or ""),
        #     )

        # # Manufacturing orders to export
        # for i in (
        #     ManufacturingOrder.objects.using(self.database)
        #     .filter(
        #         item__source__startswith="odoo",
        #         operation__source__startswith="odoo",
        #         operation__owner__isnull=True,
        #         status="proposed",
        #         startdate__lte=today + timedelta(days=7),
        #     )
        #     .order_by("startdate")
        #     .select_related("operation", "location", "item", "owner")
        # ):
        #     if (
        #         i.status not in ("proposed", "approved")
        #         or not i.operation
        #         or not i.operation.source
        #         or not i.operation.item
        #         or not i.operation.source.startswith("odoo")
        #         or not i.item.subcategory
        #         or not i.location.subcategory
        #     ):
        #         continue
        #     self.exported.append(i)
        #     res = set()
        #     try:
        #         for j in i.operationplanresources:
        #             res.add(j.resource.name)
        #     except Exception:
        #         pass
        #     demand_str = json.dumps(i.plan["pegging"]) if i.plan["pegging"] else ""
        #     if i.operation.category == "subcontractor":
        #         yield '<operationplan ordertype="PO" id=%s item=%s location=%s supplier=%s start="%s" end="%s" quantity="%s" location_id=%s item_id=%s criticality="%d" batch=%s/>' % (
        #             quoteattr(i.reference),
        #             quoteattr(i.item.name),
        #             quoteattr(i.location.name),
        #             quoteattr(i.operation.subcategory or ""),
        #             i.startdate,
        #             i.enddate,
        #             i.quantity,
        #             quoteattr(i.location.subcategory or ""),
        #             quoteattr(i.item.subcategory or ""),
        #             int(i.criticality),
        #             quoteattr(i.batch or ""),
        #         )
        #     else:
        #         yield '<operationplan reference=%s ordertype="MO" item=%s location=%s operation=%s start="%s" end="%s" quantity="%s" location_id=%s item_id=%s criticality="%d" resource=%s demand=%s batch=%s/>' % (
        #             quoteattr(i.reference),
        #             quoteattr(i.operation.item.name),
        #             quoteattr(i.operation.location.name),
        #             quoteattr(i.operation.name),
        #             i.startdate,
        #             i.enddate,
        #             i.quantity,
        #             quoteattr(i.operation.location.subcategory),
        #             quoteattr(i.operation.item.subcategory),
        #             int(i.criticality),
        #             quoteattr(",".join(res)),
        #             quoteattr(demand_str),
        #             quoteattr(i.batch or ""),
        #         )

        # Work orders to export
        # Normally we don't create work orders, but only updates existing work orders.
        # We leave it to odoo to create the workorders for a manufacturing order.
        for i in (
            ManufacturingOrder.objects.using(self.database)
            .filter(
                owner__operation__type="routing",
                operation__source__startswith="odoo",
                owner__item__source__startswith="odoo",
                status__in=("proposed", "approved"),
                startdate__lte=today + timedelta(days=7),
            )
            .order_by("startdate")
            .select_related("operation", "location", "item", "owner")
        ):
            if (
                i.status not in ("proposed", "approved")
                or not i.operation
                or not i.operation.source
                or not i.owner.operation.item
                or not i.operation.source.startswith("odoo")
                or not i.owner.item.subcategory
                or not i.location.subcategory
            ):
                continue
            self.exported.append(i)
            res = set()
            try:
                for j in i.operationplanresources:
                    res.add(j.resource.name)
            except Exception:
                pass
            yield '<operationplan reference=%s owner=%s ordertype="WO" item=%s location=%s operation=%s start="%s" end="%s" quantity="%s" location_id=%s item_id=%s resource=%s batch=%s/>' % (
                quoteattr(i.reference),
                quoteattr(i.owner.reference),
                quoteattr(i.owner.operation.item.name),
                quoteattr(i.operation.location.name),
                quoteattr(i.operation.name),
                i.startdate,
                i.enddate,
                i.quantity,
                quoteattr(i.operation.location.subcategory),
                quoteattr(i.owner.operation.item.subcategory),
                quoteattr(",".join(res)),
                quoteattr(i.batch or ""),
            )

        # Write the footer
        yield "</operationplans>"
        yield "</plan>"
        yield "--%s--\r" % self.boundary
        yield "\r"