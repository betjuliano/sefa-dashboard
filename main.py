"""
Main entry point for Vercel deployment
"""
import os
import sys
import subprocess
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def handler(request):
    """Handler function for Vercel"""
    # Set environment variables for Streamlit
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    # Import and run the Streamlit app
    try:
        import streamlit.web.cli as stcli
        import streamlit as st
        
        # Configure Streamlit
        st.set_page_config(
            page_title="Dashboard de Qualidade - MVP",
            page_icon="📊",
            layout="wide",
        )
        
        # Import the main app
        import app
        
        return {"statusCode": 200, "body": "Streamlit app running"}
        
    except Exception as e:
        return {"statusCode": 500, "body": f"Error: {str(e)}"}

# For local development
if __name__ == "__main__":
    import app