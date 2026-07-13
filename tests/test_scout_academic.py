import hashlib
import unittest
from unittest.mock import patch, MagicMock
from jobhunt.scouts.academic import AcademicScout
from jobhunt.models import LeadRecord

class TestAcademicScout(unittest.TestCase):
    def setUp(self):
        self.scout = AcademicScout()

    @patch("requests.get")
    def test_search_returns_lead_records(self, mock_get):
        # Mock ArXiv Atom XML response
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2301.00001v1</id>
    <title>Multimodal Large Language Models for Medical IDP</title>
    <summary>Abstract of the paper...</summary>
    <author>
      <name>Alice Smith</name>
    </author>
    <author>
      <name>Bob Jones</name>
    </author>
    <link href="http://arxiv.org/abs/2301.00001v1" rel="alternate" type="text/html"/>
  </entry>
</feed>
"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_xml
        mock_get.return_value = mock_response

        leads = self.scout.search("IDP")

        self.assertEqual(len(leads), 2)
        
        # Check first lead
        lead1 = leads[0]
        self.assertIsInstance(lead1, LeadRecord)
        self.assertEqual(lead1.name, "Alice Smith")
        self.assertEqual(lead1.title, "Author of 'Multimodal Large Language Models for Medical IDP'")
        self.assertEqual(lead1.discovery_source, "ArXiv")
        
        # Check ID generation: hash of name + title
        expected_id = hashlib.sha256("Alice SmithMultimodal Large Language Models for Medical IDP".encode()).hexdigest()[:16]
        self.assertEqual(lead1.id, expected_id)

    @patch("requests.get")
    def test_search_empty_response(self, mock_get):
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
</feed>
"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_xml
        mock_get.return_value = mock_response

        leads = self.scout.search("nonexistent")
        self.assertEqual(len(leads), 0)

    @patch("requests.get")
    def test_search_api_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("Internal Server Error")
        mock_get.return_value = mock_response

        leads = self.scout.search("IDP")
        self.assertEqual(len(leads), 0)

if __name__ == "__main__":
    unittest.main()
