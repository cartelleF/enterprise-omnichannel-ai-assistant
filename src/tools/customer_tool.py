"""
Customer tool for the Enterprise Omni-Channel AI Assistant.

Provides structured access to customer information stored
in the Gold customer_360 table.
"""

from pyspark.sql.functions import col


def get_customer(spark, table_name, customer_id):
    """
    Retrieve one customer from the Gold customer_360 table.

    Parameters
    ----------
    spark:
        Active SparkSession.

    table_name : str
        Fully qualified Unity Catalog table name.

    customer_id : str
        Enterprise customer identifier.

    Returns
    -------
    dict
        Customer information and lookup status.
    """

    df = (
        spark.table(table_name)
        .filter(col("customer_id") == customer_id)
        .limit(1)
    )

    rows = df.collect()

    if not rows:
        return {
            "found": False,
            "customer_id": customer_id
        }

    return {
        "found": True,
        "data": rows[0].asDict(recursive=True)
    }
