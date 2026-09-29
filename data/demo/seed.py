"""Deterministic demo data generator - creates 10,000+ realistic business records."""

import random
from datetime import datetime, date, timedelta
from packages.database.connection import get_db_session, init_db
from packages.database.models import (
    Customer, Product, Salesperson, Order, Transaction, Campaign,
    User, DataSource, KnowledgeDocument,
)
from packages.security.password import hash_password

# Deterministic seed
SEED = 42

REGIONS = ["North", "South", "East", "West"]
SEGMENTS = ["Enterprise", "Mid-Market", "Small Business", "Startup"]
INDUSTRIES = [
    "Technology", "Healthcare", "Finance", "Manufacturing",
    "Retail", "Education", "Energy", "Transportation",
]
PRODUCT_CATEGORIES = ["Software", "Hardware", "Services", "Support", "Consulting"]
TEAMS = ["Alpha", "Beta", "Gamma", "Delta"]
PAYMENT_METHODS = ["credit_card", "bank_transfer", "check", "wire"]
ORDER_STATUSES = ["pending", "confirmed", "shipped", "delivered", "cancelled", "returned"]

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Lisa", "Daniel", "Nancy",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Andrew", "Emily", "Paul", "Donna", "Joshua", "Michelle",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
]

COMPANY_SUFFIXES = ["Inc", "Corp", "LLC", "Group", "Solutions", "Technologies", "Systems", "Partners"]

PRODUCT_NAMES = {
    "Software": ["DataFlow Pro", "CloudSync Enterprise", "Analytics Suite", "SecureVault", "DevOps Platform"],
    "Hardware": ["ServerMax 3000", "NetSwitch Pro", "StorageArray X1", "EdgeNode Mini", "RackMount Elite"],
    "Services": ["Implementation Package", "Migration Service", "Custom Integration", "Training Program", "Managed Hosting"],
    "Support": ["Premium Support", "Standard Support", "Emergency Response", "Dedicated Engineer", "SLA Plus"],
    "Consulting": ["Strategy Workshop", "Architecture Review", "Security Audit", "Performance Tuning", "Digital Transformation"],
}

CAMPAIGN_NAMES = [
    "Q1 Enterprise Push", "Spring Mid-Market Blitz", "Summer Startup Special",
    "Fall Product Launch", "Year-End Closing", "Digital Transformation Week",
    "Cloud Migration Campaign", "Security Awareness Drive", "Partner Channel Boost",
    "Industry Summit Followup", "Webinar Series", "Trade Show Promotion",
]


