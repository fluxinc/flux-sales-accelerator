"""
Flux Inc Product Knowledge Base
This module defines detailed product information that CrewAI agents can use to generate
more specific and targeted sales materials.
"""

class ProductKnowledge:
    def __init__(self):
        self.products = {
            "DICOM Printer 2": self._get_dicom_printer2_info(),
            "Capacitor": self._get_capacitor_info(),
            "TuPACS": self._get_tupacs_info(),
            "Gobbler": self._get_gobbler_info()
        }
        
        self.detailed_use_cases = {
            "Capacitor": self._get_capacitor_detailed_use_cases(),
            "DICOM Printer 2": self._get_dicom_printer_detailed_use_cases()
        }
        
        self.company_info = self._get_company_info()
        self.competitive_analysis = self._get_competitive_analysis()
        self.customer_success_stories = self._get_customer_success_stories()
        self.industry_challenges = self._get_industry_challenges()
        
    def _get_dicom_printer2_info(self):
        """Detailed information about DICOM Printer 2"""
        return {
            "name": "DICOM Printer 2",
            "tagline": "Send Anything to PACS",
            "summary": "DICOM Printer adds query, store and print functionality to any application, enabling seamless integration of documents and images into PACS.",
            "key_features": [
                "Receive documents from print commands or pick up images/PDFs from designated folders",
                "Automatically extract document text to populate DICOM attributes",
                "Make decisions based on extracted values and configurable workflows",
                "Conditionally query Work-list and PACS",
                "Annotate images and documents with text and graphics",
                "Store to multiple destination PACS or print to film on dry imagers",
                "Share across networks to improve workflows at entire sites"
            ],
            "use_cases": [
                "Legacy device integration - enabling old devices to store to modern PACS",
                "Document integration - getting non-DICOM documents into PACS",
                "Workflow automation - reducing manual steps in document handling",
                "Work-list integration - appending patient data to outgoing series"
            ],
            "technical_specs": {
                "supported_modalities": "Any application or device that prints through Windows, or any application that can save PDF, images or DCM files to disk",
                "supported_pacs": "All major PACS systems",
                "dicom_services": [
                    "Patient, Study, and Work-list Root Query",
                    "Secondary Capture Store",
                    "Gray scale and Color Print"
                ],
                "system_requirements": [
                    "x86 or x64 CPU at 2 GHz minimum",
                    "1 GB memory for 32-bit and 2 GB for 64-bit operation",
                    "Windows XP SP3, Vista, 7, 8, 2003 Server, or 2008 Server",
                    "200 MB of storage, for binary and first three years of log files",
                    "Access to destination systems and data sources"
                ]
            },
            "pricing": {
                "first_seat": "$750 + 60% yearly maintenance",
                "additional_seats": "Decremental pricing ($25 less each time, applied to whole order)",
                "bulk_pricing": "$375 each after 15 seats"
            },
            "unique_selling_points": [
                "Legacy device integration saves thousands in equipment replacement costs",
                "Automates document handling, drastically reducing manual workflow steps",
                "Simple pricing model with decremental costs for additional seats",
                "Shockingly responsive support with worldwide coverage"
            ],
            "pain_points_addressed": [
                "Manual document printing and scanning processes",
                "Legacy devices that can't connect to modern PACS",
                "Disconnected workflows between departments",
                "High costs of replacing functional but non-DICOM compatible equipment"
            ]
        }
    
    def _get_capacitor_info(self):
        """Detailed information about DICOM Capacitor"""
        return {
            "name": "DICOM Capacitor",
            "tagline": "Smart DICOM store-forward router",
            "summary": "DICOM Capacitor is a smart DICOM store-forward router that routes images from any source to any destination in clinical settings, especially when dealing with unreliable networks, high traffic volumes, or specific routing needs.",
            "key_features": [
                "Reliable Image Transfer - handles large volumes of DICOM data with compliant transfers",
                "Compression - uses standard syntaxes like JPEG 2000 to reduce storage costs",
                "Anonymization - configurable protection of patient privacy",
                "Encryption - optional security during image transfer",
                "Flexible Routing - directs DICOM images to multiple destinations",
                "Seamless Data Migrations - streamlines large-scale data migrations",
                "Fault Tolerance - recovers from errors and network outages",
                "Worklist Management - queries, caches, and manipulates DICOM worklist data",
                "Multi-Threaded Processing - parallel processing for faster operations",
                "Stateless Operation - can stop and start without data loss",
                "Scalable - available as Docker image for Kubernetes deployment"
            ],
            "use_cases": [
                "Mobile Imaging Units - caching data with intermittent connectivity",
                "Remote Sites - scheduling large transfers during off-peak hours",
                "Unreliable Networks - ensuring successful transfers despite interruptions",
                "Vendor Compatibility - resolving issues between different vendors' equipment",
                "Data Migrations - transferring large datasets during system upgrades"
            ],
            "technical_specs": {
                "supported_platforms": ["Windows", "Linux", "macOS", "ARM architectures (including Raspberry Pi)"],
                "dicom_services": [
                    "C-ECHO", "C-STORE", "C-FIND", "C-MOVE", "QUERY-RETRIEVE", "Storage Commitment"
                ],
                "compression_formats": ["JPEG 2000"],
                "deployment_options": ["Traditional installation", "Docker (fluxinc/dicom-capacitor:latest)", "Kubernetes"]
            },
            "benefits": [
                "Cost Savings - compression reduces storage requirements",
                "Enhanced Data Security - encryption and anonymization protect patient information",
                "Improved Workflow Efficiency - increased DICOM Modality Worklist compatibility",
                "Reliable Operation - fault tolerance ensures data integrity"
            ],
            "unique_selling_points": [
                "Multi-platform support including ARM for maximum flexibility",
                "Docker and Kubernetes support for modern, scalable deployment",
                "Fault-tolerant design for operation in challenging network environments",
                "Multi-threaded processing for optimal performance with large datasets"
            ],
            "pain_points_addressed": [
                "Unreliable network connections disrupting image transfers",
                "Storage costs for large imaging datasets",
                "Managing data privacy and security requirements",
                "Integrating equipment from multiple vendors",
                "Complex data migration processes"
            ]
        }
    
    def _get_tupacs_info(self):
        """Detailed information about TuPACS"""
        return {
            "name": "TuPACS",
            "tagline": "Scan and send to PACS",
            "summary": "TuPACS scans, searches DICOM worklists, and sends to PACS, providing simplified document and study management.",
            "key_features": [
                "Instant Activation - Pops up immediately after scanning",
                "User-Friendly - Super simple user interface",
                "Universal Compatibility - Works with all scanners and PACS brands",
                "Customizable - Rearrange and rotate pages before storing",
                "Background Storage - Continuously saves to PACS while you work",
                "Effortless Matching - Match worklist by Patient ID, Accession, or Name"
            ],
            "benefits": [
                "Cheaper than competitors, saves thousands of dollars annually",
                "Frees up valuable time for your team and reduces labor expenses",
                "Eliminates the need for expensive off-site storage solutions"
            ],
            "technical_specs": {
                "system_requirements": [
                    "Windows 7 or higher",
                    "A document scanner that supports Windows Image Acquisition (WIA) or scan-to-file function",
                    "Microsoft .NET 4.0 Client Profile",
                    "A DICOM 3.0 compliant PACS"
                ],
                "compatibility": [
                    "Fully compatible with Windows 11",
                    "Works with all major PACS vendors"
                ]
            },
            "unique_selling_points": [
                "Intuitive interface requiring minimal training",
                "Customizable pricing to fit different budgets",
                "Responsive worldwide support network",
                "Seamless integration with existing workflows"
            ],
            "pain_points_addressed": [
                "Manual document scanning and import processes",
                "Complex user interfaces requiring extensive training",
                "High costs of competing document management solutions",
                "Time-consuming manual patient matching workflows"
            ]
        }
    
    def _get_gobbler_info(self):
        """Detailed information about DICOM Gobbler"""
        return {
            "name": "DICOM Gobbler",
            "tagline": "DICOMDIR disc and USB to PACS",
            "summary": "Gobbler pops-up automatically when you insert a DICOMDIR disc, asks for an MRN, and then quietly stores the contents to your local PACS.",
            "key_features": [
                "Lives mostly in the system tray with polite notifications",
                "Automatically detects CDs, DVDs and USB sticks with DICOM files",
                "Identifies patient name and prompts for Patient ID",
                "Replaces Patient ID on all images",
                "Optional decompression of JPEG studies to RGB for compatibility",
                "Sends all instances to PACS",
                "Reports failures and saves exams to temporary folders for retry",
                "Unobtrusive and easy to use interface"
            ],
            "technical_specs": {
                "system_requirements": [
                    "Windows 7 or higher",
                    "Microsoft .NET 4.0 Client Profile",
                    "A DICOM 3.0 compliant PACS",
                    "A CD/DVD tray or USB port",
                    "~1 GB of hard drive space for temporary storage"
                ]
            },
            "unique_selling_points": [
                "Automated detection of DICOMDIR media",
                "Minimal user interaction required",
                "Unobtrusive system tray operation",
                "Simple patient ID replacement process"
            ],
            "pain_points_addressed": [
                "Manual import of outside CDs and media",
                "Complex workflows for importing external studies",
                "Patient identity reconciliation challenges",
                "Time wasted on file format compatibility issues"
            ]
        }
    
    def _get_capacitor_detailed_use_cases(self):
        """Detailed use cases for Capacitor"""
        return {
            "mobile_imaging": {
                "problem": "Mobile radiology units face critical workflow challenges with intermittent connectivity, causing delays in patient care",
                "solution": "Capacitor's intelligent store-forward caching that ensures continuous operation regardless of network status",
                "specific_benefits": {
                    "technologist_focus": "Technologists can focus on patient care rather than troubleshooting connectivity issues",
                    "operational_continuity": "Exams are automatically uploaded when connectivity is restored without manual intervention",
                    "bandwidth_optimization": "Smart compression reduces cellular data usage by up to 35%",
                    "reliability": "99.9% successful transmission rate even in challenging network environments"
                },
                "proven_examples": [
                    "UPenn's highly-mobile radiology units use Capacitor as their 'fire-and-forget' repeater solution",
                    "Mobile mammography services across multiple hospital systems"
                ]
            },
            "cross_vendor_compatibility": {
                "problem": "Integrating equipment from different vendors creates persistent DICOM compatibility issues",
                "solution": "Capacitor's vendor emulation and DICOM tag manipulation capabilities",
                "specific_benefits": {
                    "seamless_integration": "Makes diverse equipment behave as if they're from the same vendor",
                    "reduced_errors": "Eliminates patient mismatches and failed transfers through intelligent tag correction",
                    "broader_compatibility": "Expands the range of supported PACS systems for legacy equipment",
                    "future_proofing": "Helps facilities maintain operations during mixed-vendor upgrade cycles"
                },
                "proven_examples": [
                    "Major mammography vendors now use Capacitor as their preferred pathway to PACS",
                    "Multi-vendor environments in hospital systems with diverse department needs"
                ]
            },
            "format_conversion": {
                "problem": "Legacy CTO and SCO formats aren't compatible with modern PACS systems",
                "solution": "Capacitor's real-time conversion to modern BTO format",
                "specific_benefits": {
                    "investment_protection": "Extends the life of older equipment by 5-7 years",
                    "cost_avoidance": "Saves $75,000-$150,000 per modality replacement",
                    "migration_simplification": "Converts formats during migration with minimal disruption",
                    "workflow_continuity": "Maintains clinical operations during technology transitions"
                },
                "proven_examples": [
                    "Hospital system that migrated 1.2 million legacy studies without downtime",
                    "Imaging centers that maintained full operational capacity during PACS upgrades"
                ]
            },
            "intelligent_prefetch": {
                "problem": "Radiologists and technologists face delays waiting for prior studies to be retrieved",
                "solution": "Capacitor's worklist-based prefetching with smart filtering",
                "specific_benefits": {
                    "zero_wait_time": "Prior studies are ready before the patient arrives",
                    "resource_optimization": "Transfers occur during off-peak hours to reduce network congestion",
                    "relevant_priors_only": "Smart filtering ensures only the most relevant studies are prefetched",
                    "multi_source_management": "Coordinates retrieval from archives, VNA, and multiple PACS systems"
                },
                "proven_examples": [
                    "Mammography department that eliminated waiting for prior comparison studies",
                    "Multi-site hospital that streamlined workflow across tiered storage architecture"
                ]
            },
            "dicom_tag_harmonization": {
                "problem": "Inconsistent DICOM tags cause display issues and hanging protocol failures",
                "solution": "Capacitor's sophisticated DICOM tag manipulation capabilities",
                "specific_benefits": {
                    "standardized_naming": "Normalizes view descriptions for consistent display (e.g., 'BTO_TOMO, L-CC, PRIME' → 'L CC Tomosynthesis')",
                    "improved_integration": "Ensures compatibility with AI and CAD systems that rely on standardized tags",
                    "accurate_display": "Corrects view position codes to ensure proper image orientation",
                    "consistent_appearance": "Standardizes series descriptions across all vendors for uniform worklists"
                },
                "proven_examples": [
                    "Multi-vendor breast imaging center that unified nomenclature across all systems",
                    "Radiology department that improved integration with new AI analysis tools"
                ]
            }
        }
    
    def _get_dicom_printer_detailed_use_cases(self):
        """Detailed use cases for DICOM Printer 2"""
        return {
            "legacy_system_integration": {
                "problem": "Valuable clinical documents and images from older systems can't integrate with modern PACS",
                "solution": "DICOM Printer 2's ability to convert any printable document into DICOM-compliant format",
                "specific_benefits": {
                    "workflow_efficiency": "Eliminates manual scanning and uploading processes, saving 2.5 hours daily per department",
                    "error_reduction": "Reduces patient matching errors by 93% through automated metadata extraction",
                    "cost_savings": "Eliminates paper costs and physical storage requirements",
                    "clinical_accessibility": "Makes all patient documents available in a single viewer"
                },
                "proven_examples": [
                    "Dental practice network that eliminated paper charting while maintaining legacy practice management software",
                    "Cardiology group that unified reporting across 3 different reporting systems"
                ]
            },
            "document_workflow_automation": {
                "problem": "Manual document handling creates bottlenecks in imaging workflows",
                "solution": "DICOM Printer 2's automated matching and metadata extraction capabilities",
                "specific_benefits": {
                    "time_savings": "Reduces document processing time from minutes to seconds per document",
                    "accuracy": "Automatically extracts and populates DICOM attributes from document text",
                    "integration": "Seamlessly connects non-DICOM systems to the imaging workflow",
                    "accessibility": "Makes documents immediately available to all clinical staff"
                },
                "proven_examples": [
                    "Hospital that processes over 100,000 documents yearly with DICOM Printer 2",
                    "Multi-site radiology practice that unified documentation across disparate systems"
                ]
            },
            "true_size_printing": {
                "problem": "Digital documents printed to film lose accurate size proportions and calibration",
                "solution": "DICOM Printer 2's true size printing capabilities",
                "specific_benefits": {
                    "diagnostic_accuracy": "Maintains accurate measurements for diagnostic purposes",
                    "calibration_preservation": "Preserves scales and measurement markers in printed output",
                    "standardization": "Ensures consistent sizing across different viewing contexts",
                    "compatibility": "Works with all major dry imagers including AGFA Drystar and Carestream Dryview"
                },
                "proven_examples": [
                    "Orthopedic practice measuring fracture alignment with true-size digital templating",
                    "Veterinary clinic printing properly scaled radiographs for surgical planning"
                ]
            },
            "multimedia_integration": {
                "problem": "Non-DICOM multimedia (photos, videos, PDFs) can't be stored in PACS",
                "solution": "DICOM Printer 2's ability to convert multimedia content to DICOM format",
                "specific_benefits": {
                    "unified_patient_record": "Consolidates all patient media in a single PACS system",
                    "workflow_simplification": "Eliminates need for separate media management systems",
                    "improved_documentation": "Enhances patient records with rich multimedia content",
                    "accessibility": "Makes multimedia content available throughout the enterprise"
                },
                "proven_examples": [
                    "Dermatology practice integrating clinical photos with radiology studies",
                    "Surgical department documenting procedures with converted video clips"
                ]
            }
        }
    
    def _get_company_info(self):
        """Information about Flux Inc as a company"""
        return {
            "name": "Flux Inc",
            "reach": {
                "customers": "Over 3,000 customers worldwide",
                "resellers": "Over 300 active resellers",
                "regions": {
                    "North America": "Active in over 500 radiology facilities, vendor relationships with customers such as SIEMENS, Philips, GE and Newman Medical",
                    "Latin America": "Active in more than 2,000 radiology centers, with extensive presence in dental radiography printing and PACS",
                    "Asia": "Active in almost 500 radiology centers and in partnership with several ultrasound and x-ray suppliers",
                    "Europe": "Numerous vendor partnerships, including Acteon, which asked us to create a DICOM layer for its award-winning WhiteFox cone beam CT instrument",
                    "Oceania": "Almost 100 radiology centers that store CT in PACS using our tools"
                }
            },
            "value_proposition": "Best value at the best prices for DICOM connectivity and workflow solutions",
            "support": "Worldwide network of support specialists providing responsive assistance",
            "contact": {
                "phone": "+1 (416) 900-1007",
                "email": "sales@fluxinc.co",
                "web": "fluxinc.co"
            }
        }
    
    def _get_competitive_analysis(self):
        """Competitive analysis information"""
        return {
            "DICOM Routing": {
                "main_competitor": "Laurel Bridge",
                "competitor_weaknesses": [
                    "Significantly higher price point",
                    "More complex implementation",
                    "Higher ongoing maintenance costs"
                ],
                "flux_advantages": [
                    "Best value at significantly lower prices",
                    "Easier implementation and management",
                    "Multi-platform support including ARM architecture",
                    "Docker containerization for modern deployments"
                ]
            },
            "DICOM Printer": {
                "market_position": "Unique solution with limited direct competition",
                "flux_advantages": [
                    "Established since 2006 with thousands of deployments",
                    "Simple Windows printer integration",
                    "Extensive workflow automation capabilities",
                    "Decremental pricing model for multi-seat deployments"
                ]
            },
            "Document Management": {
                "competitors": "Various enterprise document management solutions",
                "flux_advantages": [
                    "Purpose-built for healthcare imaging workflows",
                    "Direct PACS integration",
                    "Significantly lower cost",
                    "Simpler user interface requiring minimal training"
                ]
            }
        }
    
    def _get_customer_success_stories(self):
        """Sample customer success stories"""
        return [
            {
                "customer": "Ellesmere X-Ray",
                "product": "DICOM Printer 2",
                "challenge": "Manual document handling creating workflow bottlenecks",
                "solution": "Implemented DICOM Printer 2 for automated document processing",
                "results": "Silently and accurately processes over 100,000 documents yearly for a network of radiology facilities",
                "region": "Canada"
            },
            {
                "customer": "Parkland Hospital",
                "product": "Combobulator",
                "challenge": "Integration of multiple imaging devices with PACS",
                "solution": "First Combobulator deployment",
                "results": "Flawless deployment supporting eight heavily utilized devices",
                "region": "Dallas, USA"
            },
            {
                "customer": "Siemens Healthcare",
                "product": "Custom Integration Gateway",
                "challenge": "Measurement transmission from ultrasound carts",
                "solution": "Created measurement transmission gateways for Radiology and Cardiology ultrasound carts",
                "results": "Seamless integration of measurement data with reporting systems",
                "region": "Mountain View, USA"
            },
            {
                "customer": "Acteon",
                "product": "Custom DICOM Layer",
                "challenge": "Adding DICOM capability to cone-beam CT instrument",
                "solution": "Created a DICOM layer for their award-winning WhiteFox cone-beam CT instrument",
                "results": "Enhanced market position with seamless PACS integration capability",
                "region": "Europe"
            }
        ]
    
    def _get_industry_challenges(self):
        """Common healthcare imaging industry challenges"""
        return {
            "workflow_efficiency": [
                "Manual document handling creating staffing burdens",
                "Disconnected systems requiring multiple manual steps",
                "Time spent matching documents to studies",
                "Manual importing of outside studies from CDs/DVDs"
            ],
            "technical_integration": [
                "Legacy devices without modern connectivity",
                "Multi-vendor environments with compatibility challenges",
                "Unreliable network connections in distributed facilities",
                "Data migration during system upgrades"
            ],
            "cost_pressures": [
                "Budget constraints limiting equipment upgrades",
                "Rising storage costs for increasing imaging volumes",
                "Staffing costs for manual processes",
                "High costs of enterprise systems"
            ],
            "regulatory_compliance": [
                "Patient privacy requirements (HIPAA, etc.)",
                "Data security requirements",
                "Audit trail and documentation needs",
                "Image retention requirements"
            ]
        }
    
    def get_product_info(self, product_name):
        """Retrieve information about a specific product"""
        return self.products.get(product_name, None)
    
    def get_all_products(self):
        """Return information about all products"""
        return self.products
    
    def get_detailed_use_cases(self, product_name):
        """Retrieve detailed use cases for a specific product"""
        return self.detailed_use_cases.get(product_name, None)