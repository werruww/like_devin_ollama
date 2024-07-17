import subprocess
import requests
import json
import sys
import re

class CodeAgent:
    def __init__(self, model="Einstein-v7-Qwen2-7B-Q6_K.gguf:latest", ollama_url="http://localhost:11434"):
        self.model = model
        self.ollama_url = ollama_url

    def generate_code(self, prompt):
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt},
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
        except requests.RequestException as e:
            print(f"فشل الطلب: {e}")
            return ""

    def clean_code(self, code):
        # إزالة علامات الماركداون للكود
        code = re.sub(r'```python\s*', '', code)
        code = re.sub(r'```\s*$', '', code)
        # إزالة الأسطر الفارغة في البداية والنهاية
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
        prompt = f"""أصلح الكود التالي بلغة Python:

{code}

الخطأ:
{error}

قم بإصلاح الكود وإرجاع الكود المصحح فقط، دون أي تفسيرات أو تعليقات إضافية. لا تضف علامات الماركداون مثل ``` python."""
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

def interactive_session():
    print("تهيئة وكيل الكود...")
    agent = CodeAgent()

    print("\nاختبار الاتصال بـ Ollama...")
    if not test_ollama_connection():
        print("فشل الاتصال بـ Ollama. يرجى التحقق من تشغيل الخادم على http://localhost:11434")
        return

    print("تم الاتصال بـ Ollama بنجاح.")

    while True:
        user_input = input("\nاطلب كودًا بلغة Python (أو اكتب 'خروج' للإنهاء): ")
        if user_input.lower() == 'خروج':
            break

        print("\nجارٍ إنشاء واختبار الكود...")
        final_code, result = agent.run_until_success(user_input)
        
        if final_code:
            print("\nالكود النهائي:")
            print(final_code)
            print("\nنتيجة التنفيذ:")
            print(result)
        else:
            print("\nفشل في إنشاء كود يعمل. يرجى المحاولة مرة أخرى بطلب مختلف.")

    print("شكرًا لاستخدامك وكيل الكود. مع السلامة!")

if __name__ == "__main__":
    interactive_session()
