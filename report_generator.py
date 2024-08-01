"""
This script communicates with the OpenAI GPT API to generate detailed reports based on user-provided logs.
It allows the user to define the GPT model they want to consult, in this case, "gpt-4-turbo".
The script generates a report in LaTeX code, analyzing security logs and identifying potential attacker activities.
Due to the token limit imposed by OpenAI's API, the report is generated in parts. The script iterates through
each identified step in the logs, expanding on each with additional details, vulnerabilities explored, and
mitigation suggestions. The performance of the API interactions is also tracked, including the time taken
for each step, the number of tokens used, and the estimated cost of the API calls.

Key functionalities include:
- Loading environment variables for API key configuration.
- Sending requests to the GPT API and handling responses.
- Extracting the number of steps from the initial analysis.
- Generating and saving detailed LaTeX reports for each step.
- Tracking and reporting the performance metrics, including time, tokens, and cost.

Requirements:
- A file containing the logs must be present in the directory.
- A .env file containing the API key must also be present for the script to access the OpenAI API.

The final output consists of a complete LaTeX report and an API performance report that details the usage
metrics and costs for each part of the report generation process.
"""

import openai
import re
from dotenv import load_dotenv
import os
import time as time_module  # Renamed to avoid conflict with any local variable

# Load environment variables from the .env file
load_dotenv()

# Set your API key here
openai.api_key = os.getenv('OPENAI_API_KEY')

# Price per 1,000,000 tokens in dollars
input_per_million_price = 10.00  # $10.00 per 1M input tokens
output_per_million_price = 30.00 # $30.00 per 1M output tokens

# Function to send a request to the GPT API
def send_to_gpt(messages, max_tokens=1500):
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=messages,
        max_tokens=max_tokens
    )
    content = response['choices'][0]['message']['content']
    usage = response['usage']
    return content, usage

# Function to extract the number of steps from the response
def extract_number_of_steps(response):
    match = re.search(r'\[n(?:\\?_)?steps:(\d+)\]', response)  # Updated to n_steps
    if match:
        return int(match.group(1))
    else:
        raise ValueError("Number of steps not found in the response.")

# Function to save content to a file
def save_to_file(file_name, content):
    with open(file_name, 'w', encoding='utf-8') as file:
        file.write(content)

