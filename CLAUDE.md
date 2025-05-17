# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Date Night Planner AI application built with Streamlit. It uses the Google Gemini API to generate personalized date night suggestions based on user preferences.

## Key Architecture

1. **Main Application**: `dateNight.py` - A single-file Streamlit web application
2. **Dependencies**: Located in `requirements.txt`
   - streamlit (UI framework)
   - google-generativeai (Gemini API integration)
   - python-dotenv (environment variable management)

## Core Functionality

The application:
- Collects user preferences through interactive UI elements (theme, activity type, budget, preparation time, duration)
- Generates date plans using Google Gemini API with structured JSON output
- Displays the generated plan with custom styling in a responsive layout

## Development Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# Create a .env file with:
# GOOGLE_API_KEY=your_gemini_api_key
```

### Running the Application
```bash
streamlit run dateNight.py
```

### Testing
No test framework is currently set up. To verify functionality:
1. Run the application locally
2. Test various input combinations
3. Verify JSON parsing and error handling work correctly

## Important Considerations

1. **API Key Management**: Uses environment variables via `.env` file (not committed)
2. **Error Handling**: Includes robust error handling for API failures and JSON parsing
3. **UI Styling**: Extensive custom CSS for Streamlit components
4. **Model Configuration**: Supports multiple Gemini models with fallback options