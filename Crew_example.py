from crewai import Agent, Task, Crew, Process
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def scrape_website(url):
    """
    Scrape website content to enrich sales intelligence
    
    Args:
        url (str): URL of the company website
        
    Returns:
        dict: Extracted website information
    """
    # Clean the URL by removing any whitespace
    url = url.strip()
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    website_data = {
        "url": url,
        "domain": urlparse(url).netloc,
        "page_title": "",
        "meta_description": "",
        "main_content": "",
        "technologies": [],
        "about_content": "",
        "contacts_found": False,
        "radiology_mentions": 0,
        "pacs_mentions": 0,
        "dicom_mentions": 0,
        "imaging_mentions": 0,
        "error": None
    }
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Request the homepage
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title and meta description
        website_data["page_title"] = soup.title.text.strip() if soup.title else ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            website_data["meta_description"] = meta_desc.get("content", "")
        
        # Extract main content text
        main_content = []
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'li']):
            text = tag.get_text(strip=True)
            if text and len(text) > 20:  # Filter out short snippets
                main_content.append(text)
        
        website_data["main_content"] = "\n".join(main_content)
        
        # Count relevant mentions
        lower_content = website_data["main_content"].lower()
        website_data["radiology_mentions"] = lower_content.count("radiology") + lower_content.count("radiologist")
        website_data["pacs_mentions"] = lower_content.count("pacs") + lower_content.count("archiving")
        website_data["dicom_mentions"] = lower_content.count("dicom")
        website_data["imaging_mentions"] = lower_content.count("imaging") + lower_content.count("image")
        
        # Look for about page
        about_links = []
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            link_text = link.text.lower()
            if 'about' in href or 'about' in link_text:
                if href.startswith('/'):
                    about_links.append(url.rstrip('/') + href)
                elif href.startswith('http'):
                    about_links.append(href)
                else:
                    about_links.append(url.rstrip('/') + '/' + href)
        
        # Scrape about page if found
        if about_links:
            try:
                about_response = requests.get(about_links[0], headers=headers, timeout=10)
                about_soup = BeautifulSoup(about_response.text, 'html.parser')
                
                about_content = []
                for tag in about_soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'li']):
                    text = tag.get_text(strip=True)
                    if text and len(text) > 20:
                        about_content.append(text)
                
                website_data["about_content"] = "\n".join(about_content)
            except:
                pass  # Continue if about page scraping fails
        
        # Check for contact information presence
        contact_indicators = ['contact', 'email', 'phone', 'address', 'location']
        website_data["contacts_found"] = any(indicator in lower_content for indicator in contact_indicators)
        
        return website_data
    
    except Exception as e:
        website_data["error"] = str(e)
        return website_data

