from crewai import Task
from product_knowledge import ProductKnowledge
from google_search_tool import GoogleSearchTool
import json
import logging

def truncate_for_tokens(text, max_chars=2000):
    """Truncate text to approximate token limits"""
    if text is None:
        return ""
    if len(text) > max_chars:
        return text[:max_chars] + "...(truncated)"
    return text

# Configure logging
logger = logging.getLogger(__name__)

def create_enhanced_flux_tasks(agents, facility_details, website_data, target_products=None):
    """
    Create enhanced task definitions for Flux Sales Accelerator with detailed
    product knowledge and improved website intelligence.

    Args:
        agents (dict): Dictionary of specialized agents
        facility_details (dict): Details about the target healthcare facility
        website_data (dict): Enhanced website intelligence data
        target_products (list): List of target product focus

    Returns:
        list: List of CrewAI tasks
    """
    # Check if target_products is provided and valid
    if target_products is None or len(target_products) == 0:
        target_products = ["DICOM Printer 2", "Capacitor"]

    target_products_str = ", ".join(target_products)

    # Perform Google searches during task creation
    facility_name = facility_details.get('name', 'Unknown')
    location = facility_details.get('location', 'Unknown')

    # Perform research if we have a valid facility name
    research_data = {}
    search_results = []
    search_summary = ""

    if facility_name and facility_name != "Unknown":
        try:
            logger.info(f"Performing Google search for {facility_name}")
            # Try to import config, but use direct values if not available
            try:
                import config
                api_key = config.GOOGLE_API_KEY
                search_engine_id = config.GOOGLE_CSE_ID
            except (ImportError, AttributeError):
                # Use hardcoded values as fallback
                api_key = "AIzaSyAydQbFITjj-_jxwAeg7UNQcZjLzs4fwmc"
                search_engine_id = "a783ec7f54f7c4845"
                logger.warning("Using hardcoded API keys - consider setting up config.py")

            # Create GoogleSearchTool
            google_search = GoogleSearchTool(
                api_key=api_key,
                search_engine_id=search_engine_id
            )
            try:
                # OPTIMIZATION: Only do targeted searches instead of full research
                # Combine key search terms into 2 focused queries
                logger.info(f"Performing targeted search for {facility_name}")
                # First query - focus on technology and PACS
                tech_query = f"{facility_name} {location} radiology PACS imaging technology"
                tech_results = google_search.search(tech_query, 2)  # Reduced to 2 results
                # Second query - focus on news and recent events
                news_query = f"{facility_name} {location} healthcare news recent"
                news_results = google_search.search(news_query, 2)  # Reduced to 2 results
            except Exception as e:
                logger.error(f"Error performing targeted search: {str(e)}")
                tech_results = []
                news_results = []

                # Initialize search summary
                search_summary = "\nKEY SEARCH FINDINGS:\n"

                # OPTIMIZATION: Skip the expensive research_facility call
                # Instead, build a simple summary from our targeted queries
                # Add technology results
                if tech_results:
                    search_summary += "\nTECHNOLOGY INFORMATION:\n"
                    for result in tech_results[:2]:
                        # Truncate snippet to 150 chars max
                        snippet = result.get('snippet', 'No description available')
                        if len(snippet) > 150:
                            snippet = snippet[:150] + "..."
                        search_summary += f"- {result.get('title', 'Unknown')}: {snippet}\n"

                # Add news results
                if news_results:
                    search_summary += "\nRECENT NEWS:\n"
                    for result in news_results[:2]:
                        # Truncate snippet to 150 chars max
                        snippet = result.get('snippet', 'No description available')
                        if len(snippet) > 150:
                            snippet = snippet[:150] + "..."
                        search_summary += f"- {result.get('title', 'Unknown')}: {snippet}\n"

                # OPTIMIZATION: Enforce a hard character limit on search_summary
                if len(search_summary) > 1000:
                    search_summary = search_summary[:1000] + "...(truncated)"

                # Log success with character count to monitor token usage
                logger.info(f"Google search completed for {facility_name}")
                logger.info(f"Search summary contains {len(search_summary)} characters")
        except Exception as e:
            logger.error(f"Error performing Google search: {str(e)}")
            search_summary = f"Error performing search: {str(e)}"
    facility_context = ""
    if facility_details:
        facility_context = f"""
        Facility Name: {facility_details.get('name', 'Unknown')}
        Location: {facility_details.get('location', 'Unknown')}
        Type: {facility_details.get('type', 'Unknown')}
        Size: {facility_details.get('size', 'Unknown')}
        Current Infrastructure: {facility_details.get('current_infrastructure', 'Unknown')}
        Key Challenge: {facility_details.get('key_challenge', 'Unknown')}
        Recent Events: {facility_details.get('recent_events', 'Unknown')}
        Budget Cycle: {facility_details.get('budget_cycle', 'Unknown')}
        Pain Points: {', '.join(facility_details.get('pain_points', []))}
        """

    # Extract Apollo data for a concise summary
    apollo_summary = ""
    if website_data and isinstance(website_data, dict) and website_data.get('apollo_data') and isinstance(website_data.get('apollo_data'), dict):
        try:
            apollo_data = website_data.get('apollo_data', {})
            org_data = apollo_data.get('organization', {})
            if org_data:
                apollo_summary = "APOLLO DATA SUMMARY:\n"
                # Basic organization information
                if org_data.get('name'):
                    apollo_summary += f"- Organization Name: {org_data.get('name', 'Unknown')}\n"
                if org_data.get('founded_year'):
                    apollo_summary += f"- Founded Year: {org_data.get('founded_year', 'Unknown')}\n"
                if org_data.get('estimated_num_employees'):
                    apollo_summary += f"- Employee Count: {org_data.get('estimated_num_employees', 'Unknown')}\n"
                if org_data.get('annual_revenue_printed'):
                    apollo_summary += f"- Annual Revenue: {org_data.get('annual_revenue_printed', 'Unknown')}\n"

                # Location information
                address_parts = []
                if org_data.get('street_address'):
                    address_parts.append(org_data.get('street_address'))
                if org_data.get('city'):
                    address_parts.append(org_data.get('city'))
                if org_data.get('state'):
                    address_parts.append(org_data.get('state'))
                if org_data.get('postal_code'):
                    address_parts.append(org_data.get('postal_code'))
                if org_data.get('country'):
                    address_parts.append(org_data.get('country'))
                if address_parts:
                    apollo_summary += f"- Address: {', '.join(address_parts)}\n"

                # Technologies used
                if org_data.get('technology_names') and isinstance(org_data.get('technology_names'), list):
                    apollo_summary += f"- Technologies: {', '.join(org_data.get('technology_names')[:5])}\n"

                # Description
                if org_data.get('short_description'):
                    desc = org_data.get('short_description')
                    # Truncate if too long
                    if len(desc) > 500:
                        desc = desc[:500] + "..."
                    apollo_summary += f"- Description: {desc}\n"
        except Exception as e:
            logger.error(f"Error processing Apollo data: {str(e)}")
            apollo_summary = "Error processing Apollo data."

    # Create website intelligence summary
    website_intel_summary = "No website data available."
    if website_data and not website_data.get('error'):
        website_intel_summary = f"""
        Website URL: {website_data.get('url', 'Unknown')}
        Website Title: {website_data.get('page_title', 'Unknown')}
        Pages Scanned: {website_data.get('pages_scanned', 0)}

        ## Content Analysis
        Radiology/Imaging Mentions: {website_data.get('radiology_mentions', 0)}
        PACS Mentions: {website_data.get('pacs_mentions', 0)}
        DICOM Mentions: {website_data.get('dicom_mentions', 0)}
        Workflow Mentions: {website_data.get('workflow_mentions', 0)}
        Modernization Mentions: {website_data.get('modernization_mentions', 0)}

        ## Identified Technology Stack
        PACS Vendor: {website_data.get('technology_stack', {}).get('pacs_vendor', 'Unknown')}
        RIS Vendor: {website_data.get('technology_stack', {}).get('ris_vendor', 'Unknown')}
        Infrastructure: {', '.join(website_data.get('technology_stack', {}).get('infrastructure', ['Unknown']))}
        Modalities: {', '.join(website_data.get('technology_stack', {}).get('modalities', ['Unknown']))}

        ## Key Personnel
        {website_data.get('key_personnel', [])}

        ## Identified Pain Points
        {website_data.get('pain_points', [])}

        ## Growth Indicators
        {website_data.get('growth_indicators', [])}

        ## Job Openings
        {website_data.get('job_openings', [])}
        """

    # Facility Inference Task - Updated definition
    facility_inference_task = Task(
        description=f"""
        Create a detailed healthcare facility profile based on your expertise from 3,000+ implementations.
        GOOGLE SEARCH RESULTS:
        {truncate_for_tokens(search_summary, 1000) if search_summary else "No specific information found."}
        WEBSITE DATA ANALYSIS:
        {truncate_for_tokens(website_intel_summary, 1200)}
        Analyze the data and generate a comprehensive profile including:
        1. Facility Specifics & Scale:
        - Number of locations with geographical distribution
        - Annual imaging volumes (Locations × Modality Mix Factor × Regional Volume)
        - Radiologist counts with subspecialty breakdown
        - Technologist staffing based on modality mix
        2. Technical Infrastructure Assessment:
        - PACS/RIS systems with versions and implementation dates
        - EMR/EHR integration points
        - Primary imaging modalities by type, vendor, and age
        - Storage infrastructure and disaster recovery
        3. Quantitative Pain Points (with specific metrics):
        - Image retrieval times and workflow bottlenecks
        - Efficiency metrics compared to benchmark facilities
        - Integration issues and their operational impact
        - Cost implications in FTE hours and financial terms
        4. Competitive Analysis & Opportunity Sizing
        - Regional competitors with distance and comparison
        - Potential revenue value and implementation timeframe
        - Expected ROI with quantitative metrics
        COMPANY INFORMATION:
        Company: {facility_details.get('name', 'Unknown')}
        Website: {facility_details.get('website_url', 'Unknown')}
        Location: {facility_details.get('location', 'Unknown')}
        IMPORTANT: Provide specific metrics, accurate vendor information, and quantifiable values throughout. Use your expertise when exact data isn't available.
        RETURN DATA IN THIS FORMAT:
        {{
            "name": "Facility Name",
        "location": "Specific location",
        "type": "Facility type with subspecialty focus",
            "size": {{
        "locations": "Number and distribution",
        "annual_studies": "Volume with calculation formula",
        "radiologists": "Count with subspecialty breakdown",
        "technologists": "Staffing estimate"
            }},
            "current_infrastructure": {{
        "pacs_system": "Vendor, version, implementation date",
        "ris_system": "Vendor, version, implementation date",
                "primary_modalities": [
        {{"type": "CT", "vendor": "Example", "quantity": 2, "age": "3-4 years"}}
                ],
        "storage_infrastructure": "Current solution with capacity"
            }},
            "pain_points": [
        {{"issue": "Specific pain point", "impact": "Quantified impact", "opportunity": "Solution"}}
            ],
        "key_challenge": "Primary challenge",
        "recent_events": "Recent significant event",
        "budget_cycle": "Budget planning and timing"
                }}
        """,
        expected_output="A comprehensive, data-driven facility profile with specific metrics, benchmarks, and quantitative assessments derived from global implementation experience",
        agent=agents["facility_inference_specialist"]
    )

    # Rest of the tasks remain unchanged
    # Stakeholder ecosystem mapping task
    stakeholder_ecosystem_task = Task(
        description=f"""
        Map the complete stakeholder ecosystem at the target healthcare facility to identify
        key relationships, influence patterns, and communication preferences:

        1. Primary Stakeholder Identification:
           - Identify key stakeholders based on facility type, size, and organizational structure
           - Determine formal roles involved in imaging technology decisions (CIO, CMIO, Radiology Director, PACS Admin, etc.)
           - Estimate reporting relationships and formal hierarchies
           - Identify probable committees or groups involved in purchasing decisions

        2. Influence Network Analysis:
           - Map likely informal influence patterns beyond the formal hierarchy
           - Identify potential champions and blockers for new technology adoption
           - Determine who might be "hidden influencers" despite not having formal authority
           - Analyze how facility type and size affects decision making dynamics

        3. Stakeholder Prioritization:
           - Rank stakeholders by estimated influence on purchasing decisions
           - Create a visual map showing primary, secondary, and tertiary stakeholders
           - Identify the optimal sequence for stakeholder engagement
           - Determine potential entry points for initial conversations

        4. Communication Preference Analysis:
           - Recommend communication approaches for each key stakeholder based on role
           - Identify likely priorities and concerns for each stakeholder type
           - Determine appropriate technical depth for communications with each role
           - Suggest relationship-building strategies for different stakeholder types

        5. Decision Process Mapping:
           - Outline the likely purchasing process based on facility type and size
           - Identify potential barriers and accelerators in the decision process
           - Map how budget cycles affect purchase timing
           - Estimate timeframes for the complete decision journey

        APOLLO CONTACT DATA:
        When Apollo contact data is available (see below), use it to create a precise stakeholder map based on real people:
           - Analyze their titles, seniorities, and departments to determine roles and influences
           - Map reporting relationships based on titles and seniorities
           - Identify the most senior and influential contacts
           - Create personalized communication preferences for each specific person
           - Use their actual roles rather than hypothetical stakeholders
           - Ensure your map focuses on the real people identified through Apollo


        FACILITY CONTEXT:
        {facility_context}

        WEBSITE INTELLIGENCE SUMMARY:
        {website_intel_summary}

        TARGET PRODUCT FOCUS:
        {target_products_str}
        """,
        expected_output="A comprehensive stakeholder ecosystem map with influence patterns, priorities, and engagement strategies for each key stakeholder.",
        agent=agents["stakeholder_ecosystem_mapper"]
    )

    # Industry research task
    industry_research_task = Task(
        description=f"""
        Conduct in-depth industry research for the target healthcare facility to identify
        current trends, challenges, and opportunities relevant to Flux's products:

        1. Analyze the facility type, size, and current infrastructure to identify industry-specific challenges:
           - Common workflow challenges for this facility type
           - Typical imaging volumes and operational patterns
           - Standard technology stacks and integration points
           - Regulatory and compliance requirements specific to this region

        2. Map current industry trends to opportunities for Flux products:
           - Identify how macro healthcare trends impact this specific facility type
           - Determine how workforce challenges might create automation needs
           - Analyze how interoperability standards are evolving for this market segment
           - Evaluate cloud adoption patterns for this facility type

        3. Create a "Market Position Analysis" that includes:
           - Specific industry benchmarks for similar facilities
           - Technologies typically deployed at similar sites
           - Common modernization pathways for this facility type
           - Industry-specific ROI models and metrics

        4. Provide a detailed "Industry Context Summary" that:
           - Places the facility's pain points in broader industry context
           - Identifies whether challenges are typical or unique
           - Highlights industry-specific priorities and concerns
           - Provides benchmarks and comparative data

        Use the website intelligence and facility information to tailor your analysis to
        this specific healthcare organization while providing valuable industry context.

        FACILITY CONTEXT:
        {facility_context}

        WEBSITE INTELLIGENCE SUMMARY:
        {website_intel_summary}

        TARGET PRODUCT FOCUS:
        {target_products_str}
        """,
        expected_output="A comprehensive industry analysis that positions Flux's products within the context of current healthcare imaging trends.",
        agent=agents["industry_research_specialist"]
    )
   
    # Website intelligence task with enhanced product knowledge
    website_intelligence_task = Task(
        description=f"""
        Analyze the target prospect's website data, facility information, and industry context
        to extract actionable sales intelligence specific to Flux's products:
       
        1. Healthcare IT Environment Assessment:
           - Identify the specific PACS, RIS, and other systems mentioned
           - Determine modality mix and imaging volumes
           - Evaluate technology infrastructure (on-prem, cloud, hybrid)
           - Assess integration challenges and opportunities
       
        2. Pain Point Analysis (map to Flux products):
           - Link identified pain points directly to specific Flux product capabilities
           - Quantify impact of pain points on operations when possible
           - Prioritize pain points by strategic importance and ease of solution
           - Identify unstated pain points likely to exist based on technology mix
       
        3. Buying Signals Assessment:
           - Evaluate evidence of modernization initiatives or technology refresh cycles
           - Identify budget planning indicators or fiscal timing opportunities
           - Assess organizational readiness based on job postings and personnel
           - Determine likely barriers to purchase and adoption
       
        4. Product-Specific Opportunity Mapping:
           - For each product, identify specific integration challenges that the product would solve
           - Specifically analyze for the following products: {target_products_str}
          
        5. Create a "Website Intelligence Summary" that outlines:
           - Top 3 sales opportunities with direct links to specific Flux products
           - Specific language from the website that can be used in sales communications
           - Key stakeholders and their likely priorities based on roles and organization
           - Precise pain points that create urgency for Flux solutions
       
        If website data analysis is limited, indicate this and provide guidance on
        gathering additional intelligence through other means.
       
        FACILITY CONTEXT:
        {facility_context}
       
        WEBSITE INTELLIGENCE SUMMARY:
        {website_intel_summary}
       
        TARGET PRODUCT FOCUS:
        {target_products_str}
        """,
        expected_output="A comprehensive website intelligence report that reveals actionable sales opportunities mapped directly to Flux products.",
        agent=agents["website_intelligence_analyst"]
    )
   
    # Deal qualification task with enhanced product knowledge
    deal_qualification_task = Task(
        description=f"""
        Analyze the target healthcare facility and create a detailed sales qualification report:
       
        1. Opportunity Assessment:
           - Determine potential deal size with specific revenue ranges for each Flux product
           - Score overall opportunity on scale of 1-10 for closing probability with detailed rationale
           - Identify specific decision-makers by role who can approve purchase
           - Create timeline projection with key milestones for deal progression
       
        2. Product Fit Analysis:
           - Determine which Flux product(s) represent best primary and secondary opportunities
           - Provide specific justification for product recommendations based on facility context
           - Identify logical product bundles or cross-sell opportunities
           - Suggest optimal product configuration based on facility size and needs
       
        3. Stakeholder Mapping:
           - Map key stakeholders to their likely priorities and pain points
           - Identify potential champions and blockers with engagement strategies
           - Outline decision-making structure and approval process based on facility type
           - Create influence strategy for key decision-makers
       
        4. Opportunity Qualification Details:
           - Budget availability assessment based on fiscal cycle and facility type
           - Technical readiness evaluation for implementation
           - Competitive threat analysis with specific displacement strategies
           - Risk assessment with mitigation recommendations
        4a. Product-Specific Qualification:
           - For Capacitor, evaluate specific fit based on these key indicators:
              * Network reliability issues: Frequent failed transfers indicate high value
              * Multi-vendor environment: Different vendor systems needing integration
              * Mobile operations: Units with intermittent connectivity
              * Legacy equipment: Older modalities needing format conversion
              * Large study volumes: Facilities processing >100K studies annually
           - For DICOM Printer 2, evaluate specific fit based on these key indicators:
              * Document handling processes: Manual scanning workflows indicate high value
              * Legacy systems: Older systems producing paper or non-DICOM output
              * Error concerns: Patient mismatches or lost documentation
              * Staff efficiency issues: Time spent on manual document handling
              * Compliance requirements: Documentation needs for regulatory purposes
       
        5. Create "Deal Strategy Blueprint" that includes:
           - Clear statement of expected revenue range with probability percentages
           - 3-5 compelling reasons why this prospect NEEDS Flux products now
           - Key technical and business drivers for purchase
           - Recommended approach with concrete next steps
       
        Use the website intelligence, industry research, and facility information to create
        a precise qualification that will drive sales strategy.
       
        FACILITY CONTEXT:
        {facility_context}
       
        WEBSITE INTELLIGENCE SUMMARY:
        {website_intel_summary}
       
        TARGET PRODUCT FOCUS:
        {target_products_str}
        """,
        expected_output="A precise sales qualification that accurately identifies revenue potential, decision-makers, and closing strategy.",
        agent=agents["deal_qualifier"]
    )
   
    # Technical value proposition task with product expertise
    value_proposition_task = Task(
        description=f"""
        Create technically precise, compelling value propositions for Flux's products:

        1. Product-Specific Technical Value Propositions:
           - For each recommended Flux product, create technical value propositions that:
              * Address specific pain points identified in the facility and website analysis
              * Highlight technical capabilities that solve identified workflow challenges
              * Differentiate from competing solutions with technical specificity
              * Include quantifiable technical benefits (speed, reliability, compatibility)

        DETAILED USE CASES TO LEVERAGE:
        {target_products_str} DETAILED USE CASES:
        For Capacitor:
        1. Mobile Imaging
        - Problem: Mobile units face intermittent connectivity causing delays
        - Solution: Intelligent store-forward caching for continuous operation
        - Benefits: Technologist focus on patients, automatic uploads when connected, 35% bandwidth reduction
        - Examples: UPenn mobile radiology, multiple mammography services
        2. Cross-Vendor Compatibility
        - Problem: Integration issues between equipment from different vendors
        - Solution: Vendor emulation and DICOM tag manipulation
        - Benefits: Seamless integration, error reduction, broader compatibility
        - Examples: Major mammography vendors, multi-vendor hospital environments
        3. Format Conversion
        - Problem: Legacy CTO/SCO formats incompatible with modern PACS
        - Solution: Real-time conversion to BTO format
        - Benefits: 5-7 year equipment life extension, $75-150K savings per modality
        - Examples: 1.2M study migration without downtime, seamless PACS upgrades

        For DICOM Printer 2:
        1. Legacy System Integration
        - Problem: Valuable documents from older systems can't reach PACS
        - Solution: Convert any printable document to DICOM format
        - Benefits: 2.5 hours saved daily, 93% error reduction, eliminated paper costs
        - Examples: Dental practice network, cardiology report unification
        2. Document Workflow Automation
        - Problem: Manual document handling creates bottlenecks
        - Solution: Automated matching and metadata extraction
        - Benefits: Processing time from minutes to seconds, automatic attribute population
        - Examples: Hospital processing 100K documents yearly, multi-site practice documentation

        Use these detailed use cases to create highly specific, technically precise value propositions
        tailored to the facility's specific environment and identified pain points. Include quantitative
        metrics and relevant examples from similar facilities whenever possible.

        2. Stakeholder-Specific Technical Value Frameworks:
           - Create technical value propositions tailored to different stakeholders:
              * For IT: Focus on integration ease, security, reliability, and maintenance
              * For Radiology Admins: Focus on workflow improvements and clinical productivity
              * For Department Directors: Focus on staff productivity and service quality
              * For Finance: Focus on TCO, ROI, and operational efficiency metrics

        3. Technical Differentiation Matrix:
           - Create a technical comparison framework that shows:
              * Specific technical advantages versus identified or likely competitors
              * Unique technical capabilities that only Flux products offer
              * Technical compatibility advantages with existing infrastructure
              * Security and compliance advantages of Flux solutions

        4. Technical Solution Narrative:
           - Create a compelling technical story that shows:
              * Current state with technical limitations and challenges
              * Implementation process with technical specifics and timeframes
              * Future state with technical improvements and benefits
              * Long-term technical strategic advantages

        Each value proposition must be technically precise, credible, and directly relevant
        to the specific technical environment and challenges of this facility. Use concrete
        technical details, not generic marketing statements.

        FACILITY CONTEXT:
        {facility_context}

        WEBSITE INTELLIGENCE SUMMARY:
        {website_intel_summary}

        TARGET PRODUCT FOCUS:
        {target_products_str}
        """,
        expected_output="A set of technically precise value propositions that clearly articulate why Flux products are the optimal solution.",
        agent=agents["technical_value_strategist"]
    )
   
    # ROI analysis task with financial expertise
    roi_task = Task(
        description=f"""
        Develop a data-driven financial justification for investing in Flux's products:
       
        1. Current State Cost Analysis:
           - Quantify current costs related to the problems Flux products would solve:
              * Staff time (hours per day/week with fully-loaded hourly costs)
              * Operational inefficiencies (extended wait times, delayed reads)
              * Missed revenue opportunities (limited throughput, billable exams)
              * Infrastructure costs (existing solutions, maintenance fees)
              * Compliance and security risks (potential penalties, mitigation costs)
       
        2. Implementation Investment Model:
           - Create detailed investment breakdown:
              * License and maintenance costs for specific Flux products
              * Implementation and integration services
              * Training and change management
              * Hardware requirements (if any)
              * Internal IT resource allocation
       
        3. Multi-Year ROI Projection:
           - Create specific ROI models showing:
              * 1-year, 3-year, and 5-year financial returns
              * Monthly and quarterly breakdowns for year 1
              * Direct vs. indirect benefits clearly separated
              * Payback period with specific milestone dates
              * Capital vs. operational expense analysis
       
        4. Benefit Categories with Specific Metrics:
           - Quantify benefits in specific categories:
              * Staff productivity gains (hours saved, reallocated time)
              * Revenue impact (additional studies processed, billing efficiency)
              * Infrastructure savings (reduced storage costs, hardware elimination)
              * Operational improvements (reduced turnaround time, fewer errors)
              * Risk mitigation value (compliance, security, reliability improvements)
       
        5. Create "Financial Justification Package" with:
           - Executive summary with key financial metrics
           - Detailed cost/benefit analysis with data sources
           - Alternative investment comparison (status quo, competitor solutions)
           - Budget alignment and timing recommendations
           - Low-risk implementation approach to accelerate ROI
       
        The ROI model must be based on realistic assumptions drawn from facility information,
        industry benchmarks, and Flux customer results. All figures should be pragmatic and
        defensible, not aspirational or exaggerated.
       
        FACILITY CONTEXT:
        {facility_context}
       
        WEBSITE INTELLIGENCE SUMMARY:
        {website_intel_summary}
       
        TARGET PRODUCT FOCUS:
        {target_products_str}
        """,
        expected_output="A comprehensive, credible ROI analysis that financially justifies investment in Flux products.",
        agent=agents["financial_roi_expert"]
    )
   
    # Authentic relationship building task
    relationship_building_task = Task(
        description=f"""
        Create authentic, human-to-human communications that build genuine professional relationships:
       
        CORE PHILOSOPHICAL APPROACH:
        You are writing as one healthcare technology professional to another - not as a vendor to a prospect.
        Your goal is to start a genuine conversation that might eventually lead to helping them solve real 
        problems. You will not use any conventional sales communication techniques, but instead write exactly 
        as you would to a respected colleague at another organization.
       
        UNDERSTANDING THE PSYCHOLOGY OF TRUST:
        Your communication must establish all four components of professional trust:
        1. Competence: Demonstrate relevant knowledge about their specific situation and challenges
        2. Warmth: Show genuine care for their success and well-being as a fellow professional
        3. Integrity: Be completely honest, including about limitations or challenges
        4. Reliability: Set clear expectations and deliver on what you promise
       
        RESEARCH DEPTH APPROACH:
        Before writing, deeply analyze the organization to understand:
        - Their specific technical environment and challenges based on website data
        - Recent organizational changes or initiatives they're undertaking
        - Industry pressures specific to their type of organization
        - How their role typically interfaces with the challenges you might help solve
       
        COMMUNICATION FRAMEWORK:
        1. Initial Outreach - Share an Insight:
           - For key decision-makers, create a personalized initial outreach email that:
             * Opens with a specific observation about their organization that shows genuine research
             * Shares a relevant insight, idea, or perspective that provides immediate value
             * Makes a natural connection to a challenge they might be facing
             * Offers help only after providing value
             * Ends with a question that invites their perspective, not just a meeting request
             * Includes your full name, title, and contact information as a real person would
       
        2. Follow-up - Expand the Conversation:
           - If they don't respond, create follow-ups that:
             * Provide new, standalone value each time (never just "checking in")
             * Reference the previous communication naturally
             * Show continued attention to their organization's situation
             * Maintain complete respect for their time and priorities
             * Never use guilt, pressure, or artificial urgency
       
        3. Relationship Nurturing:
           - Develop messages that:
             * Share relevant case studies presented as stories, not sales materials
             * Offer helpful resources with no strings attached
             * Connect them with others in their field who might be helpful
             * Comment thoughtfully on their organization's public achievements or news
       
        WRITING STYLE AND TONE:
        Your writing must:
        - Sound like it came from a specific, real human with a personality
        - Use natural sentence structures and conversational phrasing
        - Vary sentence length and structure as humans naturally do
        - Include occasional conversational elements that show humanity
        - Maintain appropriate professional language while being accessible
        - Be concise but not robotic
       
        AUTHENTICITY MARKERS:
        Include natural elements that sales templates remove:
        - Occasional use of first-person perspective to share relevant experiences
        - Thoughtful questions that show genuine curiosity
        - Brief personal touches that real professionals naturally include
        - References to specific details that show you've done your homework
        - Natural transitions between ideas rather than formulaic structure
       
        FORBIDDEN ELEMENTS:
        Do not use:
        - Any stock sales phrases ("I hope this email finds you well," "I wanted to reach out")
        - Language that artificially creates urgency or scarcity
        - Claims about "revolutionizing" or "disrupting" their industry
        - Statements that could apply to any prospect
        - Multiple exclamation points or excessive formatting
        - Presumptive language about their pain points or needs
        - Manipulative closing techniques or forced calls to action
       
        EXAMPLES OF AUTHENTIC VS. SALES LANGUAGE:
       
        POOR (Sales Style):
        "I hope this email finds you well. I wanted to reach out because we've helped numerous radiology groups like yours streamline their workflows and reduce costs. Our cutting-edge solution has been proven to save 30% on operational expenses. I'd love to schedule a quick 15-minute call to discuss how we can help SimonMed."
       
        GOOD (Authentic Style):
        "I noticed SimonMed recently expanded into the Denver market with three new imaging centers. Having worked on multi-site PACS implementations, I know the challenge of standardizing workflows across newly acquired locations with different legacy systems. We recently helped another radiology group with a similar expansion connect their disparate DICOM sources without replacing existing equipment. I'm happy to share how they approached it if that would be helpful."
       
        POOR (Follow-up):
        "I'm just checking in regarding my previous email about our workflow solution. I'd still love to set up that call to show you how we can help SimonMed save time and money."
       
        GOOD (Follow-up):
        "After our exchange about SimonMed's Denver expansion, I came across a case study about reducing integration time for new imaging centers by 70%. It made me think of your situation - I've attached it in case it's useful. If you have any questions about how they handled the multi-vendor environment, just let me know."
       
        FACILITY CONTEXT:
        {facility_context}
       
        WEBSITE INTELLIGENCE SUMMARY:
        {website_intel_summary}
       
        STAKEHOLDER ECOSYSTEM MAP:
        [Will be populated during execution]
       
        TARGET PRODUCT FOCUS:
        {target_products_str}
        """,
        expected_output="""A set of completely authentic communications that build genuine relationships through valuable insights, relevant observations, and human connection rather than sales tactics.""",
        agent=agents["relationship_advisor"]
    )
   
    # Strategic communication review task
    communication_review_task = Task(
        description=f"""
        Review and enhance communications to create the perfect balance of authentic human connection
        and strategic business alignment:
       
        YOUR ROLE:
        You are receiving draft communications from a relationship advisor. Your job is to review these
        communications to ensure they're both:
        1. Authentically human and non-salesy
        2. Strategically aligned with key business insights and objectives
       
        Your goal is to create the perfect communications that feel completely authentic while subtly
        incorporating the most impactful insights from all previous analyses.
       
        REVIEW PROCESS:
        For each communication, you will:
       
        1. Authentic Voice Evaluation:
           - Ensure it maintains a natural, conversational tone
           - Verify it feels like it comes from a real human with a personality
           - Confirm it's free of all sales clichés and marketing language
           - Check that it focuses on being helpful rather than selling
       
        2. Strategic Alignment Enhancement:
           - Cross-reference with the deal qualification to ensure it addresses key decision drivers
           - Incorporate high-impact value
           - Incorporate high-impact value propositions from the technical analysis in a natural way
           - Subtly integrate ROI concepts without using financial sales language
           - Ensure industry insights are woven in to demonstrate expertise
           - Verify the communication addresses specific pain points identified in research
       
        3. Stakeholder-Specific Optimization:
           - Adjust language based on the stakeholder's role and likely priorities
           - Ensure technical depth is appropriate for the recipient's background
           - Incorporate role-specific concerns identified in stakeholder analysis
           - Customize the tone to match how this stakeholder likely prefers to communicate
       
        4. Pathway Development:
           - Ensure the communication creates a natural path to continue the conversation
           - Align suggested next steps with the strategic objectives
           - Create subtle opportunities for the prospect to engage further
           - Set the foundation for a relationship that will naturally progress to business discussions
       
        STRATEGIC INPUT INTEGRATION:
        You have access to these analyses to incorporate into your review:
       
        INDUSTRY RESEARCH:
        [Industry research from industry_research_specialist]
       
        WEBSITE INTELLIGENCE:
        [Website intelligence from website_intelligence_analyst]
       
        STAKEHOLDER ECOSYSTEM MAP:
        [Stakeholder ecosystem map from stakeholder_ecosystem_mapper]
       
        DEAL QUALIFICATION:
        [Deal qualification from deal_qualifier]
       
        VALUE PROPOSITIONS:
        [Value propositions from technical_value_strategist]
       
        ROI ANALYSIS:
        [ROI analysis from financial_roi_expert]
       
        DRAFT COMMUNICATIONS:
        [Communications from relationship_advisor]
       
        OUTPUT FORMAT:
        For each communication you review, provide:
        1. A brief explanation of the strategic elements you're incorporating
        2. The revised communication with your enhancements
        3. Notes on why your changes maintain authenticity while adding strategic value
       
        REMEMBER:
        - The perfect communication should not FEEL strategic even though it IS
        - It should read like a helpful message from one professional to another
        - The recipient should never feel like they're being "sold to"
        - Strategic elements should be woven in organically and subtly
       
        FACILITY CONTEXT:
        {facility_context}
       
        TARGET PRODUCT FOCUS:
        {target_products_str}
        """,
        expected_output="""A set of perfectly balanced communications that feel authentically human while subtly incorporating key strategic insights that advance business objectives.""",
        agent=agents["strategic_reviewer"]
    )
   
    # Objection handling with specific counters
    objection_handling_task = Task(
        description=f"""
        Develop comprehensive objection handling strategies specific to this prospect and Flux products:
       
        1. Identify Prospect-Specific Objections:
           - Based on the facility profile and website analysis, identify the 8-10 most likely objections:
              * Budget/financial constraints specific to this facility type
              * Technical integration concerns based on their identified systems
              * Timeline/implementation concerns based on their current initiatives
              * Stakeholder-specific objections (IT, clinical, administrative)
              * Competitor-specific objections (if competitors are identified)
       
        2. Create Precision Objection Responses:
           - For each objection, develop:
              * The exact anticipated phrasing of the objection
              * The underlying concern driving the objection
              * A 3-part response: Acknowledge, Address with Flux-specific evidence, Advance
              * Specific data points and examples to overcome the objection
              * A transition question to move the conversation forward
       
        3. Develop Stakeholder-Specific Objection Strategies:
           - Create tailored approaches for:
              * Technical stakeholders (IT, PACS Admins)
              * Clinical leaders (Radiologists, Department Directors)
              * Financial decision-makers (CFO, Finance Director)
              * Executive leadership (CEO, COO, CIO)
       
        4. Create an "Objection Prevention Strategy":
           - Develop proactive approaches to:
              * Address potential objections before they arise
              * Frame conversations to minimize common objections
              * Provide evidence that preemptively counters typical concerns
              * Position Flux advantages to neutralize competitive threats
       
        5. Create a "Closing Strategy" section with:
              * Specific language to use when asking for the sale
              * Techniques for creating urgency without being pushy
              * Methods to secure next steps and maintain momentum
              * Negotiation guidance that protects margin while addressing concerns
       
        Each objection handling strategy must be specifically tailored to this prospect's
        context, using specific Flux product capabilities and relevant success stories
        as evidence.
       
        FACILITY CONTEXT:
        {facility_context}
       
        WEBSITE INTELLIGENCE SUMMARY:
        {website_intel_summary}
       
        TARGET PRODUCT FOCUS:
        {target_products_str}
        """,
        expected_output="A comprehensive objection handling guide that equips salespeople to overcome specific prospect barriers and close deals.",
        agent=agents["objection_specialist"]
    )
   
    # Sales playbook task with complete strategy
    sales_playbook_task = Task(
        description=f"""
        Compile all generated materials into a comprehensive, actionable sales playbook:
       
        1. Executive Opportunity Summary:
           - Create a concise 1-page summary that includes:
              * Revenue potential and timeframe (specific numbers)
              * Key decision-makers and buying process
              * Critical pain points and Flux solutions
              * Compelling reasons to act now
              * Recommended approach and next steps
       
        2. Opportunity Details Section:
           - Compile key findings from all analyses:
              * Industry context and benchmarks
              * Website intelligence insights
              * Stakeholder ecosystem mapping
              * Deal qualification assessment
              * Technical environment and integration points
              * Decision-making process and stakeholders
              * Competitive positioning
       
        3. Solution Strategy Section:
           - Organize all product recommendations:
              * Specific Flux products and configurations
              * Technical value propositions by stakeholder
              * ROI justification and financial analysis
              * Implementation approach and timeline
              * Integration requirements and process
       
        4. Sales Execution Plan:
           - Create a detailed action plan:
              * Day 1 actions to initiate the sale
              * Week 1 outreach sequence with specific tasks
              * 30/60/90 day engagement milestones
              * Stakeholder engagement strategy by role
              * Objection handling and advancement techniques
       
        5. Sales Tools and Resources:
           - Compile ready-to-use sales tools:
              * Personalized email templates
              * Objection handling scripts
              * ROI calculator with preset values
              * Technical comparison matrix
              * Customer success story parallels
       
        The playbook must be completely focused on activities that will generate
        revenue as quickly as possible, with clear guidance on exactly what to say and do
        to close the sale of Flux products to this specific prospect.
       
        FACILITY CONTEXT:
        {facility_context}
       
        WEBSITE INTELLIGENCE SUMMARY:
        {website_intel_summary}
       
        TARGET PRODUCT FOCUS:
        {target_products_str}
        """,
        expected_output="A complete, actionable sales playbook that equips salespeople with everything needed to close the deal quickly and effectively.",
        agent=agents["deal_qualifier"]
    )
   
    # Define the sequence of tasks
    tasks = [
        facility_inference_task,
        stakeholder_ecosystem_task,
        industry_research_task,
        website_intelligence_task,
        deal_qualification_task,
        value_proposition_task,
        roi_task,
        relationship_building_task,
        communication_review_task,
        objection_handling_task,
        sales_playbook_task
    ]
   
    return tasks