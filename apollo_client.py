import requests
from urllib.parse import urlparse

class ApolloClient:
    """Client for interacting with the Apollo API"""
    
    BASE_URL = "https://api.apollo.io/v1"
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache"
        }
    
    def clean_website_url(self, url):
        """Clean and normalize a website URL"""
        if not url:
            return url
        
        url = url.strip()
        
        # For search, we just need the domain without http/https
        if '/' in url or '.' in url:
            # Try to parse it as a URL
            if not (url.startswith('http://') or url.startswith('https://')):
                url = 'https://' + url
                
            try:
                parsed_url = urlparse(url)
                # Get just the domain for search
                domain = parsed_url.netloc
                if not domain:  # Handle cases with no scheme
                    domain = parsed_url.path.split('/')[0]
                    
                # Remove www. prefix if present for more consistent searches
                if domain.startswith('www.'):
                    domain = domain[4:]
                    
                return domain
            except:
                # If parsing fails, just return the original
                return url
        
        # If it doesn't look like a URL at all, just return it
        return url

    def search_organizations(self, domain=None, name=None, limit=10):
        """Search for organizations by domain or name"""
        url = f"{self.BASE_URL}/organizations/search"
        
        data = {
            "api_key": self.api_key,
            "page": 1,
            "per_page": limit
        }
        
        if domain:
            cleaned_domain = self.clean_website_url(domain)
            parsed_domain = urlparse(cleaned_domain).netloc or urlparse(cleaned_domain).path
            data["q_organization_domains"] = [parsed_domain]
        
        if name:
            data["q_organization_name"] = name
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error searching organizations: {str(e)}")
            return {"error": str(e), "organizations": []}

    def search_people(self, organization_id=None, titles=None, departments=None, seniorities=None, limit=25):
        """Search for people within an organization"""
        url = f"{self.BASE_URL}/people/search"
        
        data = {
            "api_key": self.api_key,
            "page": 1,
            "per_page": limit
        }
        
        if organization_id:
            data["q_organization_id"] = organization_id
        
        if titles:
            data["q_titles"] = titles
        
        if departments:
            data["q_departments"] = departments
        
        if seniorities:
            data["q_seniorities"] = seniorities
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error searching people: {str(e)}")
            return {"error": str(e), "people": []}

    def get_person_details(self, person_id):
        """Get detailed information about a specific person"""
        url = f"{self.BASE_URL}/people/{person_id}"
        
        params = {
            "api_key": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting person details: {str(e)}")
            return {"error": str(e)}

    def get_organization_details(self, organization_id):
        """Get detailed information about a specific organization"""
        url = f"{self.BASE_URL}/organizations/{organization_id}"
        
        params = {
            "api_key": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting organization details: {str(e)}")
            return {"error": str(e)}

    def enrich_domain(self, domain):
        """Enrich a domain with organization data"""
        url = f"{self.BASE_URL}/organizations/enrich"
        
        cleaned_domain = self.clean_website_url(domain)
        parsed_domain = urlparse(cleaned_domain).netloc or urlparse(cleaned_domain).path
        
        data = {
            "api_key": self.api_key,
            "domain": parsed_domain
        }
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error enriching domain: {str(e)}")
            return {"error": str(e)}

    def enrich_person(self, email=None, first_name=None, last_name=None, organization_name=None):
        """Enrich person data with contact information"""
        url = f"{self.BASE_URL}/people/match"
        
        data = {
            "api_key": self.api_key
        }
        
        if email:
            data["email"] = email
        
        if first_name and last_name and organization_name:
            data["first_name"] = first_name
            data["last_name"] = last_name
            data["organization_name"] = organization_name
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error enriching person: {str(e)}")
            return {"error": str(e)}

    def unlock_contact(self, person_id):
        """Reveal a contact's details (uses credits)"""
        url = f"{self.BASE_URL}/people/{person_id}/reveal"
        data = {
            "api_key": self.api_key
        }
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error unlocking contact: {str(e)}")
            return {"error": str(e)}