def create_flux_sales_accelerator(csv_data=None, target_product="Both", facility_details=None, website_url=None):
    """
    Create a sales-focused acceleration system for Flux Inc's DICOM products
    
    Args:
        csv_data (list): Optional list of contacts from Hubspot/Apollo
        target_product (str): Either "DICOM Printer 2", "Capacitor", or "Both"
        facility_details (dict): Details about the target healthcare facility
        website_url (str): URL of the facility's website
        
    Returns:
        dict: Complete sales acceleration package including personalized outreach
    """
    # Check if OpenAI API key is set
    if "OPENAI_API_KEY" not in os.environ or not os.environ["OPENAI_API_KEY"]:
        raise ValueError("OpenAI API key is not set in environment variables. Please provide a valid API key.")
    
    # Scrape website if URL provided
    website_data = None
    if website_url:
        website_url = website_url.strip()  # Clean any whitespace
        website_data = scrape_website(website_url)
    
    # Configure specialized agents
    website_intelligence_specialist = Agent(
        role="Healthcare Website Intelligence Analyst",
        goal="Extract actionable sales intelligence from prospect websites to increase deal size and close rates",
        backstory="""You are an expert in analyzing healthcare organization websites to extract insights that drive sales. 
        You have a unique ability to identify buying signals, pain points, and strategic initiatives from website content 
        that others miss. Your analyses consistently reveal opportunities to position Flux's DICOM products as strategic 
        solutions rather than tactical purchases, increasing average deal size by 40%. You can spot the hidden signals 
        that indicate readiness to purchase, competitive displacement opportunities, and specific stakeholder priorities 
        just from reviewing a company's web presence. Your intelligence reports have directly contributed to closing 
        over $15M in healthcare IT sales by identifying the right messaging, timing, and approach for each prospect.""",
        verbose=True,
        allow_delegation=True,
        llm="gpt-4"
    )
    
    deal_qualifier = Agent(
        role="Healthcare Deal Qualification Specialist",
        goal="Identify and prioritize high-value deals for Flux's DICOM products",
        backstory="""You are an expert in healthcare IT sales with 15+ years of experience closing
        6 and 7-figure deals for imaging solutions. You have a precise understanding of which healthcare 
        facilities represent the highest revenue potential for DICOM solutions like Flux's products.
        You know exactly how to analyze a facility's size, imaging volume, and technical environment to 
        determine deal size, sales cycle, and closing probability. Your qualification process consistently 
        delivers deals that close at a 40% higher rate than industry average.""",
        verbose=True,
        allow_delegation=True,
        llm="gpt-4"
    )
    
    technical_value_strategist = Agent(
        role="DICOM Technical Value Strategist",
        goal="Create compelling technical value propositions that drive sales of Flux products",
        backstory="""You are a former PACS administrator who now specializes in translating technical benefits 
        into sales-winning value propositions. You have deep technical knowledge of DICOM standards, imaging 
        workflows, and integration requirements in healthcare environments. You excel at identifying exactly 
        how Flux's DICOM Printer 2 and Capacitor solve specific technical pain points that prospects are willing 
        to pay premium prices to fix. Your technical value propositions have a proven track record of shortening 
        sales cycles by 35% and increasing average deal size by 28%.""",
        verbose=True,
        allow_delegation=True,
        llm="gpt-4"
    )
    
    financial_roi_expert = Agent(
        role="Healthcare ROI Specialist",
        goal="Develop compelling financial justifications for Flux product investments",
        backstory="""You are a healthcare financial analyst who specializes in creating ROI models that get deals 
        approved. You understand both the technical aspects of DICOM solutions and the financial priorities of 
        healthcare organizations. You excel at quantifying the financial impact of workflow improvements, 
        infrastructure optimizations, and technical capabilities in terms that healthcare financial decision-makers 
        respond to. Your ROI models have been used to close over $25M in healthcare IT sales, with CFOs frequently 
        commenting on the clarity and persuasiveness of your financial justifications.""",
        verbose=True,
        allow_delegation=True,
        llm="gpt-4"
    )
    
    sales_email_specialist = Agent(
        role="Healthcare IT Sales Messaging Expert",
        goal="Create high-converting personalized emails that drive sales engagements",
        backstory="""You are an expert in crafting personalized sales emails that consistently achieve 
        30%+ response rates in healthcare IT sales. You understand the psychology of different healthcare 
        stakeholders and know exactly how to craft messages that resonate with radiologists, PACS administrators, 
        IT directors, and C-level executives. You excel at creating concise, compelling messages that clearly 
        articulate the specific value of Flux's products to each recipient, with calls-to-action that drive 
        immediate engagement. Your email templates are consistently praised for their personalization and 
        relevance, driving sales conversations that convert to revenue.""",
        verbose=True,
        allow_delegation=True,
        llm="gpt-4"
    )
    
    objection_specialist = Agent(
        role="DICOM Sales Closing Expert",
        goal="Create objection handling strategies that convert prospects to customers",
        backstory="""You are an elite healthcare IT sales closer with a 72% close rate on qualified opportunities.
        You have deep experience overcoming the specific objections that arise during DICOM solution sales
        processes. You know exactly what concerns different stakeholders will raise about budget, integration,
        training, and competitive alternatives, and have developed proven techniques to address each one.
        You specialize in turning objections into opportunities to highlight the unique advantages of Flux's
        products, creating momentum that drives deals to close faster and at higher values.""",
        verbose=True,
        allow_delegation=True,
        llm="gpt-4"
    )
    
    # Create facility context string
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
    
    # Website intelligence task
    website_intelligence_task = Task(
        description=f"""
        Analyze the target prospect's website and extract actionable sales intelligence:
        
        1. Strategic Sales Opportunities:
           - Identify specific sales opportunities based on website content
           - Determine if there are any recent initiatives or changes that create urgency
           - Find evidence of strategic priorities that Flux products can address
           - Evaluate readiness signals that indicate buying readiness
        
        2. Competitive Intelligence:
           - Identify any mentions of competing products or vendors
           - Determine if there are opportunities for competitive displacement
           - Analyze how the prospect describes their technical environment
           - Look for gaps or pain points in their current solutions
        
        3. Stakeholder Intelligence:
           - Identify key decision-makers mentioned on the website
           - Determine organizational structure and reporting relationships
           - Find evidence of decision-making criteria or priorities
           - Identify potential champions or blockers
        
        4. Timing and Budget Signals:
           - Look for evidence of budget cycles or fiscal planning
           - Identify any time-sensitive initiatives or compliance deadlines
           - Find signals of recent or planned technology investments
           - Determine if there are any announced strategic projects
        
        5. Create a clear "Website Intelligence Summary" that outlines:
           - Top 3 sales opportunities identified from the website
           - Specific language from the website that can be used in sales communications
           - Recommended approach based on website findings
           - Potential objections or obstacles inferred from website content
        
        If no website data is available, indicate this and provide general guidance on finding 
        this intelligence through other means.
        
        WEBSITE DATA:
        {website_data if website_data else "No website data available."}
        
        FACILITY CONTEXT:
        {facility_context}
        
        TARGET PRODUCT FOCUS:
        {target_product}
        """,
        expected_output="A comprehensive website intelligence report that reveals actionable sales opportunities and insights.",
        agent=website_intelligence_specialist
    )
    
    # Qualification task - now references website intelligence
    qualification_task = Task(
        description=f"""
        Analyze the target healthcare facility and create a detailed sales qualification report:
        
        1. Determine the potential deal size (clearly state expected revenue range)
        2. Score the opportunity on a scale of 1-10 for probability of closing
        3. Identify the specific decision-makers who can approve a purchase
        4. Determine which Flux product (DICOM Printer 2, Capacitor, or both) represents the best sales opportunity
        5. Highlight specific technical pain points that will drive purchasing decisions
        6. Recommend a sales approach that will maximize deal size and minimize sales cycle
        7. Clearly identify 3 specific reasons why this prospect NEEDS Flux products now
        
        Focus entirely on factors that will drive a sale and generate revenue. The qualification
        must provide actionable intelligence that will help close a deal.
        
        Incorporate the website intelligence findings into your qualification. Pay special
        attention to signals of buying readiness, budget availability, and specific pain points
        that create urgency.
        
        FACILITY CONTEXT:
        {facility_context}
        
        TARGET PRODUCT FOCUS:
        {target_product}
        """,
        expected_output="A precise sales qualification that accurately identifies revenue potential, decision-makers, and closing strategy.",
        agent=deal_qualifier
    )
    
    value_proposition_task = Task(
        description=f"""
        Create compelling, sales-focused value propositions for Flux's products:
        
        1. For each recommended product (DICOM Printer 2, Capacitor, or both), develop:
           - A clear statement of how the product solves the prospect's most painful problems
           - Specific technical capabilities that differentiate from competing solutions
           - Concrete examples of how similar facilities have benefited (with metrics)
           - Clear positioning against competitive alternatives
        
        2. Customize value propositions for key stakeholders:
           - Technical buyers: Focus on integration ease, reliability, and performance
           - Economic buyers: Focus on cost savings, ROI, and operational efficiency
           - Clinical users: Focus on workflow improvements and clinical outcomes
        
        3. Highlight the key competitive advantages that make Flux's solutions worth paying premium prices for:
           - Feature comparisons against common alternatives
           - Unique capabilities that only Flux offers
           - Long-term strategic advantages
        
        Each value proposition must be compelling enough to drive purchase decisions and
        justify premium pricing. Focus on benefits that prospects will actually pay for.
        
        Use the website intelligence analysis to tailor your value propositions to the
        specific language, priorities, and initiatives mentioned on the prospect's website.
        
        FACILITY CONTEXT:
        {facility_context}
        
        TARGET PRODUCT FOCUS:
        {target_product}
        """,
        expected_output="A set of powerful value propositions that clearly articulate why prospects should buy Flux products.",
        agent=technical_value_strategist
    )
    
    roi_task = Task(
        description=f"""
        Develop a compelling financial justification for investing in Flux's products:
        
        1. Create a detailed ROI model that includes:
           - Implementation and licensing costs
           - Staffing and operational impacts (time savings, efficiency gains)
           - Infrastructure cost reductions
           - Revenue impact through improved workflows
           - Risk mitigation value (compliance, security, reliability)
        
        2. Present ROI in multiple formats:
           - 1-year, 3-year, and 5-year projections
           - Capital expense vs. operational expense analysis
           - Total cost of ownership compared to alternatives
           - Payback period with clear milestones
        
        3. Provide financial justifications tailored to healthcare finance priorities:
           - Budget cycle alignment
           - Depreciation advantages
           - Operating vs. capital expenditure considerations
           - Risk reduction financial benefits
        
        The ROI model must be detailed enough to stand up to financial scrutiny while
        presenting a clear and compelling case for purchasing Flux products.
        
        Use any financial terminology or priorities identified in the website intelligence
        to align your ROI model with the prospect's financial language and priorities.
        
        FACILITY CONTEXT:
        {facility_context}
        
        TARGET PRODUCT FOCUS:
        {target_product}
        """,
        expected_output="A comprehensive, credible ROI analysis that financially justifies investment in Flux products.",
        agent=financial_roi_expert
    )
    
    personalized_email_task = Task(
        description=f"""
        Create highly personalized, high-converting sales emails for the identified decision-makers:
        
        1. For each key stakeholder, develop a personalized initial outreach email that:
           - Opens with a highly specific reference to their role and challenges
           - Clearly articulates the specific value Flux products offer to THEM
           - Includes 1-2 relevant proof points or customer examples
           - Ends with a clear, low-friction call to action
           - Has a subject line with 50%+ open rate potential
        
        2. Develop 3-5 follow-up email templates that:
           - Reference the initial outreach
           - Provide additional value with each touch
           - Address likely concerns proactively
           - Maintain momentum toward a sales conversation
        
        3. Include specific guidance on:
           - Optimal send timing and sequence
           - Personalization elements to add for each prospect
           - Response handling approaches
        
        Every email must be focused on generating a response and moving toward a sales
        conversation that can close a deal. Avoid marketing language in favor of direct,
        value-focused sales communication.
        
        Incorporate specific language, initiatives, and priorities from the website intelligence
        analysis to make your emails highly personalized and relevant. Reference specific content
        from their website where appropriate to demonstrate research and relevance.
        
        FACILITY CONTEXT:
        {facility_context}
        
        TARGET PRODUCT FOCUS:
        {target_product}
        """,
        expected_output="A set of highly personalized, response-generating email templates for each key decision-maker.",
        agent=sales_email_specialist
    )
    
    objection_handling_task = Task(
        description=f"""
        Develop comprehensive objection handling strategies specific to Flux's products:
        
        1. Identify the top 10 sales objections likely to arise during the sales process, including:
           - Price/budget concerns
           - Technical integration challenges
           - Implementation timeline concerns
           - Competitive alternative considerations
           - Status quo bias/resistance to change
           - Staffing/training concerns
        
        2. For each objection, create:
           - The exact phrasing of how the objection will likely be expressed
           - The underlying concern behind the stated objection
           - A 3-part response framework: acknowledge, address with evidence, advance
           - Specific evidence points about Flux products to overcome the objection
           - A transition question to move the conversation forward
        
        3. Create a "closing strategy" section that includes:
           - Specific language to use when asking for the sale
           - Techniques for creating urgency without being pushy
           - Negotiation guidance to maximize deal size
           - Recommended concessions (if necessary) that protect margin
        
        Every objection handling strategy must be specifically tailored to Flux's products
        and focused on moving deals to close as quickly as possible.
        
        Use insights from the website intelligence to anticipate specific objections this
        prospect might raise based on their priorities, language, and initiatives mentioned
        on their website.
        
        FACILITY CONTEXT:
        {facility_context}
        
        TARGET PRODUCT FOCUS:
        {target_product}
        """,
        expected_output="A comprehensive objection handling guide that equips salespeople to overcome barriers and close deals.",
        agent=objection_specialist
    )
    
    sales_playbook_task = Task(
        description=f"""
        Compile all generated sales materials into a comprehensive, actionable sales playbook:
        
        1. Executive summary of the opportunity:
           - Clear statement of expected revenue and timeline
           - Key decision-makers and their priorities
           - Critical selling points that will drive the decision
           - Recommended product focus and approach
        
        2. Organize all generated materials in a sales-optimized sequence:
           - Website intelligence summary
           - Qualification and opportunity assessment
           - Value propositions by stakeholder
           - ROI justification and financial analysis
           - Personalized outreach templates
           - Objection handling guide and closing strategy
        
        3. Add a "Quick Action Plan" section with:
           - Day 1 actions to initiate the sale
           - Week 1 outreach sequence
           - 30-day engagement plan
           - 60-90 day closing strategy
        
        The final playbook must be completely focused on activities that will generate
        revenue as quickly as possible, with clear guidance on exactly what to say and do
        to close the sale.
        
        Ensure that the website intelligence findings are woven throughout the playbook,
        providing context and personalization for each section.
        
        FACILITY CONTEXT:
        {facility_context}
        
        TARGET PRODUCT FOCUS:
        {target_product}
        """,
        expected_output="A complete, actionable sales playbook that equips salespeople with everything needed to close the deal.",
        agent=deal_qualifier
    )
    
    # Define the sequence of tasks
    tasks = [
        website_intelligence_task,
        qualification_task,
        value_proposition_task,
        roi_task,
        personalized_email_task,
        objection_handling_task,
        sales_playbook_task
    ]
    
    # Define the crew with all agents
    flux_sales_crew = Crew(
        agents=[
            website_intelligence_specialist,
            deal_qualifier, 
            technical_value_strategist, 
            financial_roi_expert, 
            sales_email_specialist, 
            objection_specialist
        ],
        tasks=tasks,
        verbose=True,
        process=Process.sequential  # Tasks will be executed in sequence to build on previous outputs
    )
    
    # Create a dictionary to store the specific outputs
    results = {
        "website_intelligence": "",
        "qualification": "",
        "value_propositions": "",
        "roi_analysis": "",
        "personalized_emails": "",
        "objection_handling": "",
        "complete_playbook": ""
    }
    
    # Execute tasks one by one to ensure we capture the output of each task individually
    for i, task in enumerate(tasks):
        # Execute a single task
        if i == 0:  # Website intelligence task
            output = website_intelligence_specialist.execute_task(task)
            results["website_intelligence"] = output
        elif i == 1:  # Qualification task
            output = deal_qualifier.execute_task(task)
            results["qualification"] = output
        elif i == 2:  # Value proposition task
            output = technical_value_strategist.execute_task(task)
            results["value_propositions"] = output
        elif i == 3:  # ROI task
            output = financial_roi_expert.execute_task(task)
            results["roi_analysis"] = output
        elif i == 4:  # Personalized email task
            output = sales_email_specialist.execute_task(task)
            results["personalized_emails"] = output
        elif i == 5:  # Objection handling task
            output = objection_specialist.execute_task(task)
            results["objection_handling"] = output
        elif i == 6:  # Sales playbook task
            output = deal_qualifier.execute_task(task)
            results["complete_playbook"] = output
    
    return results

