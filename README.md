# Flux Sales Accelerator

## Overview

The Flux Sales Accelerator uses AI to generate comprehensive sales packages for healthcare imaging facilities. It pulls data from Apollo.io, scrapes websites, and leverages AI agents to create personalized sales content.

## Features

- Company search via Apollo.io
- Automated facility intelligence
- Website data extraction
- Comprehensive sales package generation
- Support for all Flux products (DICOM Printer 2, Capacitor, TuPACS, Gobbler)

## Prerequisites

* Python 3.12 or earlier (the app has compatibility issues with Python 3.13)
* Git

## Setup Instructions

1. **Clone the repository**
   ```
   git clone https://github.com/your-username/sales_accelerator.git
   cd sales_accelerator
   ```

2. **Create a virtual environment**
   ```
   python -m venv venv
   ```

3. **Activate the virtual environment**
   * On macOS/Linux: `source venv/bin/activate`
   * On Windows: `venv\Scripts\activate`

4. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

5. **Install specific package versions to resolve compatibility issues**
   ```
   pip install langchain==0.1.20 langchain-community==0.0.38 langchain-openai==0.0.5
   pip install tiktoken==0.5.2 tenacity==8.5.0
   ```

6. **Set up API keys**
   * You'll need to have API keys ready for:
     * OpenAI API (required)
     * Apollo.io API (optional, but recommended for company search)

7. **Run the application**
   ```
   streamlit run flux_sales_accelerator.py
   ```

## Using the application

* Enter your API keys in the sidebar
* Search for companies using the Apollo integration or manually enter facility details
* Generate personalized sales packages for Flux DICOM products

## Troubleshooting

If you encounter any dependency issues:

1. **Error with tiktoken or PyO3**:
   ```
   export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
   pip install tiktoken==0.5.2
   ```

2. **Issues with LangChain versions**:
   ```
   pip uninstall -y langchain langchain-openai langchain-community langchain-core
   pip install langchain==0.1.20 langchain-community==0.0.38 langchain-openai==0.0.5
   ```

3. **For a fresh start**:
   ```
   deactivate
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   ```
