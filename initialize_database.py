import os
import sys

# Add project root to path to allow imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from backend.core.database import Base, engine, SQLALCHEMY_DATABASE_URL
from backend.core import models # Import all models to register them with Base

def main():
    """
    Initializes the database.
    1. Deletes the old database file if it exists.
    2. Creates all tables based on the current models.
    """
    db_file = SQLALCHEMY_DATABASE_URL.split("///")[1]
    
    if os.path.exists(db_file):
        print(f"Found old database file at '{db_file}'. Deleting it...")
        os.remove(db_file)
        print("Old database file deleted.")
    else:
        print("No old database file found. Proceeding to create a new one.")

    print("Creating new database and tables based on current models...")
    # This command connects to the database engine and creates all tables
    # that inherit from the 'Base' class in our models.
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")

if __name__ == "__main__":
    main()