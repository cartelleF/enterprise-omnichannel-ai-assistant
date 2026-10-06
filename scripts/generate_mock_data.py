#!/usr/bin/env python3

"""
Generate coherent mock enterprise data for the
Enterprise Omni-Channel AI Assistant project.

Sources:
    - SAP
    - CRM
    - Documents

Output:
    data/raw/
        sap/
        crm/
        documents/
"""

import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_CUSTOMERS = 100
DEFAULT_PRODUCTS = 30
DEFAULT_ORDERS = 500
DEFAULT_TICKETS = 200
DEFAULT_INTERACTIONS = 500

SEED = 42

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data" / "raw"

SAP_DIR = RAW_DIR / "sap"
CRM_DIR = RAW_DIR / "crm"
DOCUMENTS_DIR = RAW_DIR / "documents"


# ============================================================
# REFERENCE DATA
# ============================================================

FIRST_NAMES = [
    "Thomas", "Anna", "Michael", "Laura",
    "Daniel", "Sophie", "Peter", "Julia",
    "Martin", "Emma", "David", "Sarah",
    "Paul", "Marie", "James", "Claire"
]

LAST_NAMES = [
    "Müller", "Schmidt", "Schneider", "Fischer",
    "Weber", "Meyer", "Wagner", "Becker",
    "Hoffmann", "Klein", "Martin", "Dubois",
    "Smith", "Brown"
]

CITIES = [
    ("Dortmund", "Germany"),
    ("Köln", "Germany"),
    ("Berlin", "Germany"),
    ("Hamburg", "Germany"),
    ("Munich", "Germany"),
    ("Frankfurt", "Germany"),
    ("Paris", "France"),
    ("Lyon", "France"),
    ("London", "United Kingdom")
]

PRODUCT_NAMES = [
    "Smart Home Hub X1",
    "Smart Home Camera C2",
    "Wireless Door Sensor D1",
    "Smart Thermostat T3",
    "Security Starter Kit S1",
    "Home Energy Monitor E2",
    "Smart Light Panel L4",
    "Connected Speaker A1",
    "Smart Plug P2",
    "Indoor Camera C4"
]

PRODUCT_CATEGORIES = [
    "Smart Home",
    "Security",
    "Energy",
    "Lighting",
    "Audio",
    "Accessories"
]

ORDER_STATUSES = [
    "CREATED",
    "PROCESSING",
    "SHIPPED",
    "DELIVERED",
    "DELAYED",
    "CANCELLED"
]

TICKET_SUBJECTS = [
    "Delayed delivery",
    "Payment problem",
    "Product information",
    "Return request",
    "Warranty question",
    "Damaged product",
    "Order cancellation"
]

TICKET_PRIORITIES = [
    "LOW",
    "MEDIUM",
    "HIGH"
]

TICKET_STATUSES = [
    "OPEN",
    "IN_PROGRESS",
    "RESOLVED"
]

CHANNELS = [
    "EMAIL",
    "PHONE",
    "WEB",
    "CHAT"
]

INTERACTION_TYPES = [
    "CUSTOMER_SUPPORT",
    "ORDER_INQUIRY",
    "PRODUCT_INQUIRY",
    "COMPLAINT",
    "GENERAL_INQUIRY"
]


# ============================================================
# HELPERS
# ============================================================

def random_date(
    start=datetime(2026, 1, 1),
    end=datetime(2026, 9, 20)
):
    delta = end - start
    seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=seconds)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )

    print("Created {:>5} records -> {}".format(len(data), path))


def write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        file.write(content)

    print("Created document -> {}".format(path))


# ============================================================
# SAP - CUSTOMERS
# ============================================================

