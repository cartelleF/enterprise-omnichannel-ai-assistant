from src.api.local_demo_service import LocalDemoService


def test_general_warranty_question_does_not_select_arbitrary_product():
    service = LocalDemoService()

    result = service.ask("What is the warranty policy?")

    assert result["route"] == "RAG"
    assert "product" in result["answer"].lower()

    # A general question must not present a specific
    # product warranty as the universal policy.
    assert "Product ID:" not in result["answer"]

    # The assistant should ask for product clarification.
    assert any(
        term in result["answer"].lower()
        for term in ("which product", "product id", "specify the product")
    )


def test_product_specific_warranty_still_works():
    service = LocalDemoService()

    result = service.ask("What is the warranty for PROD-1001?")

    assert result["route"] == "RAG"
    assert result["sources"] == ["PROD-1001_warranty.txt"]
    assert "PROD-1001" in result["answer"]


def test_return_policy_remains_available():
    service = LocalDemoService()

    result = service.ask("What is the return policy?")

    assert result["route"] == "RAG"
    assert "30 days" in result["answer"]
