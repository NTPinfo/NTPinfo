from server.app.db_config import init_engine
from server.app.models.Base import Base

from server.app.models.Time import Time
from server.app.models.Measurement import Measurement

engine = init_engine()
Base.metadata.create_all(bind=engine)
print("Tables created.")
