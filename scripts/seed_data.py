"""Seed database with mock users and transactions."""
import sys
import os
from decimal import Decimal
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import SessionLocal, engine
from src.models import Base, User, Transaction, TransactionStatus, TransactionCategory
from src.config import settings


# Mock user data
MOCK_USERS = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "email": "alice@example.com",
        "full_name": "Alice Johnson",
        "balance": Decimal("1500.00")
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "email": "bob@example.com",
        "full_name": "Bob Smith",
        "balance": Decimal("2000.00")
    },
    {
        "id": "33333333-3333-3333-3333-333333333333",
        "email": "charlie@example.com",
        "full_name": "Charlie Brown",
        "balance": Decimal("750.00")
    },
    {
        "id": "44444444-4444-4444-4444-444444444444",
        "email": "diana@example.com",
        "full_name": "Diana Prince",
        "balance": Decimal("3200.00")
    },
    {
        "id": "55555555-5555-5555-5555-555555555555",
        "email": "eve@example.com",
        "full_name": "Eve Martinez",
        "balance": Decimal("900.00")
    },
    {
        "id": "66666666-6666-6666-6666-666666666666",
        "email": "frank@example.com",
        "full_name": "Frank Wilson",
        "balance": Decimal("1100.00")
    },
    {
        "id": "77777777-7777-7777-7777-777777777777",
        "email": "grace@example.com",
        "full_name": "Grace Lee",
        "balance": Decimal("2500.00")
    },
    {
        "id": "88888888-8888-8888-8888-888888888888",
        "email": "henry@example.com",
        "full_name": "Henry Davis",
        "balance": Decimal("1800.00")
    },
]

# Transaction descriptions
DESCRIPTIONS = [
    "Lunch at cafe",
    "Movie tickets",
    "Grocery shopping",
    "Gas money",
    "Birthday gift",
    "Dinner split",
    "Rent payment",
    "Book purchase",
    "Coffee",
    "Concert tickets",
    "Taxi fare",
    "Pizza night",
    "Gym membership",
    "Phone bill",
    "Internet bill",
    None,  # Some transactions without description
]

CATEGORIES = [
    TransactionCategory.TRANSFER,
    TransactionCategory.PAYMENT,
    TransactionCategory.REFUND,
]


def seed_database():
    """Seed the database with mock data."""
    print("Starting database seeding...")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create tables
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Check if data already exists
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"Database already contains {existing_users} users. Skipping seed.")
            return
        
        # Create users
        print(f"Creating {len(MOCK_USERS)} mock users...")
        users = []
        for user_data in MOCK_USERS:
            user = User(**user_data)
            db.add(user)
            users.append(user)
        
        db.commit()
        print(f"✓ Created {len(users)} users")
        
        # Create transactions
        print("Creating mock transactions...")
        transactions = []
        
        # Generate 30-40 transactions over the last 30 days
        num_transactions = random.randint(30, 40)
        
        for i in range(num_transactions):
            # Random sender and receiver (must be different)
            sender = random.choice(users)
            receiver = random.choice([u for u in users if u.id != sender.id])
            
            # Random amount between $5 and $500
            amount = Decimal(str(round(random.uniform(5.0, 500.0), 2)))
            
            # Random date in the last 30 days
            days_ago = random.randint(0, 30)
            created_at = datetime.utcnow() - timedelta(days=days_ago)
            
            # Random description and category
            description = random.choice(DESCRIPTIONS)
            category = random.choice(CATEGORIES)
            
            # Most transactions are completed
            status = TransactionStatus.COMPLETED if random.random() < 0.95 else TransactionStatus.PENDING
            
            transaction = Transaction(
                from_user_id=sender.id,
                to_user_id=receiver.id,
                amount=amount,
                description=description,
                status=status,
                category=category,
                created_at=created_at
            )
            db.add(transaction)
            transactions.append(transaction)
        
        db.commit()
        print(f"✓ Created {len(transactions)} transactions")
        
        # Print summary
        print("\n" + "="*60)
        print("SEED DATA SUMMARY")
        print("="*60)
        print(f"\nMock Users ({len(users)}):")
        print("-" * 60)
        for user in users:
            print(f"  {user.email:30} | Balance: ${user.balance:8.2f}")
        
        print(f"\nTransactions: {len(transactions)} created")
        print("\nYou can use these emails to login (with any password in Supabase):")
        for user in users:
            print(f"  - {user.email}")
        
        print("\n" + "="*60)
        print("✓ Database seeding completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Error during seeding: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

