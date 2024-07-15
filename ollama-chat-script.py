import requests
import json
import subprocess
import os

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "codegeex.gguf:latest"  # Change this to the model you have loaded in Ollama

def send_message(message):
    data = {
        "model": MODEL_NAME,
        "prompt": message,
        "stream": False
    }
    response = requests.post(OLLAMA_URL, json=data)
    if response.status_code == 200:
        return response.json()["response"]
    else:
        return f"Error: {response.status_code} - {response.text}"

def test_code(code):
    # Create a temporary Python file
    with open("temp_code.py", "w") as f:
        f.write(code)
    
    # Run the code and capture output
    result = subprocess.run(["python", "temp_code.py"], capture_output=True, text=True)
    
    # Clean up the temporary file
    os.remove("temp_code.py")
    
    if result.returncode == 0:
        return True, result.stdout
    else:
        return False, result.stderr

def main():
    print("Welcome to the Ollama Chat Interface!")
    print("You can chat with the model, generate code, and test it.")
    print("Type 'exit' to quit the chat.")

    while True:
        user_input = input("You: ")
        
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        
        response = send_message(user_input)
        print(f"Model: {response}")
        
        if "```python" in response:
            code = response.split("```python")[1].split("```")[0].strip()
            print("\nCode detected. Would you like to test it? (yes/no)")
            test_choice = input().lower()
            
            if test_choice == 'yes':
                success, output = test_code(code)
                if success:
                    print("Code executed successfully. Output:")
                    print(output)
                else:
                    print("Code execution failed. Error:")
                    print(output)
                    print("\nWould you like the model to fix the code? (yes/no)")
                    fix_choice = input().lower()
                    
                    if fix_choice == 'yes':
                        fix_prompt = f"The following code produced an error:\n\n```python\n{code}\n```\n\nError:\n{output}\n\nPlease fix the code and provide the corrected version."
                        fixed_response = send_message(fix_prompt)
                        print(f"Model: {fixed_response}")
                        
                        if "```python" in fixed_response:
                            fixed_code = fixed_response.split("```python")[1].split("```")[0].strip()
                            print("\nTesting the fixed code:")
                            success, output = test_code(fixed_code)
                            if success:
                                print("Fixed code executed successfully. Output:")
                                print(output)
                            else:
                                print("Fixed code execution failed. Error:")
                                print(output)

if __name__ == "__main__":
    main()
