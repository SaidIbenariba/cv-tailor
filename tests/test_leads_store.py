import pytest
import pandas as pd
from pathlib import Path
from jobhunt.models import LeadRecord
from jobhunt import leads_store

@pytest.fixture
def temp_leads_file(tmp_path):
    return tmp_path / "leads.xlsx"

def test_leads_upsert_new_lead(temp_leads_file):
    lead = LeadRecord(
        id="Said Ibenariba|Orange",
        name="Said Ibenariba",
        org="Orange",
        title="AI Engineer",
        discovery_source="LinkedIn",
        context="Working on IDP",
        user_hook="Technical bridge text",
        linkedin_url="https://linkedin.com/in/said",
        status="NEW"
    )
    
    # 1. Load empty
    df = leads_store.load_leads(temp_leads_file)
    assert len(df) == 0
    
    # 2. Upsert
    df = leads_store.upsert_leads(df, [lead])
    assert len(df) == 1
    assert df.iloc[0]["id"] == "Said Ibenariba|Orange"
    assert df.iloc[0]["Status"] == "NEW"
    
    # 3. Save and reload
    leads_store.save_leads(df, temp_leads_file)
    df2 = leads_store.load_leads(temp_leads_file)
    assert len(df2) == 1
    assert df2.iloc[0]["name"] == "Said Ibenariba"
    assert df2.iloc[0]["Status"] == "NEW"

def test_leads_upsert_existing_lead_untouched(temp_leads_file):
    lead = LeadRecord(
        id="Said Ibenariba|Orange",
        name="Said Ibenariba",
        org="Orange",
        title="AI Engineer",
        discovery_source="LinkedIn",
        context="Working on IDP",
        user_hook="Technical bridge text"
    )
    
    df = leads_store.load_leads(temp_leads_file)
    df = leads_store.upsert_leads(df, [lead])
    
    # Manually change status
    df.loc[0, "Status"] = "MESSAGED"
    leads_store.save_leads(df, temp_leads_file)
    
    # Upsert same lead again
    df2 = leads_store.load_leads(temp_leads_file)
    df2 = leads_store.upsert_leads(df2, [lead])
    
    assert len(df2) == 1
    assert df2.iloc[0]["Status"] == "MESSAGED"
