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
from freppledb.input.views.utils import (
    PathReport as stdPathReport,
    UpstreamItemPath as stdUpstreamItemPath,
    DownstreamItemPath as stdDownstreamItemPath,
    UpstreamBufferPath as stdUpstreamBufferPath,
    DownstreamBufferPath as stdDownstreamBufferPath,
    UpstreamResourcePath as stdUpstreamResourcePath,
    UpstreamDemandPath as stdUpstreamDemandPath,
    DownstreamResourcePath as stdDownstreamResourcePath,
    UpstreamOperationPath as stdUpstreamOperationPath,
    DownstreamOperationPath as stdDownstreamOperationPath,
)


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
class PathReport(stdPathReport):
    @classmethod
    def getOperationFromBuffer(
        reportclass,
        request,
        buffer_name,
        downstream,
        depth,
        previousOperation,
        bom_quantity,
    ):
        cursor = connections[request.database].cursor()
        item = buffer_name[0 : buffer_name.find(" @ ")]
        location = buffer_name[buffer_name.find(" @ ") + 3 :]
        query = """
      -- MANUFACTURING OPERATIONS
      select distinct
      case when parentoperation is null then operation else sibling end,
      case when parentoperation is null then operation_location else sibling_location end,
      case when parentoperation is null then operation_type else sibling_type end,
      case when parentoperation is null then operation_priority else sibling_priority end,
      case when parentoperation is null then operation_om else sibling_om end,
      case when parentoperation is null then operation_or else sibling_or end,
      case when parentoperation is null then operation_duration else sibling_duration end,
      case when parentoperation is null then operation_duration_per else sibling_duration_per end,
      parentoperation,
      parentoperation_type,
      parentoperation_priority,
      grandparentoperation,
      grandparentoperation_type,
      grandparentoperation_priority,
      sizes,
      grandparentitem_name,
      parentitem_name,
      item_name,
      grandparentitem_description,
      parentitem_description,
      item_description
       from
      (
      select operation.name as operation,
           operation.type operation_type,
           operation.location_id operation_location,
           operation.priority as operation_priority,
           operation.duration as operation_duration,
           operation.duration_per as operation_duration_per,
           case when operation.item_id is not null then jsonb_build_object(operation.item_id||' @ '||operation.location_id, 1) else '{}'::jsonb end
           ||jsonb_object_agg(operationmaterial.item_id||' @ '||operation.location_id,
                              coalesce(operationmaterial.quantity, operationmaterial.quantity_fixed, 0)) filter (where operationmaterial.id is not null) as operation_om,
           jsonb_object_agg(operationresource.resource_id, operationresource.quantity) filter (where operationresource.id is not null) as operation_or,
             parentoperation.name as parentoperation,
           parentoperation.type as parentoperation_type,
           parentoperation.priority parentoperation_priority,
             sibling.name as sibling,
           sibling.type as sibling_type,
           sibling.location_id as sibling_location,
           sibling.priority as sibling_priority,
           sibling.duration as sibling_duration,
           sibling.duration_per as sibling_duration_per,
           case when grandparentoperation.item_id is not null
           and sibling.priority = (select max(priority) from operation where owner_id = parentoperation.name)
           then jsonb_build_object(grandparentoperation.item_id||' @ '||grandparentoperation.location_id, 1) else '{}'::jsonb end
           ||case when parentoperation.item_id is not null
           and sibling.priority = (select max(priority) from operation where owner_id = parentoperation.name)
           then jsonb_build_object(parentoperation.item_id||' @ '||parentoperation.location_id, 1) else '{}'::jsonb end
           ||case when sibling.item_id is not null then jsonb_build_object(sibling.item_id||' @ '||sibling.location_id, 1) else '{}'::jsonb end
           ||coalesce(jsonb_object_agg(siblingoperationmaterial.item_id||' @ '||sibling.location_id,
                                       coalesce(siblingoperationmaterial.quantity, siblingoperationmaterial.quantity_fixed, 0)) filter (where siblingoperationmaterial.id is not null), '{}'::jsonb) as sibling_om,
           jsonb_object_agg(siblingoperationresource.resource_id, siblingoperationresource.quantity)filter (where siblingoperationresource.id is not null) as sibling_or,
             grandparentoperation.name as grandparentoperation,
           grandparentoperation.type as grandparentoperation_type,
           grandparentoperation.priority as grandparentoperation_priority,
           jsonb_build_object( 'operation_min', operation.sizeminimum,
                               'operation_multiple', operation.sizemultiple,
                               'operation_max', operation.sizemaximum,
                               'parentoperation_min', parentoperation.sizeminimum,
                               'parentoperation_multiple',parentoperation.sizemultiple,
                               'parentoperation_max', parentoperation.sizemaximum,
                               'grandparentoperation_min', grandparentoperation.sizeminimum,
                               'grandparentoperation_multiple', grandparentoperation.sizemultiple,
                               'grandparentoperation_max', grandparentoperation.sizemaximum) as sizes,
           grandparentitem.name as grandparentitem_name,
           parentitem.name as parentitem_name,
           item.name as item_name,
           grandparentitem.description as grandparentitem_description,
           parentitem.description as parentitem_description,
           item.description as item_description
      from operation
      left outer join operationmaterial on operationmaterial.operation_id = operation.name
      left outer join operationresource on operationresource.operation_id = operation.name
      left outer join operation parentoperation on parentoperation.name = operation.owner_id
      left outer join operation grandparentoperation on grandparentoperation.name = parentoperation.owner_id
      left outer join operation sibling on sibling.owner_id = parentoperation.name
      left outer join operationmaterial siblingoperationmaterial on siblingoperationmaterial.operation_id = sibling.name
      left outer join operationresource siblingoperationresource on siblingoperationresource.operation_id = sibling.name
      left outer join item grandparentitem on grandparentitem.name = grandparentoperation.item_id
      left outer join item parentitem on parentitem.name = parentoperation.item_id
      left outer join item on item.name = coalesce(operation.item_id,
                                                   (select item_id from operationmaterial where operation_id = operation.name and quantity > 0 limit 1))
      where operation.type in ('time_per','fixed_time')
      and operation.location_id = %%s
      %s
      group by operation.name, parentoperation.name, sibling.name, grandparentoperation.name,
      grandparentitem.name, parentitem.name, item.name, grandparentitem.description, parentitem.description, item.description
      ) t
      union all
      -- DISTRIBUTION OPERATIONS
      select 'Ship '||item.name||' from '||itemdistribution.origin_id||' to '||itemdistribution.location_id,
      itemdistribution.location_id,
      'distribution' as type,
      itemdistribution.priority,
      jsonb_build_object(item.name||' @ '||itemdistribution.origin_id, -1,
                         item.name||' @ '||itemdistribution.location_id, 1) as operation_om,
      case when itemdistribution.resource_id is not null
      then jsonb_build_object(itemdistribution.resource_id, itemdistribution.resource_qty)
      else '{}'::jsonb end operation_or,
      leadtime as duration,
      null as duration_per,
      null,
      null,
      null,
      null,
      null,
      null,
      jsonb_build_object( 'operation_min', itemdistribution.sizeminimum,
                               'operation_multiple', itemdistribution.sizemultiple,
                               'operation_max', itemdistribution.sizemaximum) as sizes,
      null,
      null,
      item.name,
      null,
      null,
      item.description
      from itemdistribution
      inner join item parent on parent.name = itemdistribution.item_id
      inner join item on item.name = %%s and item.lft between parent.lft and parent.rght
      where itemdistribution.%s = %%s
      """ % (
            (
                """
                and (operation.item_id = %s
                or parentoperation.item_id = %s
                or grandparentoperation.item_id = %s)
                """,
                "location_id",
            )
            if not downstream
            else (
                """
                and exists (select 1 from operationmaterial om where om.operation_id = operation.name
                and om.item_id = %s and om.quantity < 0)
                """,
                "origin_id",
            )
        )
        if not downstream:
            query = (
                query
                + """
        union all
      -- PURCHASING OPERATIONS
      select 'Purchase '||item.name||' @ '|| location.name||' from '||itemsupplier.supplier_id,
      location.name as location_id,
      'purchase' as type,
      itemsupplier.priority,
      jsonb_build_object(item.name||' @ '|| location.name,1),
      case when itemsupplier.resource_id is not null then jsonb_build_object(itemsupplier.resource_id, itemsupplier.resource_qty) else '{}'::jsonb end resources,
      itemsupplier.leadtime as duration,
      null as duration_per,
      null,
      null,
      null,
      null,
      null,
      null,
      jsonb_build_object( 'operation_min', itemsupplier.sizeminimum,
                               'operation_multiple', itemsupplier.sizemultiple,
                               'operation_max', itemsupplier.sizemaximum) as sizes,
      null,
      null,
      item.name,
      null,
      null,
      item.description
      from itemsupplier
      inner join item i_parent on i_parent.name = itemsupplier.item_id
      inner join item on item.name = %s and item.lft between i_parent.lft and i_parent.rght
      inner join location l_parent on l_parent.name = itemsupplier.location_id
      inner join location on location.name = %s and location.lft between l_parent.lft and l_parent.rght
      union all
      select 'Purchase '||item.name||' @ '|| location.name||' from '||itemsupplier.supplier_id,
      location.name as location_id,
      'purchase' as type,
      itemsupplier.priority,
      jsonb_build_object(item.name||' @ '|| location.name,1),
      case when itemsupplier.resource_id is not null then jsonb_build_object(itemsupplier.resource_id, itemsupplier.resource_qty) else '{}'::jsonb end resources,
      itemsupplier.leadtime as duration,
      null as duration_per,
      null,
      null,
      null,
      null,
      null,
      null,
      jsonb_build_object( 'operation_min', itemsupplier.sizeminimum,
                               'operation_multiple', itemsupplier.sizemultiple,
                               'operation_max', itemsupplier.sizemaximum) as sizes,
      null,
      null,
      item.name,
      null,
      null,
      item.description
      from itemsupplier
      inner join item i_parent on i_parent.name = itemsupplier.item_id
      inner join item on item.name = %s and item.lft between i_parent.lft and i_parent.rght
      inner join location on location.name = %s and location.lft = location.rght - 1
      where location_id is null
      """
            )
        query = (
            query + " order by grandparentoperation, parentoperation, sibling_priority"
        )
        if downstream:
            cursor.execute(query, (location, item, item, location))
        else:
            cursor.execute(
                query,
                (
                    location,
                    item,
                    item,
                    item,
                    item,
                    location,
                    item,
                    location,
                    item,
                    location,
                ),
            )
        for i in cursor.fetchall():
            for j in reportclass.processRecord(
                i, request, depth, downstream, previousOperation, bom_quantity
            ):
                yield j
class UpstreamItemPath(stdUpstreamItemPath, PathReport):
    pass
class DownstreamItemPath(stdDownstreamItemPath, PathReport):
    pass
class UpstreamBufferPath(stdUpstreamBufferPath, PathReport):
    pass
class DownstreamBufferPath(stdDownstreamBufferPath, PathReport):
    pass
class UpstreamResourcePath(stdUpstreamResourcePath, PathReport):
    pass
class UpstreamDemandPath(stdUpstreamDemandPath, PathReport):
    pass
class DownstreamResourcePath(stdDownstreamResourcePath, PathReport):
    pass
class UpstreamOperationPath(stdUpstreamOperationPath, PathReport):
    pass
class DownstreamOperationPath(stdDownstreamOperationPath, PathReport):
    pass
