from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Dict, Any

class Base_io(BaseModel):
    """
    Base class for IO operations.
    uri: youtube id or any unique identifier for the video/audio
    root_path: root directory for saving files. Default is current directory.
    metadata_json: name of the metadata JSON file. Default is 'metadata.json'.
    """
    uri: str = Field(..., description="Unique identifier for the resource, e.g., YouTube video ID.")
    root_path: str = Field(default=".")
    metadata_json: str = "metadata.json"
    force: bool = Field(default=False, description="Force overwrite existing files.")
    jinja: Dict[str, Any] = Field(default_factory=dict)

if __name__ == "__main__":
    # Example usage
    io_instance = Base_io(uri="example_uri")
    print(io_instance)