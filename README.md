# Keyword Research and Analysis Tool

A Python-based tool for keyword research, analysis, and expansion using web scraping, Google Trends, and AI-powered keyword extraction.

## Features

- **Web Scraping**: Extract text content from websites for analysis
- **Keyword Extraction**: Uses AI (Gemini Flash) to extract relevant seed keywords from text
- **Keyword Expansion**: Expands seed keywords into related terms using AI
- **Google Trends Integration**: Fetches trend data for keywords
- **Batch Processing**: Handles keyword processing in batches for efficiency
- **Configuration**: YAML-based configuration for easy setup

## Prerequisites

- Python 3.7+
- Google API Key (for Gemini Flash)
- Internet connection (for web scraping and API calls)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Cube_task
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## Configuration

Edit the `config.yaml` file to customize the tool's behavior. The configuration includes settings for:

- API endpoints
- Request timeouts
- Batch sizes
- Data storage locations
- And more...

## Usage

1. Update the `config.yaml` file with your desired settings
2. Run the main script:
   ```bash
   python main.py
   ```

The tool will:
1. Scrape the configured website for content
2. Extract seed keywords using AI
3. Expand keywords into related terms
4. Fetch Google Trends data for the keywords
5. Generate a report with the results

## Project Structure

- `main.py`: Main script containing the core functionality
- `config.yaml`: Configuration file for the application
- `requirements.txt`: Python dependencies
- `config.normalized.json`: Normalized configuration (auto-generated)

## Dependencies

- beautifulsoup4: Web scraping
- requests: HTTP requests
- pyyaml: YAML configuration parsing
- pandas: Data manipulation
- keybert: Keyword extraction
- sentence-transformers: Text embeddings
- google-generativeai: Google's Gemini AI API
- python-dotenv: Environment variable management

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For support, please open an issue in the repository.
