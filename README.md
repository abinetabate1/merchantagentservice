# Merchant Expense Classifier

This Flask application classifies merchant names into expense categories using an Azure AI Agent. It reads merchant names from `merchants.txt` and category/subcategory options from `categories.csv`.

## How It Works

When you call `GET /classify`, the application:

1. Loads the Azure project endpoint and model deployment name from environment variables.
2. Reads merchant names from `merchants.txt`.
3. Uploads `categories.csv` for the agent's code interpreter to use.
4. Asks the agent to classify each merchant using the available categories.
5. Writes the results to `classification_results.txt` and returns them in the response.

Each result is written as a merchant name followed by its classification, separated by `^`.

## Required Files

Place these files beside the Python application:

- `categories.csv` — the allowed expense categories and subcategories.
- `merchants.txt` — merchant names, one per line.

## Configuration

Set these environment variables in a `.env` file or the process environment:

- `PROJECT_ENDPOINT` — the Azure AI project endpoint.
- `MODEL_DEPLOYMENT_NAME` — the model deployment used by the agent.

The application uses `DefaultAzureCredential` for authentication.

## Running the Application

Install the required Flask, dotenv, and Azure AI packages, then run the Python application. By default, Flask starts the server using its development server.

Call `GET /classify` to classify all merchants in `merchants.txt`.
