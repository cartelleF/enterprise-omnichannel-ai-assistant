from unittest.mock import MagicMock, patch

from src.tools.order_tool import get_order


@patch("src.tools.order_tool.col")
def test_get_order_found(mock_col):
    spark = MagicMock()

    mock_column = MagicMock()
    mock_col.return_value = mock_column
    mock_column.__eq__.return_value = MagicMock()

    row = MagicMock()
    row.asDict.return_value = {
        "order_id": "ORD-10066",
        "customer_id": "CUST-1019",
        "order_status": "DELIVERED",
        "total_amount": 150.0
    }

    df = spark.table.return_value
    df.filter.return_value = df
    df.limit.return_value = df
    df.collect.return_value = [row]

    result = get_order(
        spark,
        "catalog.gold.order_360",
        "ORD-10066"
    )

    assert result["found"] is True
    assert result["data"]["order_id"] == "ORD-10066"
    assert result["data"]["order_status"] == "DELIVERED"

    spark.table.assert_called_once_with(
        "catalog.gold.order_360"
    )

    mock_col.assert_called_once_with("order_id")


@patch("src.tools.order_tool.col")
def test_get_order_not_found(mock_col):
    spark = MagicMock()

    mock_column = MagicMock()
    mock_col.return_value = mock_column
    mock_column.__eq__.return_value = MagicMock()

    df = spark.table.return_value
    df.filter.return_value = df
    df.limit.return_value = df
    df.collect.return_value = []

    result = get_order(
        spark,
        "catalog.gold.order_360",
        "ORD-999999"
    )

    assert result == {
        "found": False,
        "order_id": "ORD-999999"
    }

    mock_col.assert_called_once_with("order_id")
