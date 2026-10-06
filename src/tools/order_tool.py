"""
Order tool for the Enterprise Omni-Channel AI Assistant.

Provides structured access to order information stored
in the Gold order_360 table.
"""

from pyspark.sql.functions import col


def get_order(spark, table_name, order_id):
    """
    Retrieve one order from the Gold order_360 table.

    Parameters
    ----------
    spark:
        Active SparkSession.

    table_name : str
        Fully qualified Unity Catalog table name.

    order_id : str
        Enterprise order identifier.

    Returns
    -------
    dict
        {
            "found": bool,
            "data": {...}
        }

        or, when the order does not exist:

        {
            "found": False,
            "order_id": "..."
        }
    """

    df = (
        spark.table(table_name)
        .filter(col("order_id") == order_id)
        .limit(1)
    )

    rows = df.collect()

    if not rows:
        return {
            "found": False,
            "order_id": order_id
        }

    return {
        "found": True,
        "data": rows[0].asDict(recursive=True)
    }