def generate_sap_customers(number):

    customers = []

    for i in range(1, number + 1):

        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        city, country = random.choice(CITIES)

        customer_id = "CUST-{}".format(1000 + i)

        customers.append({
            "customer_id": customer_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": "{}.{}{}@example.com".format(
                first_name.lower(),
                last_name.lower(),
                i
            ),
            "country": country,
            "city": city,
            "customer_segment": random.choice([
                "STANDARD",
                "PREMIUM",
                "BUSINESS"
            ]),
            "created_at": random_date().date().isoformat()
        })

    return customers


# ============================================================
# SAP - PRODUCTS
# ============================================================

def generate_products(number):

    products = []

    for i in range(1, number + 1):

        product_id = "PROD-{}".format(1000 + i)

        products.append({
            "product_id": product_id,
            "product_name": "{} {}".format(
                random.choice(PRODUCT_NAMES),
                i
            ),
            "category": random.choice(PRODUCT_CATEGORIES),
            "description": (
                "Connected enterprise product "
                "for smart home and customer solutions."
            ),
            "price": round(
                random.uniform(29.99, 799.99),
                2
            ),
            "currency": "EUR",
            "stock_quantity": random.randint(0, 500),
            "active": random.choice([
                True, True, True, False
            ])
        })

    return products


# ============================================================
# SAP - ORDERS
# ============================================================

def generate_orders(number, customers):

    orders = []

    for i in range(1, number + 1):

        customer = random.choice(customers)
        order_date = random_date()
        status = random.choice(ORDER_STATUSES)

        if status == "CANCELLED":
            delivery_date = None
        else:
            delivery_date = (
                order_date +
                timedelta(days=random.randint(2, 8))
            ).date().isoformat()

        orders.append({
            "order_id": "ORD-{}".format(10000 + i),
            "customer_id": customer["customer_id"],
            "order_date": order_date.date().isoformat(),
            "status": status,
            "total_amount": 0.0,
            "currency": "EUR",
            "delivery_date": delivery_date
        })

    return orders


# ============================================================
# SAP - ORDER ITEMS
# ============================================================

def generate_order_items(orders, products):

    order_items = []

    order_totals = {}

    for order in orders:
        order_totals[order["order_id"]] = 0.0

    item_id = 1

    for order in orders:

        number_of_items = random.randint(1, 4)

        selected_products = random.sample(
            products,
            min(number_of_items, len(products))
        )

        for product in selected_products:

            quantity = random.randint(1, 3)
            unit_price = product["price"]

            total_price = round(
                quantity * unit_price,
                2
            )

            order_totals[order["order_id"]] += total_price

            order_items.append({
                "order_item_id": "ITEM-{}".format(
                    100000 + item_id
                ),
                "order_id": order["order_id"],
                "product_id": product["product_id"],
                "quantity": quantity,
                "unit_price": unit_price,
                "total_price": total_price,
                "currency": "EUR"
            })

            item_id += 1

    return order_items, order_totals


# ============================================================
# SAP - INVOICES
# ============================================================

def generate_invoices(orders):

    invoices = []

    for i, order in enumerate(orders, start=1):

        if order["status"] == "CANCELLED":
            continue

        invoice_status = random.choice([
            "PAID",
            "PAID",
            "OPEN",
            "OVERDUE"
        ])

        invoices.append({
            "invoice_id": "INV-{}".format(10000 + i),
            "order_id": order["order_id"],
            "customer_id": order["customer_id"],
            "invoice_date": order["order_date"],
            "amount": order["total_amount"],
            "currency": "EUR",
            "status": invoice_status
        })

    return invoices


# ============================================================
# CRM - CUSTOMERS
# ============================================================

def generate_crm_customers(sap_customers):

    crm_customers = []

    for customer in sap_customers:

        crm_customers.append({
            "customer_id": customer["customer_id"],
            "customer_type": random.choice([
                "PRIVATE",
                "BUSINESS"
            ]),
            "preferred_language": random.choice([
                "de",
                "en",
                "fr"
            ]),
            "preferred_channel": random.choice(CHANNELS),
            "loyalty_level": random.choice([
                "STANDARD",
                "SILVER",
                "GOLD"
            ]),
            "marketing_consent": random.choice([
                True,
                True,
                False
            ])
        })

    return crm_customers