def generate_demo_data():
    """Generate all demo data with deterministic seed."""
    rng = random.Random(SEED)

    init_db()

    with get_db_session() as db:
        # Check if data already exists
        if db.query(Customer).count() > 0:
            print("Demo data already exists, skipping generation.")
            return

        # ── Users ──────────────────────────────────────
        users = [
            User(
                email="admin@example.local",
                name="Admin User",
                password_hash=hash_password("admin123"),
                role="admin",
            ),
            User(
                email="analyst@example.local",
                name="Data Analyst",
                password_hash=hash_password("analyst123"),
                role="analyst",
            ),
            User(
                email="manager@example.local",
                name="Sales Manager",
                password_hash=hash_password("manager123"),
                role="manager",
            ),
            User(
                email="employee@example.local",
                name="Sales Rep",
                password_hash=hash_password("employee123"),
                role="employee",
            ),
        ]
        db.add_all(users)
        db.flush()
        print(f"Created {len(users)} demo users")

        # ── Products ───────────────────────────────────
        products = []
        pid = 1
        for category, names in PRODUCT_NAMES.items():
            for name in names:
                base_price = rng.uniform(50, 5000)
                products.append(Product(
                    product_id=pid,
                    product_name=name,
                    category=category,
                    unit_price=round(base_price, 2),
                    cost=round(base_price * rng.uniform(0.3, 0.7), 2),
                ))
                pid += 1
        db.add_all(products)
        db.flush()
        print(f"Created {len(products)} products")

        # ── Salespeople ────────────────────────────────
        salespeople = []
        for sid in range(1, 41):
            salespeople.append(Salesperson(
                salesperson_id=sid,
                name=f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
                region=REGIONS[(sid - 1) % 4],
                team=TEAMS[(sid - 1) % 4],
                salary=round(rng.uniform(60000, 150000), 2),
            ))
        db.add_all(salespeople)
        db.flush()
        print(f"Created {len(salespeople)} salespeople")

        # ── Customers ─────────────────────────────────
        customers = []
        start_date = date(2023, 1, 1)
        for cid in range(1, 501):
            region = rng.choice(REGIONS)
            # Bias South region to have more enterprise customers for demo narrative
            if region == "South":
                segment = rng.choices(SEGMENTS, weights=[50, 25, 15, 10])[0]
            else:
                segment = rng.choices(SEGMENTS, weights=[25, 30, 30, 15])[0]

            created = start_date + timedelta(days=rng.randint(0, 600))
            company = f"{rng.choice(FIRST_NAMES)}{rng.choice(LAST_NAMES)} {rng.choice(COMPANY_SUFFIXES)}"
            customers.append(Customer(
                customer_id=cid,
                customer_name=company,
                region=region,
                segment=segment,
                industry=rng.choice(INDUSTRIES),
                email=f"contact{cid}@{company.lower().replace(' ', '')}.com",
                phone=f"+1-{rng.randint(200,999)}-{rng.randint(100,999)}-{rng.randint(1000,9999)}",
                created_at=datetime.combine(created, datetime.min.time()),
                status=rng.choices(["active", "inactive", "churned"], weights=[75, 15, 10])[0],
            ))
        db.add_all(customers)
        db.flush()
        print(f"Created {len(customers)} customers")

        # ── Orders & Transactions ──────────────────────
        orders = []
        transactions = []
        oid = 1
        tid = 1

        # Generate orders spanning 2023-01 to 2026-09
        order_start = date(2023, 1, 1)
        order_end = date(2026, 9, 15)
        total_days = (order_end - order_start).days

        for _ in range(4000):
            customer = rng.choice(customers)
            product = rng.choice(products)
            sp_region_candidates = [s for s in salespeople if s.region == customer.region]
            salesperson = rng.choice(sp_region_candidates) if sp_region_candidates else rng.choice(salespeople)

            order_date = order_start + timedelta(days=rng.randint(0, total_days))

            # South region gets higher quantities for enterprise customers
            if customer.region == "South" and customer.segment == "Enterprise":
                qty = rng.randint(5, 50)
                discount = rng.uniform(0, 0.15)
            else:
                qty = rng.randint(1, 25)
                discount = rng.uniform(0, 0.25)

            status = rng.choices(
                ORDER_STATUSES,
                weights=[5, 10, 10, 60, 10, 5],
            )[0]

            order = Order(
                order_id=oid,
                customer_id=customer.customer_id,
                product_id=product.product_id,
                salesperson_id=salesperson.salesperson_id,
                order_date=order_date,
                quantity=qty,
                unit_price=product.unit_price,
                discount=round(discount, 3),
                status=status,
            )
            orders.append(order)

            # Create transaction for completed orders
            if status in ("delivered", "shipped", "confirmed"):
                revenue = round(qty * product.unit_price * (1 - discount), 2)
                cost = round(qty * product.cost, 2)
                profit = round(revenue - cost, 2)

                txn = Transaction(
                    transaction_id=tid,
                    order_id=oid,
                    transaction_date=order_date + timedelta(days=rng.randint(0, 14)),
                    revenue=revenue,
                    cost=cost,
                    profit=profit,
                    payment_method=rng.choice(PAYMENT_METHODS),
                )
                transactions.append(txn)
                tid += 1

            oid += 1

        db.add_all(orders)
        db.flush()
        db.add_all(transactions)
        db.flush()
        print(f"Created {len(orders)} orders and {len(transactions)} transactions")

        # ── Campaigns ─────────────────────────────────
        campaigns = []
        for i, name in enumerate(CAMPAIGN_NAMES):
            quarter_start = date(2024, ((i % 4) * 3) + 1, 1)
            campaigns.append(Campaign(
                campaign_id=i + 1,
                campaign_name=name,
                start_date=quarter_start,
                end_date=quarter_start + timedelta(days=rng.randint(14, 60)),
                region=REGIONS[i % 4],
                segment=SEGMENTS[i % 4],
                spend=round(rng.uniform(5000, 100000), 2),
            ))
        db.add_all(campaigns)
        db.flush()
        print(f"Created {len(campaigns)} campaigns")

        # ── Data Source ────────────────────────────────
        ds = DataSource(
            name="Business Database",
            source_type="sqlite",
            status="active",
            record_count=len(orders) + len(transactions) + len(customers),
            table_count=6,
            last_sync=datetime.utcnow(),
        )
        db.add(ds)

        # ── Knowledge Documents ────────────────────────
        knowledge_docs = _create_knowledge_documents()
        db.add_all(knowledge_docs)
        db.flush()
        print(f"Created {len(knowledge_docs)} knowledge documents")

        db.commit()
        print("\n[SUCCESS] Demo data generation complete!")
        print(f"  Customers: {len(customers)}")
        print(f"  Products: {len(products)}")
        print(f"  Salespeople: {len(salespeople)}")
        print(f"  Orders: {len(orders)}")
        print(f"  Transactions: {len(transactions)}")
        print(f"  Campaigns: {len(campaigns)}")
        print(f"  Knowledge docs: {len(knowledge_docs)}")
        total = len(customers) + len(products) + len(salespeople) + len(orders) + len(transactions) + len(campaigns)
        print(f"  Total records: {total}")


