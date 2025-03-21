import streamlit as st
import pandas as pd
import os
import time
import json
import datetime
import traceback
import logging
import re
from crewai import Crew, Process, Agent, Task
import sqlite3

# Import enhanced components
from product_knowledge import ProductKnowledge
from enhanced_website_scraper import EnhancedWebsiteScraper
from improved_flux_agents import create_enhanced_flux_agents
from improved_flux_tasks import create_enhanced_flux_tasks
from apollo_client import ApolloClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_database():
    """Initialize the SQLite database for storing playbooks"""
    try:
        # Create database directory if it doesn't exist
        db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db")
        os.makedirs(db_dir, exist_ok=True)
        
        # Connect to database
        db_path = os.path.join(db_dir, "flux_playbooks.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Create table if it doesn't exist
        c.execute('''
        CREATE TABLE IF NOT EXISTS playbooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            facility_name TEXT,
            facility_location TEXT,
            target_products TEXT,
            summary TEXT,
            full_playbook TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        
        return db_path
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        # Return a default path that will be used for error handling later
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "flux_playbooks.db")

def save_playbook_to_db(db_path, facility_name, facility_location, target_products, results):
    """Save generated playbook to SQLite database"""
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        timestamp = datetime.datetime.now().isoformat()
        
        # Get a summary from the complete playbook section (first 300 chars)
        complete_playbook = results.get("complete_playbook", "")
        summary = complete_playbook[:300] + "..." if len(complete_playbook) > 300 else complete_playbook
        
        # Convert target products list to string
        if isinstance(target_products, list):
            target_products_str = ", ".join(target_products)
        else:
            target_products_str = str(target_products)
            
        # Convert full results to JSON string
        full_playbook = json.dumps(results)
        
        # Insert into database
        c.execute("""
        INSERT INTO playbooks 
        (timestamp, facility_name, facility_location, target_products, summary, full_playbook) 
        VALUES (?, ?, ?, ?, ?, ?)
        """, (timestamp, facility_name, facility_location, target_products_str, summary, full_playbook))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error saving playbook to database: {str(e)}")
        return False

def search_playbooks(db_path, search_term):
    """Search playbooks in database by facility name or location"""
    try:
        conn = sqlite3.connect(db_path)
        
        # Use parameterized query with LIKE for partial matches
        search_pattern = f"%{search_term}%"
        query = """
        SELECT id, timestamp, facility_name, facility_location, target_products, summary 
        FROM playbooks 
        WHERE facility_name LIKE ? OR facility_location LIKE ?
        ORDER BY timestamp DESC
        """
        
        playbooks = pd.read_sql(query, conn, params=(search_pattern, search_pattern))
        conn.close()
        return playbooks
    except Exception as e:
        logger.error(f"Error searching playbooks: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error

def admin_page(db_path):
    """Admin page to view saved playbooks"""
    st.title("📊 Saved Playbooks")
    
    # Password protection
    password = st.text_input("Admin Password", type="password")
    correct_password = "flux2025"  # Change this to your preferred password
    
    if password != correct_password:
        st.warning("Enter password to view saved playbooks")
        return
    
    try:
        # Add search functionality
        st.subheader("Search Playbooks")
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            search_term = st.text_input("Search by facility name or location:", placeholder="Enter search term...")
        
        with col2:
            search_button = st.button("🔍 Search", use_container_width=True)
            
        with col3:
            clear_button = st.button("❌ Clear", use_container_width=True)
        
        # Load playbooks from database
        if search_button and search_term:
            # Search for playbooks matching term
            playbooks = search_playbooks(db_path, search_term)
            if len(playbooks) == 0:
                st.info(f"No playbooks found matching '{search_term}'.")
        elif clear_button:
            # Clear search term and reload all playbooks
            search_term = ""
            conn = sqlite3.connect(db_path)
            query = """
            SELECT id, timestamp, facility_name, facility_location, target_products, summary 
            FROM playbooks 
            ORDER BY timestamp DESC
            """
            playbooks = pd.read_sql(query, conn)
            conn.close()
        else:
            # Default: load all playbooks
            conn = sqlite3.connect(db_path)
            query = """
            SELECT id, timestamp, facility_name, facility_location, target_products, summary 
            FROM playbooks 
            ORDER BY timestamp DESC
            """
            playbooks = pd.read_sql(query, conn)
            conn.close()
        
        if len(playbooks) == 0:
            st.info("No playbooks saved yet.")
            return
            
        # Display saved playbooks
        st.subheader(f"Saved Playbooks ({len(playbooks)} found)")
        
        # Format the dataframe for display
        playbooks['timestamp'] = pd.to_datetime(playbooks['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        display_df = playbooks[['id', 'timestamp', 'facility_name', 'facility_location', 'target_products']]
        display_df.columns = ['ID', 'Date', 'Facility', 'Location', 'Products']
        
        st.dataframe(display_df, use_container_width=True)
        
        # View full playbook
        col1, col2 = st.columns([1, 1])
        
        with col1:
            playbook_id = st.number_input("Enter ID to view", min_value=1, max_value=int(playbooks['id'].max()) if len(playbooks) > 0 else 1, step=1)
        
        with col2:
            view_button = st.button("View Playbook", type="primary", use_container_width=True)
        
        if view_button:
            # Get the selected playbook
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT full_playbook, facility_name FROM playbooks WHERE id = ?", (playbook_id,))
            result = c.fetchone()
            conn.close()
            
            if result:
                full_playbook, facility_name = result
                playbook_data = json.loads(full_playbook)
                
                # Display tabs for different sections
                st.markdown(f"### Playbook for {facility_name}")
                
                tabs = st.tabs([
                    "Facility Details",
                    "Stakeholder Ecosystem",
                    "Industry Research",
                    "Website Intelligence", 
                    "Deal Qualification", 
                    "Value Propositions", 
                    "ROI Analysis", 
                    "Personalized Emails", 
                    "Objection Handling",
                    "Complete Playbook"
                ])
                
                with tabs[0]:
                    st.markdown("### Inferred Facility Details")
                    inferred_details = playbook_data.get("inferred_facility_details", {})
                    st.json(inferred_details)
                
                with tabs[1]:
                    st.markdown("### Stakeholder Ecosystem Map")
                    st.markdown(playbook_data.get("stakeholder_ecosystem", "No data available"))
                
                with tabs[2]:
                    st.markdown("### Industry Research")
                    st.markdown(playbook_data.get("industry_research", "No data available"))
                
                with tabs[3]:
                    st.markdown("### Website Intelligence Analysis")
                    st.markdown(playbook_data.get("website_intelligence", "No data available"))
                
                with tabs[4]:
                    st.markdown("### Opportunity Qualification")
                    st.markdown(playbook_data.get("deal_qualification", "No data available"))
                
                with tabs[5]:
                    st.markdown("### Value Propositions")
                    st.markdown(playbook_data.get("value_propositions", "No data available"))
                
                with tabs[6]:
                    st.markdown("### ROI Analysis")
                    st.markdown(playbook_data.get("roi_analysis", "No data available"))
                
                with tabs[7]:
                    st.markdown("### Personalized Email Templates")
                    st.markdown(playbook_data.get("personalized_emails", "No data available"))
                
                with tabs[8]:
                    st.markdown("### Objection Handling Guide")
                    st.markdown(playbook_data.get("objection_handling", "No data available"))
                
                with tabs[9]:
                    st.markdown("### Complete Sales Playbook")
                    st.markdown(playbook_data.get("complete_playbook", "No data available"))
                
                # Add download options
                col1, col2 = st.columns(2)
                
                with col1:
                    st.download_button(
                        label="Download as JSON",
                        data=full_playbook,
                        file_name=f"{facility_name.replace(' ', '_')}_Sales_Package.json",
                        mime="application/json"
                    )
                
                with col2:
                    # Create a markdown version
                    markdown_content = f"""# Flux Sales Package: {facility_name}
                    
## Inferred Facility Details
{playbook_data.get("inferred_facility_details", "No data available")}

## Stakeholder Ecosystem Map
{playbook_data.get("stakeholder_ecosystem", "No data available")}

## Industry Research
{playbook_data.get("industry_research", "No data available")}

## Website Intelligence Analysis
{playbook_data.get("website_intelligence", "No data available")}

## Opportunity Qualification
{playbook_data.get("deal_qualification", "No data available")}

## Value Propositions
{playbook_data.get("value_propositions", "No data available")}

## ROI Analysis
{playbook_data.get("roi_analysis", "No data available")}

## Personalized Email Templates
{playbook_data.get("personalized_emails", "No data available")}

## Objection Handling Guide
{playbook_data.get("objection_handling", "No data available")}

## Complete Sales Playbook
{playbook_data.get("complete_playbook", "No data available")}
                    """
                    
                    st.download_button(
                        label="Download as Markdown",
                        data=markdown_content,
                        file_name=f"{facility_name.replace(' ', '_')}_Sales_Package.md",
                        mime="text/markdown"
                    )
            else:
                st.error("Playbook not found")
                
    except Exception as e:
        st.error(f"Error loading playbooks: {str(e)}")
        if "no such table: playbooks" in str(e):
            st.info("Database exists but playbooks table not found. It will be created when you save your first playbook.")

class FluxSalesAccelerator:
    """
    Enhanced Flux Sales Accelerator with detailed product knowledge,
    improved website intelligence, and powerful sales content generation.
    """
    
    def __init__(self, api_key=None, model="gpt-4-turbo"):
        self.api_key = api_key
        self.model = model
        self.product_knowledge = ProductKnowledge()
        self.website_scraper = EnhancedWebsiteScraper()

    def get_product_use_cases(self, target_products):
        """Get detailed use cases for the target products"""
        use_cases = {}
        for product in target_products:
            product_info = self.product_knowledge.get_product_info(product)
            if product_info and 'use_cases' in product_info:
                use_cases[product] = product_info['use_cases']
        return use_cases
        
    def set_api_key(self, api_key):
        """Set OpenAI API key"""
        self.api_key = api_key
        os.environ["OPENAI_API_KEY"] = api_key
    
    def scrape_website(self, url):
        """Scrape website for enhanced intelligence"""
        if not url:
            return None
        
        # Clean the URL by stripping whitespace
        clean_url = url.strip()
        return self.website_scraper.scrape_website(clean_url)
    
    def parse_agent_output(self, output_str):
        """
        Parse agent output to extract properly formatted JSON
        """
        # Try direct JSON parsing first
        try:
            return json.loads(output_str)
        except json.JSONDecodeError:
            # Try to extract JSON with regex
            try:
                json_match = re.search(r'({[\s\S]*})', output_str)
                if json_match:
                    return json.loads(json_match.group(1))
            except:
                pass
            
            # Try to extract the JSON after "Final Answer:" if present
            try:
                if "Final Answer:" in output_str:
                    answer_part = output_str.split("Final Answer:")[1].strip()
                    return json.loads(answer_part)
            except:
                pass
                
            # Manually parse as last resort
            result = {}
            try:
                # Extract field values with regex
                for field in ["name", "location", "type", "size", "current_infrastructure", 
                            "key_challenge", "recent_events", "budget_cycle"]:
                    match = re.search(fr'"{field}":\s*"([^"]+)"', output_str)
                    if match:
                        result[field] = match.group(1)
                
                # Extract pain points array
                pain_points_match = re.search(r'"pain_points":\s*\[(.*?)\]', output_str, re.DOTALL)
                if pain_points_match:
                    points_str = pain_points_match.group(1)
                    result["pain_points"] = [p.strip(' "') for p in points_str.split(',')]
                
                return result
            except Exception as e:
                logger.error(f"Failed to manually parse agent output: {e}")
                return {"error": "Failed to parse output", "raw": output_str[:500]}

    def infer_facility_details(self, basic_details):
        """Only infer facility details without generating the full package"""
        # Verify API key is set
        if not self.api_key and "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OpenAI API key is not set. Please provide a valid API key.")
        elif self.api_key:
            os.environ["OPENAI_API_KEY"] = self.api_key

        # Create agents with API key
        agents = create_enhanced_flux_agents(model=self.model, api_key=self.api_key)
        
        # Create just the inference task
        facility_inference_task = Task(
            description=f"""
            Infer detailed facility information based on the following basic details:
            {json.dumps(basic_details, indent=2)}
            
            CRITICAL: Your response MUST be a valid JSON object with EXACTLY this structure:
            {{
                "name": "Facility Name",
                "location": "City, State",
                "type": "Facility Type",
                "size": "X locations, Y studies annually",
                "current_infrastructure": "Description of systems",
                "pain_points": ["Point 1", "Point 2", "Point 3"],
                "key_challenge": "Primary challenge",
                "recent_events": "Recent event",
                "budget_cycle": "Budget cycle info"
            }}
            
            DO NOT include nested objects.
            DO NOT include 'Final Answer:' or any other text.
            DO NOT use markdown formatting.
            ONLY return the JSON object.
            """,
            expected_output="A structured dictionary containing inferred facility details.",
            agent=agents["facility_inference_specialist"]
        )
        
        # Execute only this single task
        output = agents["facility_inference_specialist"].execute_task(facility_inference_task)
        
        # Parse the output
        inferred_details = self.parse_agent_output(output)
        
        return inferred_details
    
    def generate_sales_package(self, facility_details, website_url=None, target_products=None, csv_data=None, apollo_data=None, skip_inference=False):
        """Generate complete sales acceleration package"""
        
        # Verify API key is set
        if not self.api_key and "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OpenAI API key is not set. Please provide a valid API key.")
        elif self.api_key:
            os.environ["OPENAI_API_KEY"] = self.api_key
        
        # Initialize results
        results = {
            "timestamp": datetime.datetime.now().isoformat(),
            "facility_details": facility_details,
            "target_products": target_products,
            "website_url": website_url,
            "apollo_data": apollo_data,
            "inferred_facility_details": {},  # New field for inferred data
            "stakeholder_ecosystem": "",
            "industry_research": "",
            "website_intelligence": "",
            "deal_qualification": "",
            "value_propositions": "",
            "roi_analysis": "",
            "draft_communications": "",
            "personalized_emails": "",
            "objection_handling": "",
            "complete_playbook": ""
        }
        
        # Process website if URL provided
        website_data = None
        if website_url:
            try:
                website_data = self.scrape_website(website_url)
                
                # Add Apollo data to website data if available
                if apollo_data:
                    website_data = website_data or {}
                    website_data["apollo_data"] = apollo_data
                
                results["website_data"] = website_data
            except Exception as e:
                logger.error(f"Error scraping website {website_url}: {str(e)}")
                results["website_data"] = {"error": str(e)}
        
        # Create agents with API key
        try:
            agents = create_enhanced_flux_agents(model=self.model, api_key=self.api_key)
        except Exception as e:
            logger.error(f"Error creating agents: {str(e)}")
            raise ValueError(f"Failed to create agents: {str(e)}")
        
        # Create tasks
        try:
            tasks = create_enhanced_flux_tasks(agents, facility_details, website_data, target_products)
        except Exception as e:
            logger.error(f"Error creating tasks: {str(e)}")
            raise ValueError(f"Failed to create tasks: {str(e)}")
        
        # Execute tasks one by one to ensure we capture output of each task
        task_results = {}  # Store results in a dictionary instead of trying to modify Task objects
        
        # Skip inference if requested (when we already have inference results)
        if skip_inference:
            logger.info("Skipping facility inference task as requested")
            i_start = 1  # Start from the second task
        else:
            i_start = 0  # Start from the first task (inference)
        
        for i, task in enumerate(tasks):
            # Skip tasks before our starting point
            if i < i_start:
                continue
                
            if i == 0:  # Facility inference task (new first step)
                logger.info("Executing facility inference task")
                
                # Override the task description to enforce a specific output format
                task.description += """
                
                CRITICAL: Your response MUST be a valid JSON object with EXACTLY this structure:
                {
                    "name": "Facility Name",
                    "location": "City, State",
                    "type": "Facility Type",
                    "size": "X locations, Y studies annually",
                    "current_infrastructure": "Description of systems",
                    "pain_points": ["Point 1", "Point 2", "Point 3"],
                    "key_challenge": "Primary challenge",
                    "recent_events": "Recent event",
                    "budget_cycle": "Budget cycle info"
                }
                
                DO NOT include nested objects.
                DO NOT include 'Final Answer:' or any other text.
                DO NOT use markdown formatting.
                ONLY return the JSON object.
                """
                
                output = agents["facility_inference_specialist"].execute_task(task)
                logger.info(f"Raw agent output type: {type(output)}")
                logger.info(f"Raw agent output sample: {str(output)[:200]}...")
                
                try:
                    # Process the raw output with a format validation agent
                    validation_agent = Agent(
                        role="JSON Format Validator",
                        goal="Ensure output is properly formatted according to specifications",
                        backstory="""You are an expert in data validation and formatting. You take unstructured 
                        or improperly structured data and convert it into the exact required format. You excel 
                        at extracting key information and presenting it in a consistent, standardized way.""",
                        verbose=True,
                        allow_delegation=False,
                        llm=agents["facility_inference_specialist"].llm
                    )
                    
                    validation_task = Task(
                        description=f"""
                        Validate and correct the format of the following output: 
                        
                        {output}
                        
                        The output should be a valid JSON object with exactly this structure:
                        {{
                            "name": "Facility Name",
                            "location": "City, State",
                            "type": "Facility Type", 
                            "size": "X locations, Y studies annually",
                            "current_infrastructure": "Description of systems",
                            "pain_points": ["Point 1", "Point 2", "Point 3"],
                            "key_challenge": "Primary challenge",
                            "recent_events": "Recent event",
                            "budget_cycle": "Budget cycle info"
                        }}
                        
                        If the output is already in this format, simply return it.
                        If not, extract the information and reformat it to match this structure exactly.
                        If information for a field is missing, use an empty string or empty array as appropriate.
                        
                        Return ONLY the properly formatted JSON object without any additional text.
                        """,
                        expected_output="A properly formatted JSON object.",
                        agent=validation_agent
                    )
                    
                    # Execute the validation task
                    logger.info("Validating and reformatting inference output...")
                    validated_output = validation_agent.execute_task(validation_task)
                    logger.info(f"Validated output: {validated_output[:200]}...")
                    
                    # Now try to parse the validated output
                    try:
                        # Attempt to parse directly
                        inferred_facility_details = self.parse_agent_output(validated_output)
                    except json.JSONDecodeError:
                        # If it's still not valid JSON, try to extract JSON using regex
                        json_match = re.search(r'({[\s\S]*})', validated_output)
                        if json_match:
                            inferred_facility_details = json.loads(json_match.group(1))
                        else:
                            # Manual parsing as a last resort
                            inferred_facility_details = {}
                            # Extract field values
                            name_match = re.search(r'"name":\s*"([^"]+)"', validated_output)
                            if name_match:
                                inferred_facility_details["name"] = name_match.group(1)
                            
                            location_match = re.search(r'"location":\s*"([^"]+)"', validated_output)
                            if location_match:
                                inferred_facility_details["location"] = location_match.group(1)
                            
                            type_match = re.search(r'"type":\s*"([^"]+)"', validated_output)
                            if type_match:
                                inferred_facility_details["type"] = type_match.group(1)
                            
                            size_match = re.search(r'"size":\s*"([^"]+)"', validated_output)
                            if size_match:
                                inferred_facility_details["size"] = size_match.group(1)
                            
                            infra_match = re.search(r'"current_infrastructure":\s*"([^"]+)"', validated_output)
                            if infra_match:
                                inferred_facility_details["current_infrastructure"] = infra_match.group(1)
                            
                            pain_points_match = re.search(r'"pain_points":\s*\[(.*?)\]', validated_output, re.DOTALL)
                            if pain_points_match:
                                pain_points_str = pain_points_match.group(1)
                                pain_points = [p.strip(' "') for p in pain_points_str.split(',')]
                                inferred_facility_details["pain_points"] = pain_points
                            
                            challenge_match = re.search(r'"key_challenge":\s*"([^"]+)"', validated_output)
                            if challenge_match:
                                inferred_facility_details["key_challenge"] = challenge_match.group(1)
                            
                            events_match = re.search(r'"recent_events":\s*"([^"]+)"', validated_output)
                            if events_match:
                                inferred_facility_details["recent_events"] = events_match.group(1)
                            
                            budget_match = re.search(r'"budget_cycle":\s*"([^"]+)"', validated_output)
                            if budget_match:
                                inferred_facility_details["budget_cycle"] = budget_match.group(1)
                    
                    # Log the inferred details for debugging
                    logger.info(f"Inferred facility details: {inferred_facility_details}")
                    
                    # Process each field to ensure proper structure before updating
                    processed_details = {}
                    
                    # Handle name
                    if "name" in inferred_facility_details:
                        processed_details["name"] = inferred_facility_details["name"]
                    
                    # Handle location
                    if "location" in inferred_facility_details:
                        processed_details["location"] = inferred_facility_details["location"]
                    
                    # Handle type which might be a string or a dictionary
                    if "type" in inferred_facility_details:
                        if isinstance(inferred_facility_details["type"], dict):
                            if "facility_type" in inferred_facility_details["type"]:
                                processed_details["type"] = inferred_facility_details["type"]["facility_type"]
                            else:
                                # Use the first value in the dictionary if facility_type isn't present
                                first_value = next(iter(inferred_facility_details["type"].values()), "Unknown")
                                processed_details["type"] = first_value
                        else:
                            processed_details["type"] = inferred_facility_details["type"]
                    
                    # Handle size which might be a string or a dictionary
                    if "size" in inferred_facility_details:
                        if isinstance(inferred_facility_details["size"], dict):
                            size_str = ""
                            if "number_of_locations" in inferred_facility_details["size"]:
                                size_str += f"{inferred_facility_details['size']['number_of_locations']} locations, "
                            elif "locations" in inferred_facility_details["size"]:
                                size_str += f"{inferred_facility_details['size']['locations']} locations, "
                            
                            if "annual_studies" in inferred_facility_details["size"]:
                                size_str += f"{inferred_facility_details['size']['annual_studies']} studies annually"
                            
                            processed_details["size"] = size_str.strip(", ")
                        else:
                            processed_details["size"] = inferred_facility_details["size"]
                    
                    # Handle pain_points which might be a list or a string
                    if "pain_points" in inferred_facility_details:
                        if isinstance(inferred_facility_details["pain_points"], list):
                            processed_details["pain_points"] = inferred_facility_details["pain_points"]
                        else:
                            # Try to split string by newlines or commas if it's a string
                            pain_points_str = inferred_facility_details["pain_points"]
                            if "\n" in pain_points_str:
                                processed_details["pain_points"] = [p.strip() for p in pain_points_str.split("\n") if p.strip()]
                            elif "," in pain_points_str:
                                processed_details["pain_points"] = [p.strip() for p in pain_points_str.split(",") if p.strip()]
                            else:
                                processed_details["pain_points"] = [pain_points_str]
                    
                    # Handle other fields
                    for field in ["current_infrastructure", "key_challenge", "recent_events", "budget_cycle"]:
                        if field in inferred_facility_details:
                            if isinstance(inferred_facility_details[field], dict):
                                # Try to get sensible value from dictionary
                                first_key = next(iter(inferred_facility_details[field].keys()), None)
                                if first_key and first_key in ["value", "description", "text"]:
                                    processed_details[field] = inferred_facility_details[field][first_key]
                                else:
                                    # Just take the first value
                                    processed_details[field] = next(iter(inferred_facility_details[field].values()), "")
                            else:
                                processed_details[field] = inferred_facility_details[field]
                    
                    # Update facility_details with processed values
                    facility_details.update(processed_details)
                    
                    # Store both raw and processed details for reference
                    results["inferred_facility_details"] = inferred_facility_details
                    task_results["facility_inference"] = processed_details
                    
                    logger.info(f"Successfully inferred facility details for {facility_details.get('name', 'unknown facility')}")
                    
                    # Recreate tasks with updated facility details
                    tasks = create_enhanced_flux_tasks(agents, facility_details, website_data, target_products)
                
                except Exception as e:
                    logger.error(f"Error processing inference results: {str(e)}")
                    traceback.print_exc()
                    results["inferred_facility_details"] = {"error": str(e)}
                    # Continue with original facility details
                
                continue  # Skip to the next iteration to process the updated tasks
                
            elif i == 1:  # Stakeholder ecosystem mapping task (now index 1)
                try:
                    # Add Apollo contact data directly to task description if available
                    if apollo_data and 'contacts' in apollo_data and apollo_data['contacts']:
                        apollo_contacts_str = json.dumps(apollo_data['contacts'], indent=2)
                        task.description = task.description.replace("APOLLO CONTACT DATA:", 
                                                               f"APOLLO CONTACT DATA:\n{apollo_contacts_str}")
                    
                    output = agents["stakeholder_ecosystem_mapper"].execute_task(task)
                    results["stakeholder_ecosystem"] = output
                    task_results["stakeholder_ecosystem"] = output
                    logger.info("Completed stakeholder ecosystem mapping")
                except Exception as e:
                    logger.error(f"Error in stakeholder ecosystem mapping: {str(e)}")
                    results["stakeholder_ecosystem"] = f"Error generating stakeholder ecosystem map: {str(e)}"
            
            # Continue with the remaining tasks (industry_research, etc.)
            elif i == 2:
                try:
                    output = agents["industry_research_specialist"].execute_task(task)
                    results["industry_research"] = output
                    task_results["industry_research"] = output
                    logger.info("Completed industry research")
                except Exception as e:
                    logger.error(f"Error in industry research: {str(e)}")
                    results["industry_research"] = f"Error generating industry research: {str(e)}"
                    
            elif i == 3:
                try:
                    output = agents["website_intelligence_analyst"].execute_task(task)
                    results["website_intelligence"] = output
                    task_results["website_intelligence"] = output
                    logger.info("Completed website intelligence analysis")
                except Exception as e:
                    logger.error(f"Error in website intelligence analysis: {str(e)}")
                    results["website_intelligence"] = f"Error generating website intelligence: {str(e)}"
                    
            elif i == 4:  # Deal qualification task
                try:
                    output = agents["deal_qualifier"].execute_task(task)
                    # NEW CODE: Extract only the final answer
                    if "Final Answer:" in output:
                        final_answer = output.split("Final Answer:")[1].strip()
                    elif "```" in output and "Final Answer" in output:
                        import re
                        match = re.search(r'```.*?Final Answer:?(.*?)```', output, re.DOTALL)
                        final_answer = match.group(1).strip() if match else output
                    else:
                        
                        import re
                        final_answer = re.sub(r'Thought:.*?(Do I need to use a tool\?.*?)(.*)', r'\2', output, flags=re.DOTALL)
                    results["deal_qualification"] = final_answer
                    task_results["deal_qualification"] = final_answer
                    logger.info("Completed deal qualification")
                except Exception as e:
                    logger.error(f"Error in deal qualification: {str(e)}")
                    results["deal_qualification"] = f"Error generating deal qualification: {str(e)}"
                    
            elif i == 5:
                try:
                    output = agents["technical_value_strategist"].execute_task(task)
                    results["value_propositions"] = output
                    task_results["value_propositions"] = output
                    logger.info("Completed value propositions")
                except Exception as e:
                    logger.error(f"Error in value propositions: {str(e)}")
                    results["value_propositions"] = f"Error generating value propositions: {str(e)}"
                    
            elif i == 6:  # ROI analysis task
                try:
                    output = agents["financial_roi_expert"].execute_task(task)
                    # Extract only the final answer
                    if "Final Answer:" in output:
                        final_answer = output.split("Final Answer:")[1].strip()
                    elif "```" in output and "Final Answer" in output:
                        import re
                        match = re.search(r'```.*?Final Answer:?(.*?)```', output, re.DOTALL)
                        final_answer = match.group(1).strip() if match else output
                    else:
                        # Remove thought process
                        import re
                        final_answer = re.sub(r'Thought:.*?(Do I need to use a tool\?.*?)(.*)', r'\2', output, flags=re.DOTALL)
                    results["roi_analysis"] = final_answer
                    task_results["roi_analysis"] = final_answer
                    logger.info("Completed ROI analysis")
                except Exception as e:
                    logger.error(f"Error in ROI analysis: {str(e)}")
                    results["roi_analysis"] = f"Error generating ROI analysis: {str(e)}"
                    
            elif i == 7:
                try:
                    output = agents["relationship_advisor"].execute_task(task)
                    results["draft_communications"] = output
                    task_results["draft_communications"] = output
                    logger.info("Completed relationship building communications")
                except Exception as e:
                    logger.error(f"Error in relationship building: {str(e)}")
                    results["draft_communications"] = f"Error generating communications: {str(e)}"
                    
            elif i == 8:
                try:
                    # Add all previous outputs to review task context
                    for key, value in task_results.items():
                        placeholder = f"[{key.replace('_', ' ').title()}]"
                        # Convert any non-string values to strings before using replace()
                        if not isinstance(value, str):
                            # Format as JSON string if it's a dictionary or list
                            value = json.dumps(value, indent=2)
                        task.description = task.description.replace(placeholder, value)
                        
                    output = agents["strategic_reviewer"].execute_task(task)
                    results["personalized_emails"] = output
                    task_results["personalized_emails"] = output
                    logger.info("Completed communication review")
                except Exception as e:
                    logger.error(f"Error in communication review: {str(e)}")
                    results["personalized_emails"] = f"Error generating personalized emails: {str(e)}"
                    
            elif i == 9:
                try:
                    output = agents["objection_specialist"].execute_task(task)
                    results["objection_handling"] = output
                    task_results["objection_handling"] = output
                    logger.info("Completed objection handling")
                except Exception as e:
                    logger.error(f"Error in objection handling: {str(e)}")
                    results["objection_handling"] = f"Error generating objection handling: {str(e)}"
                    
            elif i == 10:
                try:
                    output = agents["deal_qualifier"].execute_task(task)
                    results["complete_playbook"] = output
                    task_results["complete_playbook"] = output
                    logger.info("Completed sales playbook")
                except Exception as e:
                    logger.error(f"Error in sales playbook: {str(e)}")
                    results["complete_playbook"] = f"Error generating sales playbook: {str(e)}"
                
        return results

class FluxSalesAcceleratorApp:
    """
    Streamlit app for the enhanced Flux Sales Accelerator
    """
    
    def __init__(self):
        """Initialize the Flux Sales Accelerator App with Apollo integration"""
        # Set page configuration with sidebar + database
        st.set_page_config(page_title="Flux Sales Accelerator", layout="wide", initial_sidebar_state="expanded")
        self.db_path = setup_database()
        
        # Initialize session state variables if not already set
        if 'inference_status' not in st.session_state:
            st.session_state['inference_status'] = 'not_started'
        if 'auto_generate' not in st.session_state:
            st.session_state['auto_generate'] = False
        if 'last_inference_time' not in st.session_state:
            st.session_state['last_inference_time'] = None
        if 'show_admin' not in st.session_state:
            st.session_state['show_admin'] = False
        
        # Initialize default facility attributes FIRST to avoid AttributeError
        self.facility_name = "Metropolitan Imaging Center"
        self.website_url = "www.nm.org"
        self.location = "Chicago, IL"
        self.facility_type = "Multi-specialty outpatient imaging center"
        self.size = "3 locations, 45,000 studies annually"
        self.budget_cycle = "Fiscal year begins July 1, capital requests due by March 15"
        self.current_infrastructure = "GE PACS (7 years old), Siemens and Philips modalities"
        self.key_challenge = "Slow image retrieval, limited remote access capabilities"
        self.recent_events = "New radiologist leadership hired, considering workflow modernization"
        self.pain_points = "17-minute average retrieval time for prior studies\nNo tablet/mobile viewing capabilities\nLimited integration with referring physician EMRs\nManual CD importing process taking 2 FTE staff\nMultiple disconnected DICOM workflows between locations"
        self.target_products = ["DICOM Printer 2"]  # Default selection
        
        # Initialize the accelerator
        self.accelerator = FluxSalesAccelerator()
        
        # Initialize class variables for CSV data
        self.name_col = ""
        self.title_col = ""
        self.company_col = ""
        self.email_col = ""
        self.phone_col = ""
        self.industry_col = ""
        self.contacts_df = None
        
        # Set default API keys
        self.api_key = ""
        self.apollo_api_key = ""
        self.model = "gpt-4"
        
        # Setup sidebar first
        self.setup_sidebar()
        
        # Title and description
        st.title("Flux Sales Accelerator")
        st.markdown("Generate high-converting sales materials for your Flux DICOM products")
        
        # Add a debug panel if needed
        if os.environ.get('DEBUG', 'false').lower() == 'true':
            with st.expander("Debug Info", expanded=False):
                st.write("Session State Keys:", list(st.session_state.keys()))
                st.write("Inference Status:", st.session_state.get('inference_status', 'not_started'))
                st.write("Auto Generate Flag:", st.session_state.get('auto_generate', False))
                if 'inferred_details' in st.session_state:
                    st.write("Inferred Details:", st.session_state['inferred_details'])
        
        # Apollo Search Section (comes first for better workflow)
        self.apollo_search_section()
        
        # Main form for facility details
        self.facility_form()
        
        # Manual Contact Upload Section (no longer conditional on Apollo)
        self.contact_upload()
        
        # Generate button
        self.generate_button()
        
        # Check for auto-generation trigger
        if st.session_state.get('auto_generate', False):
            logger.info("Auto-generation flag detected!")
            # This will be handled in the generate_button method

    def validate_website_url(self, company_name, website_url):
        """
        Use an agent to validate that the website URL matches the company
        
        Args:
            company_name (str): The company name to validate against
            website_url (str): The website URL to validate
            
        Returns:
            dict: Validation results with status and any issues found
        """
        if not website_url or not company_name:
            return {"valid": False, "reason": "Missing company name or website URL"}
        
        # Clean the URL
        clean_url = website_url.strip()
        if not clean_url.startswith("http"):
            clean_url = "https://" + clean_url
        
        # Try to access the website
        try:
            from urllib.request import urlopen
            from urllib.error import URLError
            
            # First check if the URL is accessible
            try:
                response = urlopen(clean_url, timeout=5)
                if response.status != 200:
                    return {"valid": False, "reason": f"Website returned status code {response.status}"}
            except URLError as e:
                return {"valid": False, "reason": f"Could not access website: {str(e)}"}
            
            # If accessible, create a validation agent
            if self.api_key:
                os.environ["OPENAI_API_KEY"] = self.api_key
                
                # Create a specialized agent for website validation
                from crewai import Agent, Task
                from langchain.chat_models import ChatOpenAI
                
                llm = ChatOpenAI(model_name=self.model, temperature=0.5, openai_api_key=self.api_key)
                
                validation_agent = Agent(
                    role="Website Validation Specialist",
                    goal="Verify if a website belongs to the expected company",
                    backstory="""You are an expert at validating company websites to ensure
                    they match the expected company. You check for company name, industry relevance,
                    and other indicators that the website belongs to the expected organization.""",
                    verbose=True,
                    allow_delegation=False,
                    llm=llm
                )
                
                validation_task = Task(
                    description=f"""
                    Verify if the website {clean_url} belongs to the company "{company_name}".
                    Check for company name mentions, logos, industry relevance, and other indicators.
                    
                    TASKS:
                    1. Try to determine if this website actually belongs to {company_name}
                    2. Look for mentions of the company name or variations of it
                    3. Check if the website is relevant to the company's industry
                    4. Identify any red flags that might indicate this is the wrong website
                    
                    RESPONSE FORMAT:
                    Return a JSON object with the following structure:
                    {{
                        "valid": true/false,
                        "confidence": 0-100 (percentage),
                        "reason": "Explanation of your conclusion",
                        "company_mentions": "Where/how the company is mentioned, if found"
                    }}
                    """,
                    expected_output="JSON validation result",
                    agent=validation_agent
                )
                
                # Execute the validation task
                logger.info(f"Validating website {clean_url} for company {company_name}")
                result = validation_agent.execute_task(validation_task)
                
                # Parse the result
                try:
                    import json
                    import re
                    
                    # Try to extract JSON
                    json_match = re.search(r'({[\s\S]*})', result)
                    if json_match:
                        validation_result = json.loads(json_match.group(1))
                        return validation_result
                    else:
                        return {"valid": True, "reason": "Could not parse validation result, assuming valid"}
                except Exception as e:
                    logger.error(f"Error parsing validation result: {str(e)}")
                    return {"valid": True, "reason": "Error in validation, assuming valid"}
            else:
                return {"valid": True, "reason": "API key not set, skipping validation"}
        except Exception as e:
            logger.error(f"Error in website validation: {str(e)}")
            return {"valid": True, "reason": f"Error in validation: {str(e)}, assuming valid"}
    
    def setup_sidebar(self):
        """Setup sidebar with configuration options"""
        with st.sidebar:
            st.header("Configuration")
            
            # OpenAI API Key handling
            api_key = st.text_input("OpenAI API Key", value="", type="password")
            if api_key:
                self.api_key = api_key
                os.environ["OPENAI_API_KEY"] = api_key
                st.success("OpenAI API key set successfully!")
                
            # Apollo API Key handling
            apollo_api_key = st.text_input("Apollo API Key", value="", type="password")
            if apollo_api_key:
                self.apollo_api_key = apollo_api_key
                st.success("Apollo API key set successfully!")
            
            st.divider()
            st.header("Model Settings")
            self.model = st.selectbox("OpenAI Model", ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"], index=0)
            
            if st.button("Admin Access", type="secondary", use_container_width=True):
                st.session_state['show_admin'] = True
                st.rerun()
                
            st.divider()
            st.markdown("### About")
            st.markdown("This app generates targeted sales materials for Flux DICOM products using AI agents.")
            st.markdown("© 2025 Flux Inc. - Created by Rodrigo Tinajero")
            
            # Display inference status
            if st.session_state.get('inference_status') != 'not_started':
               st.info(f"Inference: {st.session_state.get('inference_status')}")
    
    def apollo_search_section(self):
        """Apollo.io integration for finding company data to auto-fill facility information"""
        with st.expander("Target Company Search with Apollo.io", expanded=True):
            # Debug info
            st.write(f"API Key exists: {bool(self.apollo_api_key)}")
            st.write(f"API Key length: {len(self.apollo_api_key) if self.apollo_api_key else 0}")
            
            # Check for Apollo API key in both instance variable and environment
            apollo_key = self.apollo_api_key or os.environ.get("APOLLO_API_KEY", "")
            
            if not apollo_key:
                st.warning("Please enter your Apollo API key in the sidebar to enable company search.")
                return
            
            # Initialize Apollo client with error handling
            try:
                apollo_client = ApolloClient(apollo_key)
                
                st.subheader("Find Organization")
                
                # Company search options
                search_option = st.radio(
                    "Search by:",
                    ["Domain/Website", "Company Name"],
                    horizontal=True
                )
                
                # Search input field
                if search_option == "Domain/Website":
                    default_value = self.website_url if hasattr(self, 'website_url') and self.website_url else ""
                    search_query = st.text_input("Company Website or Domain:", value=default_value)
                    
                    if search_query and ("http://" in search_query or "https://" in search_query):
                        from urllib.parse import urlparse
                        domain = urlparse(search_query).netloc
                        if domain.startswith("www."):
                            domain = domain[4:]
                        search_query = domain
                else:
                    default_value = self.facility_name if hasattr(self, 'facility_name') and self.facility_name else ""
                    search_query = st.text_input("Company Name:", value=default_value)
                
                # Search button
                col1, col2 = st.columns([3, 1])
                with col2:
                    search_clicked = st.button("Search Apollo", type="primary", use_container_width=True)
                
                if search_clicked and search_query:
                    st.session_state.pop('apollo_company_results', None)
                    st.session_state.pop('selected_company', None)
                    with st.spinner("Searching Apollo.io..."):
                        try:
                            if search_option == "Domain/Website":
                                try:
                                    # For debugging
                                    st.info(f"Searching for domain: {search_query}")
                                    results = apollo_client.enrich_domain(search_query)
                                    if "error" in results:
                                        st.error(f"Error from Apollo API: {results['error']}")
                                        return
                                    
                                    logger.info(f"Enrich domain result: {results}")
                                    if results.get("organization"):
                                        st.session_state['selected_company'] = results.get("organization")
                                        st.session_state['apollo_company_results'] = {"organizations": [results.get("organization")]}
                                    else:
                                        st.info("Domain enrichment didn't find an organization, trying organization search...")
                                        results = apollo_client.search_organizations(domain=search_query)
                                        if "error" in results:
                                            st.error(f"Error from Apollo API: {results['error']}")
                                            return
                                            
                                        if results.get('organizations'):
                                            st.session_state['apollo_company_results'] = results
                                            if len(results['organizations']) == 1:
                                                st.session_state['selected_company'] = results['organizations'][0]
                                        else:
                                            st.warning("No organizations found for this domain.")
                                except Exception as e:
                                    logger.error(f"Enrich failed: {str(e)}")
                                    st.error(f"Error enriching domain: {str(e)}")
                                    try:
                                        results = apollo_client.search_organizations(domain=search_query)
                                        if results.get('organizations'):
                                            st.session_state['apollo_company_results'] = results
                                            if len(results['organizations']) == 1:
                                                st.session_state['selected_company'] = results['organizations'][0]
                                    except Exception as e2:
                                        st.error(f"Error searching organizations: {str(e2)}")
                            else:
                                # For debugging
                                st.info(f"Searching for company name: {search_query}")
                                results = apollo_client.search_organizations(name=search_query)
                                if "error" in results:
                                    st.error(f"Error from Apollo API: {results['error']}")
                                    return
                                    
                                st.session_state['apollo_company_results'] = results
                                logger.info(f"Name search results: {len(results.get('organizations', []))} organizations found")
                        except Exception as e:
                            st.error(f"Error searching Apollo: {str(e)}")
            except Exception as e:
                st.error(f"Error initializing Apollo client: {str(e)}")
                return
            
            if 'apollo_company_results' in st.session_state:
                results = st.session_state['apollo_company_results']
                
                if results.get('organizations') and len(results['organizations']) > 0:
                    if len(results['organizations']) == 1 and 'selected_company' in st.session_state:
                        org = st.session_state['selected_company']
                        st.success(f"Found: **{org.get('name')}** | {org.get('website_url', 'N/A')}")
                    else:
                        st.subheader("Select Organization")
                        for i, org in enumerate(results['organizations']):
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.write(f"**{org.get('name')}** | {org.get('website_url', 'N/A')}")
                                st.write(f"Industry: {org.get('industry', 'Unknown')} | Size: {org.get('employee_count', 'Unknown')} employees")
                            with col2:
                                if st.button(f"Select", key=f"select_org_{i}"):
                                    st.session_state['selected_company'] = org
                                    logger.info(f"Selected organization ID: {org.get('id')}")
                                    
                                    # Update facility attributes
                                    self.facility_name = org.get('name', self.facility_name)
                                    
                                    # Explicitly set website URL from Apollo data
                                    website_url = org.get('website_url', '')
                                    if website_url:
                                        # Validate the website URL
                                        with st.spinner(f"Validating website {website_url}..."):
                                            validation_result = self.validate_website_url(org.get('name', ''), website_url)
                                            
                                            if validation_result.get("valid", True):
                                                # Website is valid
                                                self.website_url = website_url
                                                # Update session state for the website input field
                                                st.session_state["website_url_input"] = website_url
                                                
                                                # Show success message with confidence
                                                confidence = validation_result.get("confidence", 100)
                                                st.success(f"Website validated with {confidence}% confidence: {validation_result.get('reason', '')}")
                                            else:
                                                # Website validation failed
                                                st.warning(f"Website validation warning: {validation_result.get('reason', 'Unknown issue')}")
                                                # Still set the website URL but with a warning
                                                self.website_url = website_url
                                                st.session_state["website_url_input"] = website_url
                                                st.info("The website has been set but may not be correct. Please verify manually.")
                                    
                                    # Update location if available
                                    location_parts = []
                                    if org.get('location', {}).get('city'):
                                        location_parts.append(org.get('location', {}).get('city'))
                                    if org.get('location', {}).get('state'):
                                        location_parts.append(org.get('location', {}).get('state'))
                                    if location_parts:
                                        location_str = ', '.join(location_parts)
                                        self.location = location_str
                                        st.session_state["location_input"] = location_str
                                    
                                    # Update other session state fields
                                    st.session_state["facility_name_input"] = self.facility_name
                                    
                                    # Use rerun instead of experimental_rerun
                                    st.rerun()
                else:
                    st.warning("No organizations found. Try a different search term.")
            
            if 'selected_company' in st.session_state:
                st.markdown("---")
                st.subheader("Auto-Fill Facility Information")
                
                # Create a progress container to show real-time updates
                inference_progress_container = st.empty()
                
                col1, col2 = st.columns([3, 1])
                with col2:
                    infer_details = st.button("Infer Facility Details", type="primary", use_container_width=True)
                
                if infer_details:
                    # Set up UI elements to show real-time progress
                    inference_status = inference_progress_container.info("Starting inference process...")
                    
                    # Update session state
                    st.session_state['inference_status'] = 'in_progress'
                    st.session_state['inferred_details'] = {}
                    
                    try:
                        # Get the organization details
                        org = st.session_state['selected_company']
                        # Prepare basic facility details for inference
                        basic_details = {
                            "name": org.get('name', 'Unknown'),
                            "website_url": org.get('website_url', 'Unknown'),
                            "industry": org.get('industry', 'Unknown'),
                            "employee_count": org.get('employee_count', 'Unknown'),
                            "location": ""
                        }
                        # Add location if available
                        location_parts = []
                        if org.get('location', {}).get('city'):
                            location_parts.append(org.get('location', {}).get('city'))
                        if org.get('location', {}).get('state'):
                            location_parts.append(org.get('location', {}).get('state'))
                        if location_parts:
                            basic_details["location"] = ', '.join(location_parts)
                        
                        inference_status.info(f"Inferring details for {basic_details['name']}...")
                        
                        # Use the dedicated inference method instead of the full package generation
                        inferred_details = self.accelerator.infer_facility_details(basic_details)
                        
                        # Update session state for form fields
                        st.session_state["facility_name_input"] = inferred_details.get("name", org.get('name', 'Unknown'))
                        st.session_state["location_input"] = inferred_details.get("location", basic_details["location"])
                        
                        # Set facility type (with validation)
                        facility_type = inferred_details.get("type", "")
                        facility_types = ["Multi-specialty outpatient imaging center", "Hospital", "Radiology group", "Orthopedic center", "Dental practice"]
                        if facility_type in facility_types:
                            st.session_state["facility_type_input"] = facility_type
                        else:
                            # Try to find the closest match
                            for ft in facility_types:
                                if facility_type.lower() in ft.lower():
                                    st.session_state["facility_type_input"] = ft
                                    break
                        
                        # Update other fields
                        st.session_state["size_input"] = inferred_details.get("size", "")
                        st.session_state["infrastructure_input"] = inferred_details.get("current_infrastructure", "")
                        st.session_state["key_challenge_input"] = inferred_details.get("key_challenge", "")
                        st.session_state["recent_events_input"] = inferred_details.get("recent_events", "")
                        st.session_state["budget_cycle_input"] = inferred_details.get("budget_cycle", "")
                        
                        # Handle pain points
                        if "pain_points" in inferred_details:
                            pain_points = inferred_details["pain_points"]
                            if isinstance(pain_points, list):
                                st.session_state["pain_points_input"] = "\n".join(pain_points)
                            else:
                                st.session_state["pain_points_input"] = str(pain_points)
                        
                        # Save the inference results
                        st.session_state['inference_status'] = 'complete'
                        st.session_state['inferred_details'] = inferred_details
                        st.session_state['inference_results'] = {"inferred_facility_details": inferred_details}
                        
                        # Explicitly set auto_generate to False
                        st.session_state['auto_generate'] = False
                        
                        # Show success message
                        inference_status.success("✅ Facility details inferred! You can now review before generating.")
                        
                        # Force UI update
                        st.rerun()
                        
                    except Exception as e:
                        inference_status.error(f"Error inferring facility details: {str(e)}")
                        logger.error(f"Error inferring facility details: {str(e)}")
                        traceback.print_exc()
                        st.session_state['inference_status'] = 'error'
    
    def facility_form(self):
        """Display facility information form"""
        with st.expander("Target Facility Information (user may need to input some info manually)", expanded=True):
            # Initialize session state for form fields if not already set
            if "facility_name_input" not in st.session_state:
                st.session_state["facility_name_input"] = self.facility_name
            if "location_input" not in st.session_state:
                st.session_state["location_input"] = self.location
            if "facility_type_input" not in st.session_state:
                st.session_state["facility_type_input"] = self.facility_type
            if "target_products_input" not in st.session_state:
                st.session_state["target_products_input"] = self.target_products if isinstance(self.target_products, list) else [self.target_products]
            if "website_url_input" not in st.session_state:
                st.session_state["website_url_input"] = self.website_url
            if "size_input" not in st.session_state:
                st.session_state["size_input"] = self.size
            if "budget_cycle_input" not in st.session_state:
                st.session_state["budget_cycle_input"] = self.budget_cycle
            if "infrastructure_input" not in st.session_state:
                st.session_state["infrastructure_input"] = self.current_infrastructure
            if "key_challenge_input" not in st.session_state:
                st.session_state["key_challenge_input"] = self.key_challenge
            if "recent_events_input" not in st.session_state:
                st.session_state["recent_events_input"] = self.recent_events
            if "pain_points_input" not in st.session_state:
                st.session_state["pain_points_input"] = self.pain_points
            
            # Facility information form
            col1, col2 = st.columns(2)
            
            with col1:
                # Use only the key, not the value parameter
                self.facility_name = st.text_input(
                    "Facility Name", 
                    key="facility_name_input"
                )
                
                self.location = st.text_input(
                    "Location", 
                    key="location_input"
                )
                
                # Get facility types for selectbox
                facility_types = ["Multi-specialty outpatient imaging center", "Hospital", "Radiology group", "Orthopedic center", "Dental practice"]
                
                self.facility_type = st.selectbox(
                    "Facility Type", 
                    facility_types,
                    key="facility_type_input"
                )
                
                self.target_products = st.multiselect(
                    "Target Products", 
                    ["DICOM Printer 2", "Capacitor", "TuPACS", "Gobbler"],
                    key="target_products_input"
                )
                
                self.website_url = st.text_input(
                    "Facility Website URL", 
                    key="website_url_input"
                )
            
            with col2:
                self.size = st.text_input(
                    "Size (locations/studies)", 
                    key="size_input"
                )
                self.budget_cycle = st.text_input(
                    "Budget Cycle", 
                    key="budget_cycle_input"
                )
                self.current_infrastructure = st.text_area(
                    "Current Infrastructure", 
                    key="infrastructure_input"
                )
                
            self.key_challenge = st.text_area(
                "Key Challenge", 
                key="key_challenge_input"
            )
            self.recent_events = st.text_area(
                "Recent Events", 
                key="recent_events_input"
            )
            
            st.subheader("Current Pain Points")
            self.pain_points = st.text_area(
                "Pain Points (one per line)", 
                key="pain_points_input"
            )
    
    def contact_upload(self):
        """Display contact upload section"""
        with st.expander("Upload Contact Data (Optional)", expanded=False):
            st.markdown("Upload contacts from Hubspot or Apollo.io to generate personalized outreach")
            
            # File uploader for CSV
            self.uploaded_file = st.file_uploader("Upload contacts CSV", type=["csv"])
            
            if self.uploaded_file is not None:
                # Read the CSV file
                try:
                    self.contacts_df = pd.read_csv(self.uploaded_file)
                    st.write(f"Successfully loaded {len(self.contacts_df)} contacts")
                    
                    # Show a preview of the contacts
                    st.dataframe(self.contacts_df.head())
                    
                    # Mapping columns
                    st.subheader("Map Columns")
                    st.markdown("Select which columns contain key contact information")
                    
                    # Get column names from the CSV
                    csv_columns = self.contacts_df.columns.tolist()
                    
                    # Column mapping
                    col1, col2 = st.columns(2)
                    with col1:
                        self.name_col = st.selectbox("Full Name Column", options=[""] + csv_columns, index=0)
                        self.title_col = st.selectbox("Job Title Column", options=[""] + csv_columns, index=0)
                        self.company_col = st.selectbox("Company Column", options=[""] + csv_columns, index=0)
                    
                    with col2:
                        self.email_col = st.selectbox("Email Column", options=[""] + csv_columns, index=0)
                        self.phone_col = st.selectbox("Phone Column", options=[""] + csv_columns, index=0)
                        self.industry_col = st.selectbox("Industry Column", options=[""] + csv_columns, index=0)
                    
                    # Filter contacts to use
                    st.subheader("Filter Contacts")
                    
                    if self.title_col:
                        unique_titles = sorted(self.contacts_df[self.title_col].dropna().unique().tolist())
                        self.selected_titles = st.multiselect(
                            "Filter by Job Title",
                            options=unique_titles,
                            default=[]
                        )
                except Exception as e:
                    st.error(f"Error processing CSV: {str(e)}")
                    logger.error(f"Error processing CSV: {str(e)}")
                    self.contacts_df = None
    
    def _update_facility_from_inference(self, inferred_details):
        """Update facility attributes from inference results"""
        logger.info(f"Updating facility attributes from inference: {inferred_details}")
        try:
            # Update basic attributes
            self.facility_name = inferred_details.get("name", self.facility_name)
            self.location = inferred_details.get("location", self.location)
            
            # Handle type which might be a string or dict
            if "type" in inferred_details:
                if isinstance(inferred_details["type"], dict):
                    if "facility_type" in inferred_details["type"]:
                        self.facility_type = inferred_details["type"]["facility_type"]
                else:
                    self.facility_type = inferred_details["type"]
            
            # Handle size which might be a string or dict
            if "size" in inferred_details:
                if isinstance(inferred_details["size"], dict):
                    size_str = ""
                    if "number_of_locations" in inferred_details["size"]:
                        size_str += f"{inferred_details['size']['number_of_locations']} locations, "
                    elif "locations" in inferred_details["size"]:
                        size_str += f"{inferred_details['size']['locations']} locations, "
                    
                    if "annual_studies" in inferred_details["size"]:
                        size_str += f"{inferred_details['size']['annual_studies']} studies annually"
                    
                    self.size = size_str.strip(", ")
                else:
                    self.size = inferred_details["size"]
            
            # Handle infrastructure, challenge, events, budget, etc.
            for field in ["current_infrastructure", "key_challenge", "recent_events", "budget_cycle"]:
                if field in inferred_details:
                    if isinstance(inferred_details[field], dict):
                        first_key = next(iter(inferred_details[field].keys()), None)
                        if first_key:
                            setattr(self, field.replace("current_", ""), inferred_details[field][first_key])
                    else:
                        setattr(self, field.replace("current_", ""), inferred_details[field])
            
            # Handle pain_points
            if "pain_points" in inferred_details:
                if isinstance(inferred_details["pain_points"], list):
                    self.pain_points = "\n".join(inferred_details["pain_points"])
                else:
                    self.pain_points = inferred_details["pain_points"]
                    
            logger.info("Successfully updated facility attributes from inference")
        except Exception as e:
            logger.error(f"Error updating facility attributes: {str(e)}")
            traceback.print_exc()
    
    def format_facility_details(self):
        """Format facility details into a dictionary"""
        pain_points_list = [point.strip() for point in self.pain_points.split('\n') if point.strip()] if self.pain_points else []
        target_products = self.target_products if isinstance(self.target_products, list) else [self.target_products]
        
        # Handle facility_type which could be a string or a dict
        if isinstance(self.facility_type, dict) and "facility_type" in self.facility_type:
            facility_type = self.facility_type["facility_type"]
        else:
            facility_type = str(self.facility_type)
        
        return {
            "name": str(self.facility_name),
            "website_url": str(self.website_url),
            "location": str(self.location),
            "type": facility_type,
            "size": str(self.size),
            "current_infrastructure": str(self.current_infrastructure),
            "key_challenge": str(self.key_challenge),
            "recent_events": str(self.recent_events),
            "budget_cycle": str(self.budget_cycle),
            "pain_points": pain_points_list,  # Keep as a list
            "target_products": target_products,  # Keep as a list
            "industry": "",
            "employee_count": "",
            "website": str(self.website_url)
        }
    
    def generate_button(self):
        """Display generate button and handle generation process"""
        # Check for auto-generate flag
        auto_generate = st.session_state.get('auto_generate', False)
        
        # Display the button
        generate_clicked = st.button("🚀 Generate Sales Acceleration Package", type="primary", use_container_width=True)
        
        # Process generation if button clicked OR auto-generate is set
        if generate_clicked or auto_generate:
            # Reset the auto-generate flag if it was set
            if auto_generate:
                logger.info("Auto-generate flag detected - resetting for this run")
                st.session_state['auto_generate'] = False
            
            if not self.api_key:
                st.error("Please enter your OpenAI API key in the sidebar.")
            else:
                # Set the API key
                self.accelerator.set_api_key(self.api_key)
                self.accelerator.model = self.model
                
                # Prepare facility details
                facility_details = self.format_facility_details()

                # Get detailed use cases for target products
                product_use_cases = self.accelerator.get_product_use_cases(self.target_products)
                facility_details["product_use_cases"] = product_use_cases
                
                # Set up progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(percent, message):
                    progress_bar.progress(percent/100)
                    status_text.text(message)
                
                try:
                    # Process website if URL provided
                    website_data = None
                    apollo_data = None
                    
                    # Use Apollo data if available (only for company info, not contacts)
                    if 'selected_company' in st.session_state:
                        update_progress(10, f"Processing Apollo data for {st.session_state['selected_company'].get('name', 'company')}")
                        
                        # Create a combined data object with only company info
                        company = st.session_state['selected_company']
                        apollo_data = {
                            "organization": company,
                            "contacts": []  # No longer relying on Apollo for contacts
                        }
                        
                        # Include Apollo organization data in facility details
                        facility_details["apollo_organization"] = company
                    
                    if self.website_url:
                        # Get the most up-to-date URL from form field
                        current_url = self.website_url.strip()
                        # Log the URL being used
                        logger.info(f"Scraping website: {current_url}")
                        update_progress(15, f"Scraping website for enhanced intelligence: {current_url}")
                        website_data = self.accelerator.scrape_website(current_url)
                    
                    # Process CSV data if available (manual upload only)
                    csv_data = None
                    if hasattr(self, 'contacts_df') and self.contacts_df is not None:
                        update_progress(20, "Processing contact data for personalized outreach...")
                        # Filter by selected titles if any
                        if hasattr(self, 'selected_titles') and self.selected_titles and self.title_col:
                            filtered_df = self.contacts_df[self.contacts_df[self.title_col].isin(self.selected_titles)]
                        else:
                            filtered_df = self.contacts_df
                        
                        # Convert to dict for processing
                        csv_data = filtered_df.to_dict(orient='records')
                    
                    # Run the generation
                    start_time = time.time()
                    
                    # Determine if we should skip inference
                    skip_inference = auto_generate and 'inference_results' in st.session_state
                    if skip_inference:
                        update_progress(20, "Using previously inferred facility details...")
                    else:
                        update_progress(10, "Inferring facility details...")
                    
                    update_progress(20, "Mapping stakeholder ecosystem and influence networks...")
                    update_progress(30, "Analyzing industry context and trends...")
                    update_progress(40, "Extracting website intelligence and buying signals...")
                    update_progress(50, "Qualifying opportunity and mapping stakeholders...")
                    update_progress(60, "Creating technical value propositions...")
                    update_progress(70, "Developing ROI analysis and financial justification...")
                    update_progress(80, "Crafting authentic human communications...")
                    update_progress(90, "Strategically reviewing communications...")
                    update_progress(95, "Building objection handling strategies and compiling playbook...")
                    
                    # Special handling for auto-generated results
                    if skip_inference and 'inference_results' in st.session_state:
                        # Use the cached results from previous inference
                        logger.info("Using cached inference results")
                        results = st.session_state['inference_results']
                    else:
                        # Run the enhanced accelerator process with multiple products
                        results = self.accelerator.generate_sales_package(
                            facility_details=facility_details,
                            website_url=self.website_url,
                            target_products=self.target_products,
                            csv_data=csv_data,
                            apollo_data=apollo_data,
                            skip_inference=skip_inference,
                        )
                    
                    elapsed_time = time.time() - start_time
                    update_progress(100, f"Completed in {elapsed_time:.2f} seconds")
                    
                    # Display results with tabs for different components
                    st.subheader("Your Sales Acceleration Package")
                    
                    tabs = st.tabs([
                        "Facility Details",
                        "Stakeholder Ecosystem",
                        "Industry Research",
                        "Website Intelligence", 
                        "Deal Qualification", 
                        "Value Propositions", 
                        "ROI Analysis", 
                        "Personalized Emails", 
                        "Objection Handling",
                        "Complete Playbook"
                    ])
                    
                    with tabs[0]:
                        st.markdown("### Inferred Facility Details")
                        inferred_details = results.get("inferred_facility_details", facility_details)
                        
                        # Handle different possible structures for inferred_details
                        if not isinstance(inferred_details, dict):
                            st.warning("Inferred details are not in the expected format.")
                            st.json(inferred_details)
                        else:
                            # Create a clean display of facility details
                            if "error" in inferred_details:
                                st.error(f"Error in facility inference: {inferred_details['error']}")
                            
                            st.markdown(f"**Facility Name:** {inferred_details.get('name', 'N/A')}")
                            st.markdown(f"**Location:** {inferred_details.get('location', 'N/A')}")
                            
                            # Handle type display
                            if "type" in inferred_details:
                                if isinstance(inferred_details["type"], dict):
                                    if "facility_type" in inferred_details["type"]:
                                        st.markdown(f"**Type:** {inferred_details['type']['facility_type']}")
                                        if "rationale" in inferred_details["type"]:
                                            st.markdown(f"*Rationale: {inferred_details['type']['rationale']}*")
                                else:
                                    st.markdown(f"**Type:** {inferred_details['type']}")
                            
                            # Handle size display
                            if "size" in inferred_details:
                                if isinstance(inferred_details["size"], dict):
                                    size_parts = []
                                    if "number_of_locations" in inferred_details["size"]:
                                        size_parts.append(f"Locations: {inferred_details['size']['number_of_locations']}")
                                    elif "locations" in inferred_details["size"]:
                                        size_parts.append(f"Locations: {inferred_details['size']['locations']}")
                                    
                                    if "annual_studies" in inferred_details["size"]:
                                        size_parts.append(f"Annual studies: {inferred_details['size']['annual_studies']}")
                                    
                                    st.markdown(f"**Size:** {', '.join(size_parts)}")
                                    
                                    if "rationale" in inferred_details["size"]:
                                        st.markdown(f"*Rationale: {inferred_details['size']['rationale']}*")
                                else:
                                    st.markdown(f"**Size:** {inferred_details['size']}")
                            
                            # Handle infrastructure display
                            if "current_infrastructure" in inferred_details:
                                if isinstance(inferred_details["current_infrastructure"], dict):
                                    st.markdown("**Current Infrastructure:**")
                                    for key, value in inferred_details["current_infrastructure"].items():
                                        if isinstance(value, list):
                                            st.markdown(f"- {key}: {', '.join(value)}")
                                        else:
                                            st.markdown(f"- {key}: {value}")
                                else:
                                    st.markdown(f"**Current Infrastructure:** {inferred_details['current_infrastructure']}")
                            
                            # Handle pain points display
                            if "pain_points" in inferred_details:
                                st.markdown("**Pain Points:**")
                                if isinstance(inferred_details["pain_points"], list):
                                    for point in inferred_details["pain_points"]:
                                        st.markdown(f"- {point}")
                                else:
                                    st.markdown(inferred_details["pain_points"])
                            
                            # Display other fields
                            if "key_challenge" in inferred_details:
                                st.markdown(f"**Key Challenge:** {inferred_details['key_challenge']}")
                            
                            if "recent_events" in inferred_details:
                                if isinstance(inferred_details["recent_events"], dict):
                                    event = inferred_details["recent_events"].get("event", "Unknown")
                                    st.markdown(f"**Recent Events:** {event}")
                                else:
                                    st.markdown(f"**Recent Events:** {inferred_details['recent_events']}")
                            
                            if "budget_cycle" in inferred_details:
                                if isinstance(inferred_details["budget_cycle"], dict):
                                    cycle = inferred_details["budget_cycle"].get("cycle", "Unknown")
                                    st.markdown(f"**Budget Cycle:** {cycle}")
                                else:
                                    st.markdown(f"**Budget Cycle:** {inferred_details['budget_cycle']}")
                    
                    with tabs[1]:
                        st.markdown("### Stakeholder Ecosystem Map")
                        st.markdown(results.get("stakeholder_ecosystem", "No data available"))
                    
                    with tabs[2]:
                        st.markdown("### Industry Research")
                        st.markdown(results.get("industry_research", "No data available"))
                    
                    with tabs[3]:
                        st.markdown("### Website Intelligence Analysis")
                        st.markdown(results.get("website_intelligence", "No data available"))
                    
                    with tabs[4]:
                        st.markdown("### Opportunity Qualification")
                        st.markdown(results.get("deal_qualification", "No data available"))
                    
                    with tabs[5]:
                        st.markdown("### Value Propositions")
                        st.markdown(results.get("value_propositions", "No data available"))
                    
                    with tabs[6]:
                        st.markdown("### ROI Analysis")
                        st.markdown(results.get("roi_analysis", "No data available"))
                    
                    with tabs[7]:
                        st.markdown("### Personalized Email Templates")
                        
                        # Option to show draft vs. final emails
                        show_drafts = st.checkbox("Show draft communications (before strategic review)")
                        
                        if show_drafts:
                            st.markdown("#### Draft Communications (Before Strategic Review)")
                            st.markdown(results.get("draft_communications", "No draft communications available"))
                            st.markdown("#### Final Communications (After Strategic Review)")
                        
                        st.markdown(results.get("personalized_emails", "No data available"))
                    
                    with tabs[8]:
                        st.markdown("### Objection Handling Guide")
                        st.markdown(results.get("objection_handling", "No data available"))
                    
                    with tabs[9]:
                        st.markdown("### Complete Sales Playbook")
                        st.markdown(results.get("complete_playbook", "No data available"))
                    
                    # Save playbook to database
                    save_success = save_playbook_to_db(
                        self.db_path,
                        self.facility_name,
                        self.location,
                        self.target_products,
                        results
                    )
                    
                    if save_success:
                        st.success("✅ Playbook saved to your private database.")
                    else:
                        st.warning("⚠️ Failed to save playbook to database.")
                    
                    # Add download buttons
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.download_button(
                            label="Download Complete Sales Package (JSON)",
                            data=json.dumps(results, indent=2),
                            file_name=f"{self.facility_name.replace(' ', '_')}_Sales_Package.json",
                            mime="application/json"
                        )
                    
                    with col2:
                        # Create a markdown version
                        markdown_content = f"""# Flux Sales Package: {self.facility_name}
                        
## Inferred Facility Details
**Facility Name:** {inferred_details.get("name", "N/A")}  
**Location:** {inferred_details.get("location", "N/A")}  
**Type:** {inferred_details.get("type", "N/A") if not isinstance(inferred_details.get("type"), dict) else inferred_details.get("type", {}).get("facility_type", "N/A")}  
**Size:** {inferred_details.get("size", "N/A") if not isinstance(inferred_details.get("size"), dict) else f"{inferred_details.get('size', {}).get('number_of_locations', '')} locations, {inferred_details.get('size', {}).get('annual_studies', '')} studies"}  
**Current Infrastructure:** {inferred_details.get("current_infrastructure", "N/A") if not isinstance(inferred_details.get("current_infrastructure"), dict) else "; ".join([f"{k}: {v}" for k, v in inferred_details.get("current_infrastructure", {}).items()])}  
**Key Challenge:** {inferred_details.get("key_challenge", "N/A")}  
**Recent Events:** {inferred_details.get("recent_events", "N/A") if not isinstance(inferred_details.get("recent_events"), dict) else inferred_details.get("recent_events", {}).get("event", "N/A")}  
**Budget Cycle:** {inferred_details.get("budget_cycle", "N/A") if not isinstance(inferred_details.get("budget_cycle"), dict) else inferred_details.get("budget_cycle", {}).get("cycle", "N/A")}  
**Pain Points:** {', '.join(inferred_details.get("pain_points", [])) if isinstance(inferred_details.get("pain_points"), list) else inferred_details.get("pain_points", "N/A")}

## Stakeholder Ecosystem Map
{results.get("stakeholder_ecosystem", "No data available")}

## Industry Research
{results.get("industry_research", "No data available")}

## Website Intelligence Analysis
{results.get("website_intelligence", "No data available")}

## Opportunity Qualification
{results.get("deal_qualification", "No data available")}

## Value Propositions
{results.get("value_propositions", "No data available")}

## ROI Analysis
{results.get("roi_analysis", "No data available")}

## Personalized Email Templates
{results.get("personalized_emails", "No data available")}

## Objection Handling Guide
{results.get("objection_handling", "No data available")}

## Complete Sales Playbook
{results.get("complete_playbook", "No data available")}
                        """
                        
                        st.download_button(
                            label="Download as Markdown",
                            data=markdown_content,
                            file_name=f"{self.facility_name.replace(' ', '_')}_Sales_Package.md",
                            mime="text/markdown"
                        )
                    
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    logger.error(f"Error generating sales package: {str(e)}")
                    traceback.print_exc()
                    st.error("Please check your API key and try again.")
    
    def run(self):
        """Run the application"""
        # Check for admin mode first
        if st.session_state.get('show_admin', False):
            admin_page(self.db_path)
            if st.button("Back to Main App", type="primary"):
                st.session_state['show_admin'] = False
                st.rerun()
            return  # Important to return here to avoid showing main app
            
        # Display debugging state if enabled
        if os.environ.get('DEBUG', 'false').lower() == 'true':
            st.sidebar.write("Session State:", st.session_state)
            
        # Default view - show some instructions
        if 'OPENAI_API_KEY' not in os.environ and not self.api_key:
            st.info("👈 Please enter your OpenAI API key in the sidebar to get started.")
            st.markdown("""
            ## How to use this enhanced Flux Sales Accelerator:
            
            1. Enter your OpenAI API key in the sidebar
            2. Enter your Apollo API key for company search
            3. Search for your target company and infer facility details
            4. Add any additional facility details or edit inferred data
            5. Upload contacts manually via CSV for personalized outreach
            6. Click "Generate Sales Acceleration Package"
            7. Use the generated materials to close more deals, faster!
            
            This enhanced tool creates highly targeted sales materials for Flux's entire product suite:
            - DICOM Printer 2: Send anything to PACS
            - Capacitor: Smart DICOM store-forward router
            - TuPACS: Scan and send to PACS
            - Gobbler: DICOMDIR disc and USB to PACS
            """)

if __name__ == "__main__":
    app = FluxSalesAcceleratorApp()
    app.run()