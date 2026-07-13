import hashlib
import logging
import requests
import xml.etree.ElementTree as ET
from jobhunt.models import LeadRecord

log = logging.getLogger("jobhunt.scouts.academic")

class AcademicScout:
    """Scout for ArXiv academic leads."""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    NAMESPACE = {"atom": "http://www.w3.org/2005/Atom"}

    def search(self, query: str, max_results: int = 10) -> list[LeadRecord]:
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
        except Exception as e:
            log.error("ArXiv API request failed: %s", e)
            return []

        root = ET.fromstring(response.text)
        leads = []
        
        for entry in root.findall("atom:entry", self.NAMESPACE):
            title_elem = entry.find("atom:title", self.NAMESPACE)
            title = title_elem.text.strip() if title_elem is not None else "Unknown Title"
            # Clean up title (remove newlines often present in ArXiv titles)
            title = " ".join(title.split())
            
            summary_elem = entry.find("atom:summary", self.NAMESPACE)
            summary = summary_elem.text.strip() if summary_elem is not None else ""
            summary = " ".join(summary.split())
            
            link_elem = entry.find("atom:link[@rel='alternate']", self.NAMESPACE)
            paper_url = link_elem.get("href") if link_elem is not None else ""

            for author in entry.findall("atom:author", self.NAMESPACE):
                name_elem = author.find("atom:name", self.NAMESPACE)
                if name_elem is None:
                    continue
                name = name_elem.text.strip()
                
                # ArXiv sometimes has affiliation in a separate tag if using extensions,
                # but standard Atom doesn't have it easily. We'll leave org empty or use a placeholder.
                # The design spec mentioned ArXiv/Scholar authors.
                org = "ArXiv Researcher" 
                
                lead_title = f"Author of '{title}'"
                
                # ID generation: hash of name + original paper title (to be unique per paper-author pair)
                id_input = f"{name}{title}"
                lead_id = hashlib.sha256(id_input.encode()).hexdigest()[:16]
                
                leads.append(LeadRecord(
                    id=lead_id,
                    name=name,
                    org=org,
                    title=lead_title,
                    discovery_source="ArXiv",
                    context=summary[:200] + "..." if len(summary) > 200 else summary,
                    user_hook=f"Found via paper: {title}",
                    social_url=paper_url
                ))
        
        return leads
