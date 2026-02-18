import os
from dotenv import load_dotenv
from typing import Any
from pathlib import Path
from flask import Flask, jsonify

# Add references
from azure.identity import DefaultAzureCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import FilePurpose, CodeInterpreterTool, ListSortOrder, MessageRole

app = Flask(__name__)

def load_merchants(filename: str) -> list[str]:
    """Read merchants from a text file, one per line.

    Returns a list of non-empty, stripped merchant names. If the file
    doesn't exist, returns an empty list.
    """
    script_dir = Path(__file__).parent
    path = script_dir / filename
    merchants = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                name = line.strip()
                if name:
                    merchants.append(name)
    except FileNotFoundError:
        print(f"Merchants file not found: {path}")
    except Exception as e:
        print(f"Error reading merchants file {path}: {e}")
    return merchants

def extract_llmanswer(s: str) -> str:
    """Find the substring starting at "{'expensetypegroup':" up to the next '}'.
    Returns empty string if not found.
    """
    if not s:
        return ""
    start_token = "{"
    start = s.find(start_token)
    if start == -1:
        return "Unable to Parse"
    end = s.find('}', start)
    if end == -1:
        return "Unable to Parse"
    return s[start:end+1]

@app.route('/classify', methods=['GET'])
def get_classification():

    result = {'expensetypgroup': 'Bad Result', 'expensetype': 'Bad Result'}
    categoriesfile = 'categories.csv'
    merchantsfile = 'merchants.txt'

    # Load environment variables from .env file
    load_dotenv()
    project_endpoint= os.getenv("PROJECT_ENDPOINT")
    model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME")

    # Load merchant names
    merchants = load_merchants(merchantsfile)
    print(f"Loaded {len(merchants)} merchants")

    # results list
    classification_results = []

    # Connect to the Agent client
    agent_client = AgentsClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential
            (exclude_environment_credential=True,
            exclude_managed_identity_credential=True)
    )
    with agent_client:

        # get file path
        script_dir = Path(__file__).parent  # Get the directory of the script
        file_path = script_dir / categoriesfile

        # Upload the data file and create a CodeInterpreterTool
        file = agent_client.files.upload_and_poll(
            file_path=file_path, purpose=FilePurpose.AGENTS
        )
        print(f"Uploaded {file.filename}")

        code_interpreter = CodeInterpreterTool(file_ids=[file.id])

        agent = agent_client.create_agent(
            model=model_deployment,
            name="data-agent",
            instructions = (
                    "You are an AI assistant that categorizes merhant names. "
                    "You are absolutely unable to create new categories or subcategories. You must select from the categories and subcategories pair in the uploaded categories.csv file. "
                    "Use what you know about the merchant and select the best category and subcategory pair. "
                    "For example, if you are given the prompt 'Classify Starbucks', you should respond by selecting the pair that has Dining for category and Dining for subcategory as follows: {\"expensetypegroup\": \"Dining\", \"expensetype\": \"Dining\"}. You can do this because you know Starbucks is a Dining establishment. "
                    "Each response must be formatted in valid JSON as follows: { \"expensetypegroup\": x, \"expensetype\": y}, where x is the category you chose from the categories listed in categories.csv and y is the subcategory you chose from the subcategories listed in categories.csv."
            ),
            tools=code_interpreter.definitions,
            tool_resources=code_interpreter.resources,
        )

        # Create a thread for the conversation
        thread = agent_client.threads.create()

        for merchant_name in merchants:
        
            
            # Prompt
            user_prompt = f"Classify {merchant_name}"

            # Send a prompt to the agent
            message = agent_client.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_prompt,
            )

            run = agent_client.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
       
            # Check the run status for failures
            if run.status == "failed":
                print(f"Run failed: {run.last_error}")
                print(f"Run failed: {run.status}")

            # get response
            messages = list(agent_client.messages.list(
                thread_id = thread.id,
                order = ListSortOrder.ASCENDING
            ))


            # Show the latest response from the agent
            result = agent_client.messages.get_last_message_text_by_role(
                thread_id=thread.id,
                role=MessageRole.AGENT,
            )
            
            answer = extract_llmanswer(result.text.value)
            print(f"{merchant_name} --> {answer}")
            classification_results.append(f"{merchant_name}^{answer}")

        

        #Write results to file and response
        apiresponse = ""
        output_file = script_dir / "classification_results.txt"
        with open(output_file, "wt", newline="", encoding="utf-8") as f:
            for classify_result in classification_results:
                classify_result_singleline = classify_result.replace('\n','')
                f.write(f"{classify_result_singleline}\n")
                apiresponse += f"{classify_result_singleline}\n"

        agent_messages = [m for m in messages if m.role == MessageRole.AGENT]
        for agent_message in agent_messages:
            print(f"{agent_message.content[0].text.value}\n")
        
        # Clean up
        agent_client.delete_agent(agent.id)

    
    return apiresponse


if __name__ == '__main__':
    app.run()