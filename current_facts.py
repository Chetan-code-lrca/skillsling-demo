# Manual current facts database for SkillSling AI
# This is manually updated - no API key needed

# Current facts (verified Feb 2026)
CURRENT_FACTS = {
    # Andhra Pradesh
    "ap cm": "N. Chandrababu Naidu (CM since June 2024, TDP party)",
    "andhra pradesh cm": "N. Chandrababu Naidu (CM since June 2024, TDP party)",
    "current cm of andhra": "N. Chandrababu Naidu (CM since June 2024)",
    
    # Telangana
    "ts cm": "A. Revanth Reddy (CM since December 2023, Congress)",
    "telangana cm": "A. Revanth Reddy (CM since December 2023, Congress)",
    "current cm of telangana": "A. Revanth Reddy (CM since December 2023)",
    
    # Other states
    "rajasthan cm": "Bhajan Lal Sharma (CM since December 2023, BJP)",
    "up cm": "Yogi Adityanath (CM since March 2017, BJP)",
    "mumbai cm": "Maharashtra has CM - Eknath Shinde (since June 2022, BJP-Shiv Sena alliance)",
    "maharashtra cm": "Eknath Shinde (CM since June 2022)",
    "delhi cm": "Atishi (CM since September 2024, AAP)",
    
    # Governors
    "ap governor": "S. Abdul Nazeer (since July 2023)",
    "ts governor": "Jishnu Dev Varma (since February 2024)",
    
    # PM
    "india pm": "Narendra Modi (PM since May 2014, BJP)",
    "current pm of india": "Narendra Modi (PM since May 2014)",
    
    # President
    "india president": "Droupadi Murmu (President since July 2022)",
    "current president of india": "Droupadi Murmu (since July 2022)",

    # Economic Theories
    "drain theory": "Drain Theory (Dadabhai Naoroji, 19th century): Systematic transfer of wealth from India to Britain during British rule without adequate return. Key sources: Salaries of British officials, profits of British companies, 'Home Charges' (pensions, admin), interest on debt, and export surplus not returned to India.",
}

def get_current_facts(query):
    """Check if query is about current facts"""
    query_lower = query.lower()
    
    for key, value in CURRENT_FACTS.items():
        if key in query_lower:
            return value
    
    return None
