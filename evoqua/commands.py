#
# This code was developed by frePPLe bv for Evoqua.
#
# Evoqua has full copyright and intellectual property rights.
# FrePPLe reserves the rights to apply the techniques and
# reuse the code for other implementations.
#
import os

from django.db import connections, DEFAULT_DB_ALIAS

from freppledb.common.commands import PlanTaskRegistry, PlanTask


@PlanTaskRegistry.register
class CheckBuckets(PlanTask):
    description = "Evoqua resource type conversion"
    sequence = 107.6

    @classmethod
    def getWeight(cls, **kwargs):
        for i in range(5):
            if ("odoo_read_%s" % i) in os.environ:
                return 0.1
        return -1

    @classmethod
    def run(cls, database=DEFAULT_DB_ALIAS, **kwargs):
        with connections[database].cursor() as cursor:
            # When we read from odoo we get records of type "buckets".
            # But we actually want records of type 'buckets_day'.
            cursor.execute(
                """
                update resource
                set type = 'buckets_day'
                where type = 'buckets'
                """
            )
