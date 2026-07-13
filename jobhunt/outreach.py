from jobhunt.models import LeadRecord

def generate_ice_breaker(lead: LeadRecord, cv_text: str) -> str:
    """
    Generate a personalized ice-breaker message.
    Attributes the paper clearly to the lead and highlights the user's specific experience.
    """
    # Clean up the lead's paper title from the title field if possible
    paper_title = lead.title.replace("Author of '", "").rstrip("'")
    
    # Selection of projects from Said's CV to rotate or use as bridge
    experience_bridge = (
        f"my work on air-gapped IDP pipelines at Orange Business using Qwen2.5-VL"
    )
    
    # Context-aware CTA
    if lead.related_jobs:
        cta = (
            f"I saw an opening at {lead.org} and would love to discuss how my "
            "background in production-grade AI pipelines could fit your team."
        )
    else:
        cta = "I'd love to connect and potentially share my CV if you're open to a brief chat."

    # Professional template
    template = (
        f"Hi {lead.name},\n\n"
        f"I recently read your paper '{paper_title}' and was impressed by your "
        f"approach to {lead.context[:60]}... Your research aligns closely with "
        f"{experience_bridge}. I've focused on building template-free "
        "validation systems for high-security environments.\n\n"
        f"{cta}\n\n"
        "Best regards,"
    )
    return template