# ============================================================
# CRM - TICKETS
# ============================================================

def generate_tickets(number, customers, orders):

    tickets = []

    for i in range(1, number + 1):

        customer = random.choice(customers)

        customer_orders = [
            order for order in orders
            if order["customer_id"] == customer["customer_id"]
        ]

        linked_order = None

        if customer_orders and random.random() < 0.7:
            linked_order = random.choice(customer_orders)

        subject = random.choice(TICKET_SUBJECTS)

        tickets.append({
            "ticket_id": "TICK-{}".format(5000 + i),
            "customer_id": customer["customer_id"],
            "order_id": (
                linked_order["order_id"]
                if linked_order
                else None
            ),
            "subject": subject,
            "description": (
                "Customer reports an issue related to "
                "{}.".format(subject.lower())
            ),
            "priority": random.choice(TICKET_PRIORITIES),
            "status": random.choice(TICKET_STATUSES),
            "created_at": random_date().isoformat()
        })

    return tickets


# ============================================================
# CRM - INTERACTIONS
# ============================================================

def generate_interactions(number, customers, tickets):

    interactions = []

    for i in range(1, number + 1):

        customer = random.choice(customers)

        customer_tickets = [
            ticket for ticket in tickets
            if ticket["customer_id"] == customer["customer_id"]
        ]

        linked_ticket = None

        if customer_tickets and random.random() < 0.5:
            linked_ticket = random.choice(customer_tickets)

        interaction_type = random.choice(
            INTERACTION_TYPES
        )

        interactions.append({
            "interaction_id": "INT-{}".format(
                8000 + i
            ),
            "customer_id": customer["customer_id"],
            "ticket_id": (
                linked_ticket["ticket_id"]
                if linked_ticket
                else None
            ),
            "channel": random.choice(CHANNELS),
            "interaction_type": interaction_type,
            "summary": (
                "Customer interaction concerning {}.".format(
                    interaction_type.lower().replace(
                        "_",
                        " "
                    )
                )
            ),
            "timestamp": random_date().isoformat()
        })

    return interactions


# ============================================================
# DOCUMENTS
# ============================================================

def generate_documents(products):

    faq_dir = DOCUMENTS_DIR / "faq"
    warranty_dir = DOCUMENTS_DIR / "warranty"
    policies_dir = DOCUMENTS_DIR / "policies"

    # FAQ - English

    write_text(
        faq_dir / "delivery_faq_en.txt",
        """
Delivery FAQ

Standard delivery normally takes between 2 and 4 business days.

Customers can check their order status using their order number.

If an order is marked as DELAYED, customer support should verify
the latest logistics information before providing a delivery date.
""".strip()
    )

    # FAQ - German

    write_text(
        faq_dir / "delivery_faq_de.txt",
        """
Lieferungs-FAQ

Die Standardlieferung dauert normalerweise zwischen 2 und 4 Werktagen.

Kunden können den Status ihrer Bestellung anhand ihrer Bestellnummer
überprüfen.

Wenn eine Bestellung als DELAYED markiert ist, sollte der Kundenservice
die aktuellen Logistikdaten prüfen.
""".strip()
    )

    # FAQ - Returns

    write_text(
        faq_dir / "returns_faq_en.txt",
        """
Returns FAQ

Customers may request a return within 30 days after delivery.

The product should normally be returned in good condition.

Some products may have specific return conditions.
""".strip()
    )

    # Warranty documents

    for product in products[:10]:

        product_id = product["product_id"]
        product_name = product["product_name"]

        content = """
Product Warranty

Product ID: {product_id}
Product Name: {product_name}

Warranty period: 24 months.

The warranty covers manufacturing defects under normal usage.

The warranty does not normally cover damage caused by misuse,
accidents or unauthorized modifications.

Customers should provide their order number when submitting
a warranty request.
""".format(
            product_id=product_id,
            product_name=product_name
        ).strip()

        write_text(
            warranty_dir / "{}_warranty.txt".format(product_id),
            content
        )

    # Policies

    write_text(
        policies_dir / "return_policy.txt",
        """
Return Policy

Customers can request a return within 30 days after delivery.

Returned products must normally be in acceptable condition.

The customer service team must verify the original order before
approving a return.

Refunds are processed after the returned product has been inspected.
""".strip()
    )

    write_text(
        policies_dir / "delivery_policy.txt",
        """
Delivery Policy

Standard delivery takes approximately 2 to 4 business days.

Orders may occasionally experience delays because of logistics,
availability or exceptional circumstances.

For delayed orders, customer support should consult the latest
order information before communicating an estimated delivery date.
""".strip()
    )


