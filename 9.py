import subprocess
import requests
import json
import sys
import re
import os

class CodeAgent:
    def __init__(self, model="Einstein-v7-Qwen2-7B-Q6_K.gguf:latest", ollama_url="http://localhost:11434"):
        self.model = model
        self.ollama_url = ollama_url
        self.prompts = self.load_prompts()

    def load_prompts(self):
        prompt_file = 'prompts.txt'
        default_prompts = {
            "GENERATE_CODE": "قم بإنشاء كود Python للمهمة التالية:",
            "IMPROVE_CODE": "أصلح الكود التالي بلغة Python:\n{code}\n\nالخطأ:\n{error}\n\nقم بإصلاح الكود وإرجاع الكود المصحح فقط، دون أي تفسيرات أو تعليقات إضافية."
        }

        if not os.path.exists(prompt_file):
            with open(prompt_file, 'w', encoding='utf-8') as f:
                for key, value in default_prompts.items():
                    f.write(f"{key}: {value}\n")
            return default_prompts

        prompts = {}
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for line in content.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    prompts[key.strip()] = value.strip()

            # Ensure all required prompts are present
            for key in default_prompts:
                if key not in prompts:
                    prompts[key] = default_prompts[key]
                    print(f"Warning: '{key}' prompt not found in file. Using default.")

        except Exception as e:
            print(f"Error loading prompts: {e}")
            print("Using default prompts.")
            return default_prompts

        return prompts

    def generate_code(self, prompt):
        try:
            if 'GENERATE_CODE' not in self.prompts:
                raise KeyError("'GENERATE_CODE' prompt not found")

            full_prompt = self.prompts['GENERATE_CODE'] + "\n" + prompt
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": full_prompt},
                stream=True,
                timeout=30
            )
            response.raise_for_status()
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        json_response = json.loads(line)
                        full_response += json_response.get('response', '')
                        if json_response.get('done', False):
                            break
                    except json.JSONDecodeError as e:
                        print(f"خطأ في تحليل JSON: {e}")
                        print("محتوى السطر:", line)
            
            return self.clean_code(full_response.strip())
        except KeyError as e:
            print(f"Error: {e}")
            return ""
        except requests.RequestException as e:
            print(f"فشل الطلب: {e}")
            return ""

    def clean_code(self, code):
        code = re.sub(r'```python\s*', '', code)
        code = re.sub(r'```\s*$', '', code)
        return code.strip()

    def execute_code(self, code):
        try:
            result = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "انتهت مهلة التنفيذ"

    def improve_code(self, code, error):
        prompt = self.prompts['IMPROVE_CODE'].format(code=code, error=error)
        return self.generate_code(prompt)

    def run_until_success(self, initial_prompt, max_attempts=5):
        if "fix this code" in initial_prompt.lower():
            code = initial_prompt.split("fix this code", 1)[1].strip()
        else:
            code = self.generate_code(initial_prompt)
        
        for attempt in range(max_attempts):
            print(f"المحاولة {attempt + 1}:")
            print("الكود المُولَّد:")
            print(code)
            success, output, error = self.execute_code(code)
            if success:
                return code, output
            print(f"فشل التنفيذ. الخطأ:\n{error}")
            code = self.improve_code(code, error)
        return None, "فشل في إنشاء كود يعمل بعد عدة محاولات"

def test_ollama_connection():
    try:
        response = requests.get("http://localhost:11434/api/tags")
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"فشل الاتصال بـ Ollama: {e}")
        return False

def read_prompt_from_file(filename='prompt.txt'):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def main():
    print("تهيئة وكيل الكود...")
    agent = CodeAgent()

    print("\nاختبار الاتصال بـ Ollama...")
    if not test_ollama_connection():
        print("فشل الاتصال بـ Ollama. يرجى التحقق من تشغيل الخادم على http://localhost:11434")
        return

    print("تم الاتصال بـ Ollama بنجاح.")

    prompt = read_prompt_from_file()
    if prompt is None:
        return

    print("\nالمطالبة المقروءة من الملف:")
    print(prompt)

    print("\nجارٍ إنشاء واختبار الكود...")
    final_code, result = agent.run_until_success(prompt)
    
    if final_code:
        print("\nالكود النهائي:")
        print(final_code)
        print("\nنتيجة التنفيذ:")
        print(result)
    else:
        print("\nفشل في إنشاء كود يعمل. يرجى التحقق من المطالبة في الملف وحاول مرة أخرى.")

    print("تم الانتهاء من تنفيذ المهمة.")

if __name__ == "__main__":
    main()
