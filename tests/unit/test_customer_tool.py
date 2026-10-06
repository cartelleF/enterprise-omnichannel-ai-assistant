from unittest.mock import MagicMock, patch

from src.tools.customer_tool import get_customer


@patch("src.tools.customer_tool.col")
def test_get_customer_found(mock_col):
    spark = MagicMock()

    mock_column = MagicMock()
    mock_col.return_value = mock_column
    mock_column.__eq__.return_value = MagicMock()

    row = MagicMock()
    row.asDict.return_value = {
        "customer_id": "CUST-1019",
        "loyalty_level": "SILVER",
        "open_tickets": 2
    }

    df = spark.table.return_value
    df.filter.return_value = df
    df.limit.return_value = df
    df.collect.return_value = [row]

    result = get_customer(
        spark,
        "catalog.gold.customer_360",
        "CUST-1019"
    )

    assert result["found"] is True
    assert result["data"]["customer_id"] == "CUST-1019"
    assert result["data"]["loyalty_level"] == "SILVER"

    spark.table.assert_called_once_with(
        "catalog.gold.customer_360"
    )

    mock_col.assert_called_once_with("customer_id")


@patch("src.tools.customer_tool.col")
def test_get_customer_not_found(mock_col):
    spark = MagicMock()

    mock_column = MagicMock()
    mock_col.return_value = mock_column
    mock_column.__eq__.return_value = MagicMock()

    df = spark.table.return_value
    df.filter.return_value = df
    df.limit.return_value = df
    df.collect.return_value = []

    result = get_customer(
        spark,
        "catalog.gold.customer_360",
        "CUST-999999"
    )

    assert result == {
        "found": False,
        "customer_id": "CUST-999999"
    }

    mock_col.assert_called_once_with("customer_id")
