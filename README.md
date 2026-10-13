# Merchant Classification API

A lightweight Flask API that classifies merchant names into predefined expense categories using **Azure AI Agents** and a **Code Interpreter Tool**. Merchant names are read from a local text file, passed to an Azure agent, and the resulting classifications are written to an output file and returned through the `/classify` endpoint.

---

## Features

- Reads merchant names from `merchants.txt`
- Uses `categories.csv` as the fixed category/subcategory source
- Sends each merchant to an Azure Agent for classification
- Enforces strict JSON output format from the model
- Writes results to `classification_results.txt`
- Exposes a simple GET endpoint: `/classify`

---

## Project Structure


