import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
import concurrent.futures
import logging
from collections import Counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedWebsiteScraper:
   """
   Advanced website scraper that extracts healthcare IT-specific intelligence
   from medical facility websites for sales targeting.
   """
   
   def __init__(self):
       self.headers = {
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
       }
       # Key pages to scrape beyond homepage
       self.target_pages = [
           '/', '/about', '/about-us', '/technology', '/services', '/solutions', 
           '/radiology', '/imaging', '/our-team', '/staff', '/careers', '/jobs',
           '/it', '/information-technology', '/medical-imaging', '/pacs',
           # Add these new specific targets
           '/locations', '/our-locations', '/centers', '/find-us',
           '/equipment', '/technologies', '/modalities', '/patient-info',
           '/patient-portal', '/for-patients', '/appointments',
           '/contact', '/contact-us', '/leadership', '/physicians',
           '/news', '/press', '/blog', '/events'
       ]
       # Healthcare IT specific terms to look for
       self.healthcare_it_terms = {
           'pacs_terms': [
               'pacs', 'picture archiving', 'image archiving', 'archiving system', 
               'imaging system', 'radiological information', 'ris'
           ],
           'vendor_terms': [
               'ge healthcare', 'siemens', 'philips', 'agfa', 'fujifilm', 'carestream',
               'mckesson', 'merge', 'intelerad', 'sectra', 'cerner', 'epic', 'allscripts',
               'meditech', 'nuance', 'hyland', 'change healthcare', 'ibm watson'
           ],
           'imaging_terms': [
               'ct scan', 'mri', 'ultrasound', 'x-ray', 'radiograph', 'fluoroscopy',
               'mammography', 'nuclear medicine', 'pet scan', 'radiology', 'imaging',
               'radiologist', 'sonographer', 'modality', 'dicom', '3t', '1.5t', 'tesla'
           ],
           'workflow_terms': [
               'workflow', 'efficiency', 'productivity', 'throughput', 'turnaround time',
               'report', 'dictation', 'voice recognition', 'integration', 'interface',
               'downtime', 'reliability', 'upgrade', 'migration', 'replacement',
               'interoperability', 'referring physician', 'portal'
           ],
           'pain_point_terms': [
               'challenge', 'issue', 'problem', 'difficult', 'slow', 'outdated',
               'legacy', 'obsolete', 'maintenance', 'support', 'cost', 'expensive',
               'budget', 'compliance', 'hipaa', 'security', 'patient safety',
               'burnout', 'shortage', 'manual', 'error', 'inefficient'
           ],
           'technology_stack': [
               'cloud', 'server', 'storage', 'virtualization', 'vmware', 'microsoft',
               'linux', 'database', 'sql', 'oracle', 'redundancy', 'backup', 'disaster recovery',
               'high availability', 'san', 'nas', 'vendor neutral archive', 'vna'
           ],
           'modernization_terms': [
               'upgrade', 'implementation', 'project', 'initiative', 'strategic',
               'roadmap', 'plan', 'future', 'investment', 'transform', 'improvement',
               'modernize', 'enhance', 'optimize', 'expansion', 'growth'
           ]
       }
       self.pages_data = []
   
   def clean_url(self, url):
       """Normalize and clean the URL"""
       url = url.strip()
       if not url.startswith(('http://', 'https://')):
           url = 'https://' + url
       return url
   
   def get_base_url(self, url):
       """Extract the base URL"""
       parsed = urlparse(url)
       base_url = f"{parsed.scheme}://{parsed.netloc}"
       return base_url
   
   def is_valid_url(self, url, base_url):
       """Check if URL is valid and within the same domain"""
       if not url:
           return False
       # Skip anchors, javascript, mailto, tel links
       if url.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
           return False
       # Check if url is relative or from same domain
       parsed = urlparse(url)
       if not parsed.netloc:  # Relative URL
           return True
       return parsed.netloc == urlparse(base_url).netloc
   
   def normalize_url(self, url, base_url):
       """Normalize relative URLs to absolute"""
       if not url:
           return None
       if url.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
           return None
       return urljoin(base_url, url)
   
   def build_target_urls(self, base_url):
       """Build list of target URLs to scrape"""
       return [urljoin(base_url, path) for path in self.target_pages]
   
   def scrape_page(self, url, timeout=10):
       """Scrape a single page and extract content"""
       try:
           response = requests.get(url, headers=self.headers, timeout=timeout)
           response.raise_for_status()
           return response.text
       except Exception as e:
           logger.warning(f"Failed to scrape {url}: {str(e)}")
           return None
   
   def extract_page_data(self, html, url):
       """Extract relevant data from page HTML"""
       if not html:
           return None
       
       soup = BeautifulSoup(html, 'html.parser')
       
       # Basic page data
       title = soup.title.text.strip() if soup.title else ""
       meta_desc = ""
       meta_tag = soup.find("meta", attrs={"name": "description"})
       if meta_tag:
           meta_desc = meta_tag.get("content", "")
       
       # Extract main content text
       main_content = []
       for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'li']):
           text = tag.get_text(strip=True)
           if text and len(text) > 15:  # Filter out short snippets
               main_content.append(text)
       
       content_text = " ".join(main_content)
       
       # Extract links for further analysis
       links = []
       for link in soup.find_all('a', href=True):
           href = link['href']
           text = link.get_text(strip=True)
           if href and self.is_valid_url(href, url):
               norm_url = self.normalize_url(href, url)
               if norm_url:
                   links.append({
                       "url": norm_url,
                       "text": text
                   })
       
       # Find job postings if on careers page
       job_listings = []
       if any(x in url.lower() for x in ['/career', '/job', '/careers', '/jobs']):
           job_sections = soup.find_all(['div', 'section', 'article'], 
                                       class_=lambda c: c and any(x in str(c).lower() for x in 
                                                               ['job', 'career', 'position', 'opening']))
           
           for section in job_sections:
               job_titles = section.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'a'], 
                                           string=lambda s: s and any(x in s.lower() for x in 
                                                                   ['specialist', 'technologist', 'engineer', 
                                                                    'analyst', 'administrator', 'director', 'manager']))
               for job in job_titles:
                   job_text = job.get_text(strip=True)
                   if job_text and len(job_text) > 5:
                       job_listings.append(job_text)
       
       # Look for technology indicators
       tech_indicators = {}
       for category, terms in self.healthcare_it_terms.items():
           matches = []
           content_lower = content_text.lower()
           for term in terms:
               count = content_lower.count(term)
               if count > 0:
                   matches.append({"term": term, "count": count})
           tech_indicators[category] = matches
       
       # Find email addresses
       emails = []
       email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
       found_emails = re.findall(email_pattern, content_text)
       emails = list(set(found_emails))  # Remove duplicates
       
       # Return structured page data
       return {
           "url": url,
           "title": title,
           "meta_description": meta_desc,
           "content": content_text,
           "content_length": len(content_text),
           "links": links,
           "job_listings": job_listings,
           "technology_indicators": tech_indicators,
           "emails": emails,
           "html": html  # Store the HTML for later processing
       }
   
   def extract_location_count(self, pages_data):
       """Extract and count locations from website data"""
       location_count = 0
       location_names = set()
       
       # Look for location pages
       location_pages = [page for page in pages_data if page and 
                        any(loc_term in page['url'].lower() 
                            for loc_term in ['location', 'centers', 'find-us'])]
       
       if location_pages:
           for page in location_pages:
               soup = BeautifulSoup(page.get('html', ''), 'html.parser')
               
               # Look for common location patterns
               location_sections = soup.find_all(['div', 'section', 'article'], 
                                              class_=lambda c: c and any(x in str(c).lower() 
                                                                      for x in ['location', 'center', 'address']))
               
               # Process headings and addresses
               for section in location_sections:
                   locations = section.find_all(['h2', 'h3', 'h4', 'h5', 'address'])
                   for location in locations:
                       location_text = location.get_text(strip=True)
                       if location_text and len(location_text) > 10:  # Avoid very short text
                           location_names.add(location_text)
               
               # Count location listing items
               list_items = soup.find_all('li')
               for item in list_items:
                   if any(addr_indicator in item.text.lower() 
                         for addr_indicator in ['suite', 'street', 'drive', 'lane', 'road', 'ave', 'blvd']):
                       location_text = item.get_text(strip=True)
                       if location_text and len(location_text) > 10:
                           location_names.add(location_text)
       
       # If we found specific locations, return that count
       if location_names:
           return len(location_names)
       
       # Otherwise try to infer from text
       all_content = " ".join([page.get('content', '') for page in pages_data if page])
       
       # Look for specific phrases indicating multiple locations
       location_indicators = [
           r'(\d+)\s+locations', r'(\d+)\s+centers', r'(\d+)\s+facilities',
           r'(\d+)\s+offices', r'(\d+)\s+clinics', r'serving\s+(\d+)\s+locations'
       ]
       
       for indicator in location_indicators:
           matches = re.findall(indicator, all_content, re.IGNORECASE)
           if matches:
               try:
                   # Take the largest number mentioned
                   return max([int(num) for num in matches])
               except:
                   pass
       
       # Default to 1 if we couldn't find explicit mentions
       return max(1, len(location_names))
   
   def extract_equipment_information(self, pages_data):
       """Extract information about imaging equipment"""
       equipment_info = []
       equipment_terms = {
           "CT Scanner": ['ct scanner', 'computed tomography', 'ct scan'],
           "MRI": ['mri', 'magnetic resonance', 'tesla'],
           "X-Ray": ['x-ray', 'radiography', 'digital radiography'],
           "Ultrasound": ['ultrasound', 'sonogram', 'doppler'],
           "Mammography": ['mammogram', 'mammography', 'breast imaging'],
           "PET": ['pet scan', 'pet/ct', 'positron emission'],
           "Nuclear Medicine": ['nuclear medicine', 'spect', 'gamma camera']
       }
       
       # Process each page for equipment mentions
       for page in pages_data:
           if not page:
               continue
           
           content = page.get('content', '').lower()
           
           # Check for equipment mentions
           for equip_type, terms in equipment_terms.items():
               for term in terms:
                   if term in content:
                       # Try to find the specific model or vendor
                       # Look for vendor names near equipment terms
                       vendors = ['ge', 'siemens', 'philips', 'toshiba', 'canon', 'hitachi', 'samsung', 'fujifilm']
                       
                       # Extract sentences containing both the equipment term and possibly a vendor
                       sentences = re.split(r'(?<=[.!?])\s+', content)
                       for sentence in sentences:
                           if term in sentence:
                               # Check for vendors in the same sentence
                               vendor_found = None
                               for vendor in vendors:
                                   if vendor in sentence:
                                       vendor_found = vendor
                                       break
                               
                               # Look for model numbers or tesla strength for MRIs
                               model_info = None
                               if 'tesla' in sentence and 'mri' in sentence:
                                   tesla_match = re.search(r'(\d+\.?\d*)\s*tesla', sentence)
                                   if tesla_match:
                                       model_info = f"{tesla_match.group(1)}T"
                               
                               equipment_info.append({
                                   "type": equip_type,
                                   "vendor": vendor_found.title() if vendor_found else "Unknown",
                                   "model_info": model_info,
                                   "source": page['url']
                               })
                               
                               # Only add each equipment type once per page
                               break
       
       return equipment_info
   
   def find_key_personnel(self, pages_data):
       """Extract likely key personnel from about/team pages"""
       key_personnel = []
       leadership_titles = [
           'ceo', 'cio', 'cto', 'chief', 'director', 'president', 'vp', 'vice president',
           'head', 'manager', 'lead', 'principal', 'radiologist', 'chairman', 'founder',
           'administrator', 'medical director'
       ]
       
       for page in pages_data:
           if not page:
               continue
               
           if any(x in page['url'].lower() for x in ['/about', '/team', '/staff', '/leadership', '/physician']):
               soup = BeautifulSoup(page.get('html', ''), 'html.parser')
               
               # Look for common team member patterns
               team_sections = soup.find_all(['div', 'section', 'article'], 
                                           class_=lambda c: c and any(x in str(c).lower() for x in 
                                                                   ['team', 'staff', 'leadership', 'management', 'about', 'physician']))
               
               for section in team_sections:
                   name_elements = section.find_all(['h2', 'h3', 'h4', 'h5', 'strong'])
                   
                   for element in name_elements:
                       name = element.get_text(strip=True)
                       # Look for nearby elements that might contain title
                       siblings = list(element.next_siblings)
                       title = ""
                       
                       for sibling in siblings[:3]:  # Check next 3 elements
                           sibling_text = sibling.get_text(strip=True) if hasattr(sibling, 'get_text') else str(sibling).strip()
                           if any(title_term in sibling_text.lower() for title_term in leadership_titles):
                               title = sibling_text
                               break
                       
                       if title:
                           key_personnel.append({
                               "name": name,
                               "title": title,
                               "url": page['url']
                           })
       
       return key_personnel
   
   def analyze_tech_stack(self, pages_data):
       """Analyze likely technology stack based on all scraped content"""
       all_content = " ".join([page.get('content', '') for page in pages_data if page])
       all_content = all_content.lower()
       
       tech_stack = {
           "pacs_vendor": self._identify_pacs_vendor(all_content),
           "ris_vendor": self._identify_ris_vendor(all_content),
           "infrastructure": self._identify_infrastructure(all_content),
           "modalities": self._identify_modalities(all_content),
           "emr_system": self._identify_emr_system(all_content),
           "it_environment": self._identify_it_environment(all_content)
       }
       
       return tech_stack
   
   def _identify_pacs_vendor(self, content):
       """Attempt to identify PACS vendor from content"""
       vendors = {
           "GE Healthcare": ['ge healthcare', 'ge pacs', 'centricity'],
           "Philips": ['philips', 'intellispace'],
           "Siemens": ['siemens', 'syngo'],
           "Fujifilm": ['fujifilm', 'synapse'],
           "Agfa": ['agfa', 'impax', 'enterprise imaging'],
           "Carestream": ['carestream', 'vue pacs'],
           "Merge (IBM)": ['merge', 'merge pacs'],
           "Sectra": ['sectra'],
           "Intelerad": ['intelerad'],
           "Change Healthcare": ['change healthcare', 'mckesson'],
           "Hyland": ['hyland', 'acuo', 'nilread']
       }
       
       matches = {}
       for vendor, terms in vendors.items():
           count = sum(content.count(term) for term in terms)
           if count > 0:
               matches[vendor] = count
       
       if matches:
           return max(matches.items(), key=lambda x: x[1])[0]
       return "Unknown"
   
   def _identify_ris_vendor(self, content):
       """Attempt to identify RIS vendor from content"""
       vendors = {
           "Epic Radiant": ['epic', 'radiant'],
           "Cerner": ['cerner', 'radnet'],
           "Meditech": ['meditech'],
           "Allscripts": ['allscripts'],
           "GE Healthcare": ['ge', 'centricity ris'],
           "Merge (IBM)": ['merge ris'],
           "Fujifilm": ['fujifilm ris', 'synapse ris']
       }
       
       matches = {}
       for vendor, terms in vendors.items():
           count = sum(content.count(term) for term in terms)
           if count > 0:
               matches[vendor] = count
       
       if matches:
           return max(matches.items(), key=lambda x: x[1])[0]
       return "Unknown"
   
   def _identify_emr_system(self, content):
       """Attempt to identify EMR system from content"""
       vendors = {
           "Epic": ['epic', 'epic systems', 'epic emr', 'epic ehr'],
           "Cerner": ['cerner', 'cerner millennium', 'cerner ehr'],
           "Meditech": ['meditech', 'meditech ehr'],
           "Allscripts": ['allscripts', 'allscripts professional'],
           "athenahealth": ['athenahealth', 'athenaclinicals'],
           "eClinicalWorks": ['eclinicalworks', 'ecw'],
           "NextGen": ['nextgen', 'nextgen healthcare'],
           "Greenway": ['greenway', 'greenway health', 'prime suite']
       }
       
       matches = {}
       for vendor, terms in vendors.items():
           count = sum(content.count(term) for term in terms)
           if count > 0:
               matches[vendor] = count
       
       if matches:
           return max(matches.items(), key=lambda x: x[1])[0]
       return "Unknown"
   
   def _identify_infrastructure(self, content):
       """Identify infrastructure elements"""
       infrastructure_elements = []
       
       if any(term in content for term in ['cloud', 'aws', 'azure', 'google cloud']):
           infrastructure_elements.append("Cloud-based")
       
       if any(term in content for term in ['on-premise', 'on-prem', 'local server', 'data center']):
           infrastructure_elements.append("On-premise")
       
       if any(term in content for term in ['vmware', 'virtualization', 'virtual server']):
           infrastructure_elements.append("Virtualized Environment")
           
       if any(term in content for term in ['san', 'nas', 'storage area network', 'network attached storage']):
           infrastructure_elements.append("Enterprise Storage")
           
       if any(term in content for term in ['vendor neutral archive', 'vna']):
           infrastructure_elements.append("VNA")
           
       if any(term in content for term in ['enterprise imaging', 'integrated imaging']):
           infrastructure_elements.append("Enterprise Imaging Strategy")
           
       return infrastructure_elements
   
   def _identify_it_environment(self, content):
       """Identify IT environment characteristics"""
       environment = {}
       
       # Determine staffing situation
       if any(term in content for term in ['it staff shortage', 'limited it resources', 'outsourced it']):
           environment["staffing"] = "Limited IT resources"
       elif any(term in content for term in ['in-house it', 'it department', 'technology team']):
           environment["staffing"] = "In-house IT department"
       
       # Determine security stance
       if any(term in content for term in ['hipaa compliance', 'data security', 'cybersecurity']):
           environment["security_focus"] = "High"
       
       # Determine integration approach
       if any(term in content for term in ['interoperability', 'integration', 'connected systems']):
           environment["integration_focus"] = "High"
       
       # Determine budget constraints
       if any(term in content for term in ['budget constraints', 'cost-effective', 'affordable']):
           environment["budget_constraints"] = "High"
       
       return environment
   
   def _identify_modalities(self, content):
       """Identify imaging modalities in use"""
       modalities = []
       modality_terms = {
           "CT": ['ct scan', 'computed tomography', 'ct scanner'],
           "MRI": ['mri', 'magnetic resonance', 'mri scanner'],
           "Ultrasound": ['ultrasound', 'sonography', 'doppler'],
           "X-ray": ['x-ray', 'radiography', 'digital radiography', 'dr'],
           "Mammography": ['mammography', 'mammogram', 'breast imaging'],
           "Nuclear Medicine": ['nuclear medicine', 'pet', 'pet/ct', 'spect'],
           "Interventional": ['interventional', 'angiography', 'fluoroscopy'],
           "Dental": ['dental', 'cone beam', 'cbct', 'panoramic']
       }
       
       for modality, terms in modality_terms.items():
           if any(term in content for term in terms):
               modalities.append(modality)
       
       return modalities
   
   def identify_growth_indicators(self, pages_data):
       """Identify indicators of growth or expansion"""
       growth_indicators = []
       growth_terms = [
           'expansion', 'growing', 'new facility', 'new location',
           'construction', 'renovation', 'upgrade', 'investment',
           'strategic plan', 'future', 'initiative', 'advancing',
           'state-of-the-art', 'cutting edge', 'innovation'
       ]
       
       for page in pages_data:
           if not page:
               continue
           
           content = page.get('content', '').lower()
           
           for term in growth_terms:
               if term in content:
                   # Extract sentences containing growth terms
                   sentences = re.split(r'(?<=[.!?])\s+', content)
                   for sentence in sentences:
                       if term in sentence.lower():
                           growth_indicators.append({
                               "indicator": term,
                               "context": sentence.strip(),
                               "page": page['url']
                           })
       
       return growth_indicators
   
   def identify_pain_points(self, pages_data):
       """Identify potential pain points"""
       pain_points = []
       pain_terms = [
           'challenge', 'difficult', 'problem', 'issue', 'obstacle',
           'inefficient', 'slow', 'legacy', 'outdated', 'obsolete',
           'burden', 'costly', 'expensive', 'time-consuming', 'manual',
           'error', 'mistake', 'downtime', 'failure', 'compliance',
           'backlog', 'delay', 'wait time', 'turnaround'
       ]
       
       for page in pages_data:
           if not page:
               continue
           
           content = page.get('content', '').lower()
           
           for term in pain_terms:
               if term in content:
                   # Extract sentences containing pain terms
                   sentences = re.split(r'(?<=[.!?])\s+', content)
                   for sentence in sentences:
                       if term in sentence.lower():
                           pain_points.append({
                               "indicator": term,
                               "context": sentence.strip(),
                               "page": page['url']
                           })
       
       return pain_points
       
   def extract_annual_study_volume(self, pages_data):
       """Estimate annual imaging study volume"""
       all_content = " ".join([page.get('content', '') for page in pages_data if page])
       
       # Look for explicit mentions of study volumes
       volume_patterns = [
           r'(\d+(?:,\d+)?)\s+(?:studies|exams|scans|images|imaging procedures|procedures|patients)\s+(?:per|a|each)\s+(?:year|annually)',
           r'annual\s+volume\s+of\s+(\d+(?:,\d+)?)',
           r'performs?\s+(?:over|about|approximately)?\s+(\d+(?:,\d+)?)\s+(?:studies|exams|procedures)',
           r'serving\s+(?:over|about|approximately)?\s+(\d+(?:,\d+)?)\s+patients'
       ]
       
       for pattern in volume_patterns:
           matches = re.findall(pattern, all_content, re.IGNORECASE)
           if matches:
               # Convert to integers and find the max
               volumes = []
               for match in matches:
                   try:
                       volumes.append(int(match.replace(',', '')))
                   except ValueError:
                       continue
               
               if volumes:
                   return max(volumes)
       
       # If no explicit mention, estimate based on facility size and type
       location_count = self.extract_location_count(pages_data)
       modalities = self._identify_modalities(all_content)
       
       # Base estimates by facility type
       facility_type_indicators = {
           "hospital": ['hospital', 'medical center', 'health system'],
           "imaging_center": ['imaging center', 'diagnostic center', 'radiology center'],
           "physician_practice": ['physician practice', 'medical practice', 'clinic'],
           "outpatient": ['outpatient', 'ambulatory']
       }
       
       facility_type = None
       for type_name, indicators in facility_type_indicators.items():
           if any(indicator in all_content.lower() for indicator in indicators):
               facility_type = type_name
               break
       
       # Estimate based on facility type, locations, and modalities
       if facility_type == "hospital":
           base_volume = 50000
       elif facility_type == "imaging_center":
           base_volume = 20000
       elif facility_type == "physician_practice":
           base_volume = 5000
       elif facility_type == "outpatient":
           base_volume = 15000
       else:
           base_volume = 10000  # default
       
       # Adjust for multiple locations
       estimated_volume = base_volume * location_count
       
       # Adjust for modality mix
       modality_count = len(modalities)
       if modality_count > 4:  # Comprehensive services
           estimated_volume *= 1.5
       
       return int(estimated_volume)
   
   def identify_regional_competitors(self, facility_name, location):
       """Identify similar healthcare facilities in the same region"""
       competitors = []
       
       # Extract state from location
       state_match = re.search(r',\s*([A-Z]{2})', location)
       state = state_match.group(1) if state_match else None
       
       if not state:
           # Try to extract from text patterns
           state_patterns = [
               r'located in (\w+)',
               r'based in (\w+)',
               r'serving (\w+)',
               r'throughout (\w+)'
           ]
           
           all_content = " ".join([page.get('content', '') for page in self.pages_data if page])
           
           for pattern in state_patterns:
               matches = re.findall(pattern, all_content, re.IGNORECASE)
               if matches:
                   state = matches[0]
                   break
       
       # If we have a state, use it to identify potential regional competitors
       if state:
           # List of common terms used by imaging centers
           imaging_terms = [
               'radiology', 'imaging', 'diagnostic', 'medical imaging',
               'mri', 'ct scan', 'x-ray', 'ultrasound'
           ]
           
           # These would typically come from an API search in a real implementation
           # But for demonstration, we'll use a few examples based on location
           if state.upper() == 'TX' or 'texas' in state.lower():
               competitors = [
                   {
                       "name": "Austin Radiological Association",
                       "website": "https://www.ausrad.com",
                       "description": "Large multi-specialty imaging practice serving central Texas"
                   },
                   {
                       "name": "Southwest Diagnostic Imaging Center",
                       "website": "https://www.swdic.com",
                       "description": "Comprehensive outpatient imaging center in Dallas"
                   },
                   {
                       "name": "Green Imaging",
                       "website": "https://greenimaging.net",
                       "description": "Affordable imaging centers across Texas"
                   }
               ]
           elif state.upper() == 'CA' or 'california' in state.lower():
               competitors = [
                   {
                       "name": "RadNet",
                       "website": "https://www.radnet.com",
                       "description": "Largest network of imaging centers in California"
                   },
                   {
                       "name": "Dignity Health",
                       "website": "https://www.dignityhealth.org",
                       "description": "Hospital system with multiple imaging locations"
                   }
               ]
           elif state.upper() == 'FL' or 'florida' in state.lower():
               competitors = [
                   {
                       "name": "RadiologyAssociates of Florida",
                       "website": "https://www.raflorida.com",
                       "description": "Radiology group serving multiple hospitals in Florida"
                   },
                   {
                       "name": "Tower Radiology",
                       "website": "https://www.towerradiologycenters.com",
                       "description": "Multiple outpatient centers in the Tampa area"
                   }
               ]
           elif state.upper() == 'NY' or 'new york' in state.lower():
               competitors = [
                   {
                       "name": "Lenox Hill Radiology",
                       "website": "https://www.lenoxhillradiology.com",
                       "description": "Network of outpatient radiology centers in NY area"
                   },
                   {
                       "name": "Zwanger-Pesiri Radiology",
                       "website": "https://www.zprad.com",
                       "description": "Large radiology group with multiple locations"
                   }
               ]
           else:
               # Generic competitors for other regions
               competitors = [
                   {
                       "name": "RadNet",
                       "website": "https://www.radnet.com",
                       "description": "National chain of imaging centers"
                   },
                   {
                       "name": "American Radiology",
                       "website": "https://www.americanradiology.com",
                       "description": "Radiology services throughout the US"
                   }
               ]
       
       # Add shared challenges based on competitor profiles
       for competitor in competitors:
           competitor["shared_challenges"] = [
               "Integration of multiple PACS systems across locations",
               "Managing large volumes of imaging data",
               "Secure sharing of images with referring physicians",
               "Compliance with changing healthcare regulations",
               "Staff shortages and efficiency challenges"
           ]
       
       return competitors
   
   def extract_technology_implementation_dates(self, pages_data):
       """Extract information about when technologies were implemented"""
       implementation_info = []
       
       # Terms that indicate technology implementation
       implementation_terms = [
           'implemented', 'deployed', 'installed', 'upgraded to', 
           'migrated to', 'adopted', 'switched to', 'partnered with'
       ]
       
       # Technology terms to look for
       tech_terms = [
           'pacs', 'ris', 'emr', 'ehr', 'vna', 'radiology information system',
           'electronic health record', 'vendor neutral archive', 'cloud'
       ]
       
       year_pattern = r'\b(20\d\d)\b'  # Four-digit years starting with 20
       
       for page in pages_data:
           if not page:
               continue
           
           content = page.get('content', '').lower()
           
           # Look for sentences containing both implementation terms and technology terms
           sentences = re.split(r'(?<=[.!?])\s+', content)
           for sentence in sentences:
               if any(term in sentence for term in implementation_terms) and any(tech in sentence for tech in tech_terms):
                   # Look for a year in the sentence
                   year_match = re.search(year_pattern, sentence)
                   if year_match:
                       year = year_match.group(1)
                       
                       # Determine which technology is mentioned
                       tech_mentioned = None
                       for tech in tech_terms:
                           if tech in sentence:
                               tech_mentioned = tech
                               break
                       
                       implementation_info.append({
                           "technology": tech_mentioned.upper() if tech_mentioned else "Technology system",
                           "year": year,
                           "context": sentence.strip(),
                           "page": page['url']
                       })
       
       return implementation_info
   
   def analyze_budget_cycle(self, pages_data):
       """Analyze content to determine likely budget cycle"""
       budget_info = {}
       
       all_content = " ".join([page.get('content', '') for page in pages_data if page])
       
       # Look for explicit mentions of fiscal year
       fiscal_year_patterns = [
           r'fiscal\s+year\s+(?:begins|starts|commences)\s+(?:on|in)\s+(\w+)',
           r'(?:fy|fiscal year|budget year)\s+(?:begins|starts|runs)\s+(?:from)?\s+(\w+)'
       ]
       
       for pattern in fiscal_year_patterns:
           matches = re.findall(pattern, all_content, re.IGNORECASE)
           if matches:
               budget_info['fiscal_year_start'] = matches[0]
               break
       
       # Look for budget planning process
       budget_planning_patterns = [
           r'budget\s+(?:requests|planning|process)\s+(?:begins|starts)\s+(\d+)\s+months',
           r'capital\s+(?:requests|expenditures|planning)\s+(?:due|submitted|completed)\s+by\s+(\w+)'
       ]
       
       for pattern in budget_planning_patterns:
           matches = re.findall(pattern, all_content, re.IGNORECASE)
           if matches:
               budget_info['planning_timeframe'] = matches[0]
               break
       
       # If nothing found, infer based on facility type
       facility_types = ["hospital", "imaging center", "academic", "govt"]
       facility_type = None
       
       for type_name in facility_types:
           if type_name in all_content.lower():
               facility_type = type_name
               break
       
       if 'fiscal_year_start' not in budget_info:
           if facility_type == "hospital" or facility_type == "academic":
               budget_info['fiscal_year_start'] = "July"
           elif facility_type == "govt":
               budget_info['fiscal_year_start'] = "October"
           else:
               budget_info['fiscal_year_start'] = "January"  # Default for most businesses
       
       if 'planning_timeframe' not in budget_info:
           if facility_type == "hospital" or facility_type == "academic":
               budget_info['planning_timeframe'] = "3-4 months before fiscal year start"
           elif facility_type == "govt":
               budget_info['planning_timeframe'] = "6-9 months before fiscal year start"
           else:
               budget_info['planning_timeframe'] = "2-3 months before fiscal year start"
       
       return budget_info
   
   def identify_technology_refresh_cycle(self, pages_data):
       """Identify technology refresh cycle patterns"""
       refresh_indicators = []
       
       refresh_terms = [
           'refresh', 'upgrade', 'replace', 'update', 'modernize',
           'new system', 'implementation', 'migration'
       ]
       
       technology_terms = [
           'system', 'pacs', 'ris', 'equipment', 'workstation', 'server',
           'infrastructure', 'software', 'hardware'
       ]
       
       time_terms = [
           'years', 'annually', 'cycle', 'schedule', 'phase'
       ]
       
       for page in pages_data:
           if not page:
               continue
           
           content = page.get('content', '').lower()
           
           # Look for sentences containing refresh terms and technology terms
           sentences = re.split(r'(?<=[.!?])\s+', content)
           for sentence in sentences:
               if (any(term in sentence for term in refresh_terms) and 
                   any(term in sentence for term in technology_terms) and
                   any(term in sentence for term in time_terms)):
                   
                   # Look for numbers that might indicate cycle years
                   years_match = re.search(r'(\d+)[\s-]*year', sentence)
                   years = years_match.group(1) if years_match else "Unknown"
                   
                   refresh_indicators.append({
                       "cycle_years": years,
                       "context": sentence.strip(),
                       "page": page['url']
                   })
       
       # If no explicit indicators found, make inference based on equipment age mentions
       if not refresh_indicators:
           age_patterns = [
               r'(\d+)[\s-]*year[\s-]*old',
               r'installed (\d+) years ago',
               r'purchased (\d+) years ago'
           ]
           
           for page in pages_data:
               if not page:
                   continue
                   
               content = page.get('content', '').lower()
               for pattern in age_patterns:
                   matches = re.findall(pattern, content)
                   if matches:
                       try:
                           ages = [int(age) for age in matches]
                           avg_age = sum(ages) / len(ages)
                           refresh_indicators.append({
                               "inferred_cycle": f"Approximately {avg_age:.1f} years based on current equipment age mentions",
                               "source": "Age mentions in content"
                           })
                           break
                       except:
                           pass
                   
               if refresh_indicators:
                   break
       
       # If still no indicators, provide industry standard
       if not refresh_indicators:
           refresh_indicators.append({
               "inferred_cycle": "Typical 5-7 year cycle for healthcare imaging technology",
               "source": "Industry standard"
           })
       
       return refresh_indicators

   def extract_accreditation_information(self, pages_data):
       """Extract accreditation and certification information"""
       accreditations = []
       
       accreditation_orgs = [
           'ACR', 'American College of Radiology', 'Joint Commission', 'JCAHO',
           'IAC', 'Intersocietal Accreditation Commission', 'FDA', 'Food and Drug',
           'CAP', 'College of American Pathologists', 'AIUM', 'American Institute of Ultrasound in Medicine'
       ]
       
       for page in pages_data:
           if not page:
               continue
               
           content = page.get('content', '').lower()
           
           for org in accreditation_orgs:
               if org.lower() in content:
                   # Extract sentences containing the accreditation mention
                   sentences = re.split(r'(?<=[.!?])\s+', content)
                   for sentence in sentences:
                       if org.lower() in sentence.lower():
                           # Look for date information
                           year_match = re.search(r'(20\d\d)', sentence)
                           year = year_match.group(1) if year_match else None
                           
                           accreditations.append({
                               "organization": org,
                               "year": year,
                               "context": sentence.strip(),
                               "page": page['url']
                           })
       
       return accreditations
   
   def scrape_website(self, url, max_pages=15):
       """Main method to scrape a healthcare website"""
       clean_url = self.clean_url(url)
       base_url = self.get_base_url(clean_url)
       
       # Build target URLs to scan
       target_urls = self.build_target_urls(base_url)
       
       # Limit to max_pages
       target_urls = target_urls[:max_pages]
       
       logger.info(f"Scanning {len(target_urls)} pages from {base_url}")
       
       # Initialize results structure
       website_data = {
           "url": clean_url,
           "base_url": base_url,
           "domain": urlparse(base_url).netloc,
           "pages_scanned": 0,
           "scan_timestamp": None,
           "page_title": "",
           "meta_description": "",
           "pages_data": [],
           "key_personnel": [],
           "technology_stack": {},
           "growth_indicators": [],
           "pain_points": [],
           "term_counts": {},
           "emails_found": [],
           "job_openings": [],
           "location_count": 0,
           "equipment_information": [],
           "annual_study_volume": 0,
           "competitor_information": [],
           "technology_implementation_dates": [],
           "technology_refresh_cycle": [],
           "budget_cycle_info": {},
           "accreditations": [],
           "error": None
       }
       
       # Scrape pages in parallel
       pages_html = {}
       pages_data = []
       
       try:
           with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
               # Map URLs to future results
               future_to_url = {executor.submit(self.scrape_page, url): url for url in target_urls}
               
               for future in concurrent.futures.as_completed(future_to_url):
                   url = future_to_url[future]
                   try:
                       html = future.result()
                       if html:
                           pages_html[url] = html
                   except Exception as exc:
                       logger.error(f"{url} generated an exception: {exc}")
           
           # Process HTML into structured data
           for url, html in pages_html.items():
               page_data = self.extract_page_data(html, url)
               if page_data:
                   pages_data.append(page_data)
           
           # Save pages_data for use in other methods
           self.pages_data = pages_data
           
           # Set basic site info from homepage
           if pages_data and pages_data[0]['url'] == target_urls[0]:
               website_data['page_title'] = pages_data[0]['title']
               website_data['meta_description'] = pages_data[0]['meta_description']
           
           # Analyze all the collected data
           all_content = " ".join([page.get('content', '') for page in pages_data])
           
           # Count terms by category
           term_counts = {}
           for category, terms in self.healthcare_it_terms.items():
               category_counts = {}
               for term in terms:
                   count = all_content.lower().count(term)
                   if count > 0:
                       category_counts[term] = count
               term_counts[category] = category_counts
           
           # Collect all emails
           all_emails = []
           for page in pages_data:
               all_emails.extend(page.get('emails', []))
           
           # Collect job listings
           all_jobs = []
           for page in pages_data:
               all_jobs.extend(page.get('job_listings', []))
           
           # Extract enhanced information
           location_count = self.extract_location_count(pages_data)
           equipment_info = self.extract_equipment_information(pages_data)
           annual_study_volume = self.extract_annual_study_volume(pages_data)
           competitors = self.identify_regional_competitors(website_data.get('page_title', ''), 
                                                          website_data.get('domain', ''))
           tech_implementation = self.extract_technology_implementation_dates(pages_data)
           refresh_cycle = self.identify_technology_refresh_cycle(pages_data)
           budget_info = self.analyze_budget_cycle(pages_data)
           accreditations = self.extract_accreditation_information(pages_data)
           
           # Fill in the results
           website_data['pages_scanned'] = len(pages_data)
           website_data['pages_data'] = pages_data
           website_data['key_personnel'] = self.find_key_personnel(pages_data)
           website_data['technology_stack'] = self.analyze_tech_stack(pages_data)
           website_data['growth_indicators'] = self.identify_growth_indicators(pages_data)
           website_data['pain_points'] = self.identify_pain_points(pages_data)
           website_data['term_counts'] = term_counts
           website_data['emails_found'] = list(set(all_emails))  # Remove duplicates
           website_data['job_openings'] = list(set(all_jobs))  # Remove duplicates
           
           # Add enhanced information
           website_data['location_count'] = location_count
           website_data['equipment_information'] = equipment_info
           website_data['annual_study_volume'] = annual_study_volume
           website_data['competitor_information'] = competitors
           website_data['technology_implementation_dates'] = tech_implementation
           website_data['technology_refresh_cycle'] = refresh_cycle
           website_data['budget_cycle_info'] = budget_info
           website_data['accreditations'] = accreditations
           
           # Add summary metrics
           website_data['radiology_mentions'] = sum(term_counts.get('imaging_terms', {}).values())
           website_data['pacs_mentions'] = sum(term_counts.get('pacs_terms', {}).values())
           website_data['dicom_mentions'] = all_content.lower().count('dicom')
           website_data['workflow_mentions'] = sum(term_counts.get('workflow_terms', {}).values())
           website_data['modernization_mentions'] = sum(term_counts.get('modernization_terms', {}).values())
           
           # Flag if key pain points exist
           website_data['has_integration_pain_points'] = any('integration' in p['context'].lower() for p in website_data['pain_points'])
           website_data['has_workflow_pain_points'] = any('workflow' in p['context'].lower() for p in website_data['pain_points'])
           website_data['has_legacy_system_pain_points'] = any(term in p['context'].lower() for p in website_data['pain_points'] for term in ['legacy', 'outdated', 'obsolete'])
           
           import datetime
           website_data['scan_timestamp'] = datetime.datetime.now().isoformat()
           
       except Exception as e:
           website_data["error"] = str(e)
           logger.error(f"Error scraping {url}: {str(e)}")
       
       # Clean up - remove HTML to avoid bloating the results
       for page in website_data['pages_data']:
           if 'html' in page:
               del page['html']
       
       return website_data