def _create_knowledge_documents() -> list[KnowledgeDocument]:
    """Create business knowledge documents for RAG."""
    docs = []

    # Table descriptions
    table_docs = [
        ("Customers Table", "The customers table stores information about all business customers. Each customer belongs to a region (North, South, East, West) and a segment (Enterprise, Mid-Market, Small Business, Startup). Customers have a status that can be active, inactive, or churned.", "schema", "sales", "customers"),
        ("Orders Table", "The orders table records all sales orders. Each order links a customer to a product via a salesperson. Orders have a status lifecycle: pending → confirmed → shipped → delivered. Orders can also be cancelled or returned.", "schema", "sales", "orders"),
        ("Transactions Table", "The transactions table records financial transactions associated with completed orders. Each transaction includes revenue, cost, and profit figures. Revenue represents recognized revenue from completed transactions.", "schema", "finance", "transactions"),
        ("Products Table", "The products table contains the product catalog. Products belong to categories: Software, Hardware, Services, Support, and Consulting. Each product has a unit_price (sell price) and cost (acquisition/production cost).", "schema", "products", "products"),
        ("Salespeople Table", "The salespeople table stores sales team members. Each salesperson is assigned to a region and a team (Alpha, Beta, Gamma, Delta).", "schema", "sales", "salespeople"),
        ("Campaigns Table", "The campaigns table tracks marketing campaigns. Each campaign targets a specific region and customer segment, with a defined spend budget and date range.", "schema", "marketing", "campaigns"),
    ]
    for title, content, cat, domain, table in table_docs:
        docs.append(KnowledgeDocument(title=title, content=content, category=cat, business_domain=domain, table_name=table))

    # Column definitions
    col_docs = [
        ("Revenue Column", "revenue: Total recognized revenue associated with completed transactions. Calculated as quantity × unit_price × (1 - discount). Only transactions from delivered, shipped, or confirmed orders generate revenue.", "column_definition", "finance", "transactions", "revenue"),
        ("Profit Column", "profit: Net profit calculated as revenue minus cost. Profit = revenue - (quantity × product_cost).", "column_definition", "finance", "transactions", "profit"),
        ("Cost Column", "cost: Total cost of goods sold for a transaction. Calculated as quantity × product_cost.", "column_definition", "finance", "transactions", "cost"),
        ("Region Column", "region: Geographic sales region. Values: North, South, East, West. Used across customers, salespeople, and campaigns tables.", "column_definition", "sales", "customers", "region"),
        ("Segment Column", "segment: Customer market segment classification. Values: Enterprise, Mid-Market, Small Business, Startup. Enterprise customers typically have larger order volumes.", "column_definition", "sales", "customers", "segment"),
        ("Discount Column", "discount: Percentage discount applied to order. Stored as decimal (e.g., 0.15 = 15%). Applied to unit_price when calculating revenue.", "column_definition", "sales", "orders", "discount"),
    ]
    for title, content, cat, domain, table, col in col_docs:
        docs.append(KnowledgeDocument(title=title, content=content, category=cat, business_domain=domain, table_name=table, column_name=col))

    # Business rules
    rules = [
        ("Active Customer Definition", "active_customer: A customer with status='active' who has at least one completed purchase (order with status='delivered') during the previous 90 days.", "business_rule", "sales"),
        ("Revenue Recognition", "Revenue is recognized when an order reaches 'confirmed', 'shipped', or 'delivered' status. Cancelled and returned orders do not generate recognized revenue.", "business_rule", "finance"),
        ("Fiscal Calendar", "The fiscal year follows the calendar year (January-December). Q1=Jan-Mar, Q2=Apr-Jun, Q3=Jul-Sep, Q4=Oct-Dec. 'Last quarter' refers to the most recent completed quarter.", "business_rule", "finance"),
        ("Customer Churn Definition", "A customer is considered churned if they have had no orders in the past 180 days and their status is set to 'churned'.", "business_rule", "sales"),
    ]
    for title, content, cat, domain in rules:
        docs.append(KnowledgeDocument(title=title, content=content, category=cat, business_domain=domain))

    # KPIs
    kpis = [
        ("Gross Margin KPI", "gross_margin: (revenue - cost) / revenue. Expressed as percentage. Measures profitability before operating expenses. Healthy range: 40-70% depending on product category.", "kpi", "finance"),
        ("Average Order Value KPI", "average_order_value (AOV): Total revenue / Number of orders. Indicates typical transaction size. Tracked monthly and by segment.", "kpi", "sales"),
        ("Customer Acquisition Cost", "customer_acquisition_cost (CAC): Total campaign spend / Number of new customers acquired during campaign period. Lower CAC indicates more efficient marketing.", "kpi", "marketing"),
        ("Revenue Per Region", "revenue_per_region: SUM(revenue) grouped by customer region. Primary metric for regional performance comparison.", "kpi", "sales"),
    ]
    for title, content, cat, domain in kpis:
        docs.append(KnowledgeDocument(title=title, content=content, category=cat, business_domain=domain))

    # Relationships
    rels = [
        ("Orders-Customers Relationship", "orders.customer_id → customers.customer_id: Each order belongs to exactly one customer. A customer can have many orders. Join orders with customers to analyze sales by customer attributes (region, segment, industry).", "relationship", "sales"),
        ("Orders-Products Relationship", "orders.product_id → products.product_id: Each order is for exactly one product. A product can appear in many orders. Join to analyze sales by product category.", "relationship", "sales"),
        ("Transactions-Orders Relationship", "transactions.order_id → orders.order_id: Each transaction is linked to one order. Not all orders have transactions (only completed orders). Join transactions with orders to connect financial data with order details.", "relationship", "finance"),
        ("Orders-Salespeople Relationship", "orders.salesperson_id → salespeople.salesperson_id: Each order is handled by one salesperson. Join to analyze salesperson performance.", "relationship", "sales"),
    ]
    for title, content, cat, domain in rels:
        docs.append(KnowledgeDocument(title=title, content=content, category=cat, business_domain=domain))

    # Glossary
    glossary = [
        ("Quarter Definition", "A quarter is a three-month fiscal period. Q1=January-March, Q2=April-June, Q3=July-September, Q4=October-December. 'Last quarter' means the most recently completed quarter relative to today's date.", "glossary", "finance"),
        ("Year-over-Year", "Year-over-Year (YoY): Comparison of a metric's value in the current period versus the same period in the previous year. Example: Q3 2026 revenue compared to Q3 2025 revenue.", "glossary", "finance"),
        ("Pipeline", "Sales pipeline: All orders in pending or confirmed status that have not yet been delivered, cancelled, or returned.", "glossary", "sales"),
        ("Churn Rate", "churn_rate: Number of customers who became churned in a period / Total active customers at start of period. Expressed as percentage.", "glossary", "sales"),
    ]
    for title, content, cat, domain in glossary:
        docs.append(KnowledgeDocument(title=title, content=content, category=cat, business_domain=domain))

    # Examples
    examples = [
        ("Revenue by Region Query Example", "To find revenue by region: SELECT c.region, SUM(t.revenue) as total_revenue FROM transactions t JOIN orders o ON t.order_id = o.order_id JOIN customers c ON o.customer_id = c.customer_id GROUP BY c.region ORDER BY total_revenue DESC", "example", "sales"),
        ("Top Customers Query Example", "To find top customers by revenue: SELECT c.customer_name, c.segment, SUM(t.revenue) as total_revenue FROM transactions t JOIN orders o ON t.order_id = o.order_id JOIN customers c ON o.customer_id = c.customer_id GROUP BY c.customer_id, c.customer_name, c.segment ORDER BY total_revenue DESC LIMIT 10", "example", "sales"),
        ("Monthly Revenue Trend Example", "To see monthly revenue trend: SELECT strftime('%Y-%m', t.transaction_date) as month, SUM(t.revenue) as revenue FROM transactions t GROUP BY month ORDER BY month", "example", "finance"),
    ]
    for title, content, cat, domain in examples:
        docs.append(KnowledgeDocument(title=title, content=content, category=cat, business_domain=domain))

    return docs


if __name__ == "__main__":
    generate_demo_data()
