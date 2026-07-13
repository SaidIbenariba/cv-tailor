from jobhunt.models import LeadRecord
from jobhunt.outreach import generate_ice_breaker

def test_generate_ice_breaker_template():
    lead = LeadRecord(
        id="test-id",
        name="Jane Doe",
        org="AI Lab",
        title="Senior Researcher",
        discovery_source="ArXiv",
        context="recent paper on Multimodal LLMs",
        user_hook="my experience in IDP at Orange"
    )
    cv_text = "Experienced Data Scientist with skills in IDP and LLMs."
    
    message = generate_ice_breaker(lead, cv_text)
    
    assert "Jane Doe" in message
    assert "AI Lab" in message
    assert "Multimodal LLMs" in message
    assert "IDP at Orange" in message
    assert len(message) > 50

def test_generate_ice_breaker_with_jobs():
    lead = LeadRecord(
        id="test-id-2",
        name="John Smith",
        org="Tech Corp",
        title="Engineering Manager",
        discovery_source="LinkedIn",
        context="hiring post for AI Engineers",
        user_hook="my work on air-gapped LLMs",
        related_jobs=["job-123"]
    )
    cv_text = "Experienced AI Engineer."
    
    message = generate_ice_breaker(lead, cv_text)
    
    assert "Tech Corp" in message
    assert "air-gapped LLMs" in message
    assert "job-123" in message or "opening" in message.lower()