# ============================================================
# MAIN
# ============================================================

def generate_data(
    customers_count,
    products_count,
    orders_count,
    tickets_count,
    interactions_count
):

    random.seed(SEED)

    print("")
    print("==============================================")
    print("Enterprise Omni-Channel AI Assistant")
    print("Mock Data Generator")
    print("==============================================")
    print("")

    # SAP customers

    sap_customers = generate_sap_customers(
        customers_count
    )

    write_json(
        SAP_DIR / "customers.json",
        sap_customers
    )

    # SAP products

    products = generate_products(
        products_count
    )

    write_json(
        SAP_DIR / "products.json",
        products
    )

    # SAP orders

    orders = generate_orders(
        orders_count,
        sap_customers
    )

    # SAP order items

    order_items, order_totals = generate_order_items(
        orders,
        products
    )

    for order in orders:
        order["total_amount"] = round(
            order_totals[order["order_id"]],
            2
        )

    write_json(
        SAP_DIR / "orders.json",
        orders
    )

    write_json(
        SAP_DIR / "order_items.json",
        order_items
    )

    # SAP invoices

    invoices = generate_invoices(orders)

    write_json(
        SAP_DIR / "invoices.json",
        invoices
    )

    # CRM customers

    crm_customers = generate_crm_customers(
        sap_customers
    )

    write_json(
        CRM_DIR / "customers.json",
        crm_customers
    )

    # CRM tickets

    tickets = generate_tickets(
        tickets_count,
        sap_customers,
        orders
    )

    write_json(
        CRM_DIR / "tickets.json",
        tickets
    )

    # CRM interactions

    interactions = generate_interactions(
        interactions_count,
        sap_customers,
        tickets
    )

    write_json(
        CRM_DIR / "interactions.json",
        interactions
    )

    # Documents

    generate_documents(products)

    print("")
    print("==============================================")
    print("Generation completed successfully.")
    print("Output directory: {}".format(RAW_DIR))
    print("==============================================")
    print("")


# ============================================================
# COMMAND LINE
# ============================================================

def parse_args():

    parser = argparse.ArgumentParser(
        description="Generate mock enterprise data."
    )

    parser.add_argument(
        "--customers",
        type=int,
        default=DEFAULT_CUSTOMERS
    )

    parser.add_argument(
        "--products",
        type=int,
        default=DEFAULT_PRODUCTS
    )

    parser.add_argument(
        "--orders",
        type=int,
        default=DEFAULT_ORDERS
    )

    parser.add_argument(
        "--tickets",
        type=int,
        default=DEFAULT_TICKETS
    )

    parser.add_argument(
        "--interactions",
        type=int,
        default=DEFAULT_INTERACTIONS
    )

    return parser.parse_args()


if __name__ == "__main__":

    args = parse_args()

    generate_data(
        customers_count=args.customers,
        products_count=args.products,
        orders_count=args.orders,
        tickets_count=args.tickets,
        interactions_count=args.interactions
    )
