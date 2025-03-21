import requests
import json
import logging
import re

logger = logging.getLogger(__name__)

class GoogleSearchTool:
    """Tool for performing Google searches using the Custom Search JSON API"""
    
    def __init__(self, api_key="AIzaSyAydQbFITjj-_jxwAeg7UNQcZjLzs4fwmc", search_engine_id="a783ec7f54f7c4845"):
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
    
    def search(self, query, num_results=10):
        """
        Perform a Google search with the given query.
        
        Args:
            query (str): The search query.
            num_results (int): Number of results to return (max 10 per request).
            
        Returns:
            list: Search results containing title, snippet, and link.
        """
        try:
            params = {
                'q': query,
                'key': self.api_key,
                'cx': self.search_engine_id,
                'num': min(num_results, 10)  # API allows max 10 per request
            }
            
            logger.info(f"Performing Google search for: {query}")
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            results = response.json()
            
            if 'items' not in results:
                logger.warning(f"No search results found for query: {query}")
                return []
            
            formatted_results = []
            for item in results['items']:
                formatted_results.append({
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'link': item.get('link', '')
                })
            
            logger.info(f"Found {len(formatted_results)} results for query: {query}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error performing Google search: {str(e)}")
            return [{"error": str(e)}]
    
    def research_facility(self, facility_name, location=None):
        """
        Research a healthcare facility by name and optionally location.
        
        Args:
            facility_name (str): The name of the facility.
            location (str, optional): The location to narrow results.
            
        Returns:
            dict: Compiled research data about the facility.
        """
        queries = [
            f"{facility_name} radiology services",
            f"{facility_name} locations {'in ' + location if location else ''}",
            f"{facility_name} healthcare technology",
            f"{facility_name} imaging equipment",
            f"{facility_name} PACS system",
            f"{facility_name} expansion news",
            f"{facility_name} number of radiologists"
        ]
        
        all_results = {}
        for query in queries:
            results = self.search(query, 3)  # Get top 3 results for each query
            all_results[query] = results
        
        # Compile the research into a summary
        summary = {
            "facility_name": facility_name,
            "location": location,
            "sources": [],
            "key_findings": {
                "locations": [],
                "technology": [],
                "staff": [],
                "recent_news": []
            }
        }
        
        # Process the results to extract useful information
        for query, results in all_results.items():
            for result in results:
                # Add unique sources
                if result.get('link') not in [s.get('link') for s in summary["sources"]]:
                    summary["sources"].append({
                        "title": result.get('title'),
                        "link": result.get('link')
                    })
                
                # Extract relevant information based on query category
                snippet = result.get('snippet', '')
                
                if 'locations' in query or 'centers' in query:
                    summary["key_findings"]["locations"].append(snippet)
                
                if 'technology' in query or 'PACS' in query or 'equipment' in query:
                    summary["key_findings"]["technology"].append(snippet)
                
                if 'radiologists' in query or 'staff' in query:
                    summary["key_findings"]["staff"].append(snippet)
                
                if 'news' in query or 'expansion' in query:
                    summary["key_findings"]["recent_news"].append(snippet)
        
        # Add additional analysis - look for address patterns and numbers
        try:
            location_text = " ".join(summary["key_findings"]["locations"])
            
            # Look for location count
            location_count_patterns = [
                r'(\d+)\s+locations?',
                r'(\d+)\s+centers?',
                r'(\d+)\s+facilities?',
                r'locations?\s+in\s+(\d+)',
                r'centers?\s+in\s+(\d+)'
            ]
            
            for pattern in location_count_patterns:
                matches = re.findall(pattern, location_text, re.IGNORECASE)
                if matches:
                    summary["estimated_location_count"] = max([int(m) for m in matches])
                    break
            
            # Look for radiologist count
            staff_text = " ".join(summary["key_findings"]["staff"])
            radiologist_count_patterns = [
                r'(\d+)\s+radiologists?',
                r'team\s+of\s+(\d+)',
                r'staff\s+of\s+(\d+)',
                r'(\d+)\s+physicians?'
            ]
            
            for pattern in radiologist_count_patterns:
                matches = re.findall(pattern, staff_text, re.IGNORECASE)
                if matches:
                    summary["estimated_radiologist_count"] = max([int(m) for m in matches])
                    break
        
        except Exception as e:
            logger.error(f"Error analyzing research results: {str(e)}")
        
        return summary