# Main function to execute the process
def generate_detailed_report(prompt, logs):
    # Start the total timer
    start_total_time = time_module.time()  # Using time_module to avoid conflict

    # Initial prompt to identify the steps
    initial_prompt = [
        {"role": "user", "content": prompt},
        {"role": "user", "content": logs}
    ]
    
    # Send the first request to get the initial report and the number of steps
    initial_response, initial_usage = send_to_gpt(initial_prompt)
    print("Initial response:", initial_response)
    
    # Create the folder to store the files
    report_folder = 'report_generated_by_GPT'
    os.makedirs(report_folder, exist_ok=True)
    
    # Save the initial response
    save_to_file(os.path.join(report_folder, 'initial_report.txt'), initial_response)
    
    # Extract the number of steps from the initial response
    number_of_steps = extract_number_of_steps(initial_response)
    print(f"Number of identified steps: {number_of_steps}")
    
    # Lists to store the time for each step, tokens used, and cost
    step_times = []
    tokens_used = []
    step_costs = []
    total_cost = 0.0
    
    # For each step, send an expansion request and save the response
    for i in range(1, number_of_steps + 1):
        start_step_time = time_module.time()  # Start the timer for step i
        
        expansion_prompt = [
            {"role": "assistant", "content": initial_response},
            {"role": "user", "content": f"Please expand the description of Step {i}. Include details about the actions taken, vulnerabilities exploited, and mitigation suggestions."}
        ]
        expansion_response, expansion_usage = send_to_gpt(expansion_prompt)
        print(f"\nExpansion of Step {i}:\n{expansion_response}\n")
        save_to_file(os.path.join(report_folder, f'expansion_step_{i}.txt'), expansion_response)
        
        end_step_time = time_module.time()  # End the timer for step i
        step_duration = end_step_time - start_step_time
        step_times.append(step_duration)  # Store the time for the step
        
        # Calculate the cost for this step
        prompt_tokens = expansion_usage['prompt_tokens']
        completion_tokens = expansion_usage['completion_tokens']
        total_tokens = expansion_usage['total_tokens']
        tokens_used.append(total_tokens)

        input_cost = (prompt_tokens / 1000000) * input_per_million_price
        output_cost = (completion_tokens / 1000000) * output_per_million_price
        step_cost = input_cost + output_cost
        step_costs.append(step_cost)
        total_cost += step_cost
        
        print(f"Time for Step {i}: {step_duration:.2f} seconds")
        print(f"Tokens used in Step {i}: {total_tokens}")
        print(f"Cost of Step {i}: ${step_cost:.5f}")
    
    # End the total timer
    end_total_time = time_module.time()
    total_duration = end_total_time - start_total_time
    print(f"Total time for generating the report: {total_duration:.2f} seconds")
    print(f"Estimated total cost: ${total_cost:.5f}")
    
    # Display individual times and tokens used
    for i, (time, tokens, cost) in enumerate(zip(step_times, tokens_used, step_costs), start=1):
        print(f"Time for Step {i}: {time:.2f} seconds")
        print(f"Tokens used in Step {i}: {tokens}")
        print(f"Estimated cost of Step {i}: ${cost:.5f}")
    
    # Save performance report
    performance_report = os.path.join(report_folder, 'api_performance_report.txt')
    with open(performance_report, 'w', encoding='utf-8') as report_file:
        report_file.write(f"Total time for generating the report: {total_duration:.2f} seconds\n")
        report_file.write(f"Estimated total cost: ${total_cost:.5f}\n\n")
        for i, (time, tokens, cost) in enumerate(zip(step_times, tokens_used, step_costs), start=1):
            report_file.write(f"Step {i}:\n")
            report_file.write(f"  Time: {time:.2f} seconds\n")
            report_file.write(f"  Tokens used: {tokens}\n")
            report_file.write(f"  Estimated cost: ${cost:.5f}\n\n")

# Read the logs from the 'logs_experiment1' file
def read_logs_from_file(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        raise RuntimeError(f"Error reading the file {file_name}: {e}")

# Path to the log file
log_file_name = 'logs_experiment2'

# Read the logs from the file
logs = read_logs_from_file(log_file_name)

# Define the prompt with detailed instructions
prompt = (
    "You will receive a series of information security logs originating from various sources such as firewalls, database monitoring systems, web server logs, and intrusion detection tools. "
    "Your task is to analyze these logs in chronological order to identify and describe the activities of a possible attacker through a LaTeX report. Please focus on:\n\n"
    "- Describing the attack actions, like in the example:\n\"[timestamp] The attacker accessed the system, opened a file, uploaded a webshell, authenticated with a service, ...\"\n"
    "- Determining the chronological sequence of events recorded in the logs.\n"
    "- Identifying anomalous patterns or suspicious activities in each set of logs.\n"
    "- Explaining the relevance of each suspicious activity in the context of the overall attack scenario.\n"
    "- Suggesting which techniques and tactics the attacker might be using based on the observed patterns.\n"
    "- Evaluating potential vulnerabilities or security flaws that the attacker exploited.\n"
    "- Proposing response or mitigation measures for the identified incidents.\n\n"
    "- Escape underlines in the LaTeX code.\n"
    "- Do not say anything other than the LaTeX report code.\n"
    "- No need to generate a preamble, just start from \\begin{document}.\n"
    "- Indicate the number of attack steps in the following format: [n_steps:X], where X is the number of steps. For example, if the attack involved port scanning, SQL injection, and privilege escalation, then X = 3, resulting in [n_steps:3]. After stating the number of steps, write an array with the names of the steps to justify your response. For example, [n_steps:3] [port_scan, sql_injection, privilege_escalation]"
)

# Generate the detailed report
generate_detailed_report(prompt, logs)
