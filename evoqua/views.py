#
# This code was developed by frePPLe bv for Evoqua.
#
# Evoqua has full copyright and intellectual property rights.
# FrePPLe reserves the rights to apply the techniques and
# reuse the code for other implementations.
#

import json

from django.db import connections, transaction
from django.db.models import Exists, OuterRef
from django.db.models.expressions import RawSQL
from django.utils.translation import gettext_lazy as _

from freppledb.common.report import (
    GridFieldLastModified,
    GridPivot,
    GridFieldText,
    GridFieldJSON,
)
from freppledb.input.models import ManufacturingOrder, OperationResource


class OverviewDemandProgressReport(GridPivot):
    """
    A report showing the progress of each manufacturing order
    """

    title = _("Demand progress")
    template = "evoqua/demand_progress.html"
    basequeryset = (
        ManufacturingOrder.objects.all()
        .filter(operation__type="routing")
        .filter(status__in=("confirmed", "approved", "proposed"))
        .filter(
            Exists(
                ManufacturingOrder.objects.filter(
                    status__in=("confirmed", "approved", "proposed")
                )
                .filter(owner=OuterRef("reference"))
                .filter(
                    Exists(
                        OperationResource.objects.filter(resource__name__in=["oven","Painting & Oven per sqm 涂层 & 电炉每平方米面积"]).filter(
                            operation__name=OuterRef("operation")
                        )
                    )
                )
            )
        )
        .values("reference", "item")
        .annotate(
            demands=RawSQL(
                """
          select json_agg(json_build_array(value, key))
          from (
            select key, value
            from jsonb_each_text(operationplan.plan->'pegging')
            order by value desc, key desc
            limit 10
            ) peg""",
                [],
            )
        )
    )
    model = ManufacturingOrder
    permissions = (("view_demand_progress_report", "Can view demand progressreport"),)
    rows = (
        GridFieldText(
            "reference",
            title=_("manufacturing order"),
            editable=False,
            field_name="reference",
            formatter="detail",
            extra='"role":"input/manufacturingorder"',
        ),
        GridFieldJSON(
            "demands",
            title=_("demands"),
            editable=False,
            search=True,
            sortable=False,
            formatter="demanddetail",
            extra='"role":"input/demand"',
        ),
        GridFieldText(
            "item",
            title=_("item"),
            editable=False,
            field_name="name",
            formatter="detail",
            extra='"role":"input/item"',
        ),
        GridFieldText("description", title=_("description"), initially_hidden=True),
        GridFieldText("category", title=_("category"), initially_hidden=True),
        GridFieldText("subcategory", title=_("subcategory"), initially_hidden=True),
        GridFieldText(
            "owner",
            title=_("owner"),
            field_name="owner__name",
            formatter="detail",
            extra='"role":"input/item"',
            initially_hidden=True,
        ),
        GridFieldText("source", title=_("source"), initially_hidden=True),
        GridFieldLastModified("lastmodified", initially_hidden=True),
    )
    crosses = (
        ("cycles", {"title": _("cycles")}),
        ("duration", {"title": _("minutes")}),
    )

    @classmethod
    def query(reportclass, request, basequery, sortsql="1 asc"):
        basesql, baseparams = basequery.query.get_compiler(basequery.db).as_sql(
            with_col_aliases=False
        )

        # Execute the query
        query = """
            select
            operationplan.reference,
            item.name item,
            item.description item__description,
            item.category item__category,
            item.subcategory item__subcategory,
            item.owner_id item__owner,
            item.cost item__cost,
            item.source item__source,
            item.lastmodified item__lastmodified,
            d.bucket,
            d.startdate,
            d.enddate,
            sum(case when (workorder.startdate, workorder.enddate) overlaps (d.startdate, d.enddate) then 1 else 0 end),
            round(extract(epoch from sum(greatest(interval '0 day', least(d.enddate,workorder.enddate)-greatest(d.startdate,workorder.startdate)))) / 60),
            cast(operationplan.demands as text)
            from
            (%s) operationplan
            inner join item on item.name = operationplan.item_id
            cross join (
                       select name as bucket, startdate, enddate
                       from common_bucketdetail
                       where bucket_id = %%s and enddate > %%s and startdate < %%s) d
            inner join operationplan workorder on operationplan.reference = workorder.owner_id
			inner join operationresource on workorder.operation_id = operationresource.operation_id
										and operationresource.resource_id in ('oven', 'Painting & Oven per sqm 涂层 & 电炉每平方米面积')
										and workorder.status not in ('closed', 'completed', 'canceled')
            group by
            operationplan.reference,
            item.name,
            item.description,
            item.category,
            item.subcategory,
            item.owner_id,
            item.cost,
            item.source,
            item.lastmodified,
            d.bucket,
            d.startdate,
            d.enddate,
            cast(operationplan.demands as text)
            order by %s, d.startdate
        """ % (
            basesql,
            sortsql,
        )

        # Build the python result
        with transaction.atomic(using=request.database):
            with connections[request.database].chunked_cursor() as cursor_chunked:
                cursor_chunked.execute(
                    query,
                    baseparams
                    + (
                        request.report_bucket,
                        request.report_startdate,
                        request.report_enddate,  # buckets
                    ),
                )

                for row in cursor_chunked:
                    yield {
                        "reference": row[0],
                        "item": row[1],
                        "description": row[2],
                        "category": row[3],
                        "subcategory": row[4],
                        "owner": row[5],
                        "cost": row[6],
                        "source": row[7],
                        "lastmodified": row[8],
                        "bucket": row[9],
                        "startdate": row[10].date(),
                        "enddate": row[11].date(),
                        "cycles": int(row[12]),
                        "duration": row[13],
                        "demands": json.loads(row[14]) if row[14] else {},
                    }
