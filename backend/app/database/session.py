from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.transaction import Base

def setup_database(url):
    engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 15}, **({"poolclass": StaticPool} if url.endswith(":memory:") else {}))
    @event.listens_for(engine, "connect")
    def configure(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(engine, expire_on_commit=False)
