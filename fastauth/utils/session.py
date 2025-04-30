from typing import Generator
from sqlmodel import Session


def get_session(engine) -> Generator[Session, None, None]:
    """Get a database session from a SQLModel engine.
    
    Args:
        engine: SQLModel engine
        
    Yields:
        Session: A SQLModel session
    """
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
