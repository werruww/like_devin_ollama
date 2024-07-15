import requests
import json
import subprocess
import os
import tempfile

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "codegeex.gguf:latest"  # Change this to the model you have loaded in Ollama
CMD_PATH = r"C:\Windows\System32\cmd.exe"

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

def test_code(code, use_cmd=False):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name
    try:
        if use_cmd:
            cmd_command = f'"{CMD_PATH}" /c python "{temp_file_path}"'
            result = subprocess.run(cmd_command, capture_output=True, text=True, shell=True)
        else:
            result = subprocess.run(["python", temp_file_path], capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    finally:
        os.unlink(temp_file_path)

def get_multiline_input():
    print("Enter your multi-line input. Press Ctrl+D (Unix) or Ctrl+Z (Windows) followed by Enter to finish:")
    lines = []
    while True:
        try:
            line = input()
            lines.append(line)
        except EOFError:
            break
    return "\n".join(lines)

def main():
    print("Welcome to the Ollama Chat Interface!")
    print("You can chat with the model, generate code, and test it.")
    print("Type 'exit' to quit the chat.")
    print("To enter multi-line input, type 'multiline' and press Enter.")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        
        if user_input.lower() == 'multiline':
            user_input = get_multiline_input()
        
        response = send_message(user_input)
        print(f"Model: {response}")
        
        if "```python" in response:
            code = response.split("```python")[1].split("```")[0].strip()
            print("\nCode detected. How would you like to test it?")
            print("1. Run with Python")
            print("2. Run with CMD")
            print("3. Don't test")
            test_choice = input("Enter your choice (1/2/3): ")
            
            if test_choice in ['1', '2']:
                use_cmd = (test_choice == '2')
                success, output = test_code(code, use_cmd)
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
                            success, output = test_code(fixed_code, use_cmd)
                            if success:
                                print("Fixed code executed successfully. Output:")
                                print(output)
                            else:
                                print("Fixed code execution failed. Error:")
                                print(output)

if __name__ == "__main__":
    main()
