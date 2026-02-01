import pytest
from fastapi.testclient import TestClient
import yaml
from pathlib import Path

# Note: This requires the openapi-spec-validator package or similar logic
# For this project, we might just check that the docs endpoint works and schema is generated
# Or compare generated openapi.json with the spec file if we want strict compliance.

@pytest.mark.contract
def test_openapi_schema_generation(test_client: TestClient):
    """Verify that the API generates a valid OpenAPI schema."""
    response = test_client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["openapi"].startswith("3.")
    assert "paths" in schema
    assert "components" in schema

@pytest.mark.contract
def test_openapi_spec_match(test_client: TestClient):
    """
    Verify that the generated schema matches key parts of the design spec.
    This is a simplified contract test.
    """
    response = test_client.get("/openapi.json")
    generated_schema = response.json()
    
    # Check if critical endpoints from spec exist in implementation
    paths = generated_schema["paths"]
    
    # Resume Upload
    assert "/api/v1/upload/resume" in paths
    assert "post" in paths["/api/v1/upload/resume"]
    
    # Analysis
    assert "/api/v1/analyze" in paths
    assert "post" in paths["/api/v1/analyze"]
    
    # Results
    assert "/api/v1/results/{session_id}" in paths
    
    # Session
    assert "/api/v1/session" in paths

    # Check schemas
    schemas = generated_schema["components"]["schemas"]
    assert "ResumeUploadResponse" in schemas
    assert "JobDescriptionUploadResponse" in schemas
    assert "Skill" in schemas
    assert "Experience" in schemas