if __name__ == "__main__":
    # Example facility details - can be replaced with actual data
    facility_details = {
        "name": "Metropolitan Imaging Center",
        "location": "Chicago, IL",
        "type": "Multi-specialty outpatient imaging center",
        "size": "3 locations, 45,000 studies annually",
        "current_infrastructure": "GE PACS (7 years old), Siemens and Philips modalities",
        "key_challenge": "Slow image retrieval, limited remote access capabilities",
        "recent_events": "New radiologist leadership hired, considering workflow modernization",
        "budget_cycle": "Fiscal year begins July 1, capital requests due by March 15",
        "pain_points": [
            "17-minute average retrieval time for prior studies",
            "No tablet/mobile viewing capabilities",
            "Limited integration with referring physician EMRs",
            "Manual CD importing process taking 2 FTE staff",
            "Multiple disconnected DICOM workflows between locations"
        ]
    }
    
    # Set API key if running directly
    # if "OPENAI_API_KEY" not in os.environ:
    #     os.environ["OPENAI_API_KEY"] = "your-api-key-here"
    
    website_url = "www.example.com"  # Example website
    
    # Generate the sales playbook
    sales_materials = create_flux_sales_accelerator(
        facility_details=facility_details,
        website_url=website_url,
        target_product="Both"
    )
    print(sales_materials)