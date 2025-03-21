from uuid import UUID
from fastapi.encoders import jsonable_encoder as base_jsonable_encoder

def custom_jsonable_encoder(obj):
    """Custom encoder to handle UUID and other non-serializable types."""
    if isinstance(obj, UUID):
        return str(obj)  # Convert UUID to string
    return base_jsonable_encoder(obj)  # Fallback to default encoder