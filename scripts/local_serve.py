"""
Lightweight local model server using transformers + Flask.
Serves an OpenAI-compatible /v1/chat/completions endpoint.
For local testing only — use vLLM on the server.
"""

import json
import time
import torch
from http.server import HTTPServer, BaseHTTPRequestHandler
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
PORT = 8000
MAX_NEW_TOKENS = 1024

print(f"Loading {MODEL_ID}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True,
)
print(f"Model loaded on {model.device}")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/health" or self.path == "/v1/models":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "model": MODEL_ID}).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        messages = body.get("messages", [])
        max_tokens = body.get("max_tokens", MAX_NEW_TOKENS)
        temperature = body.get("temperature", 0.0)

        # Apply chat template
        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
        )
        inputs = tokenizer(text, return_tensors="pt").to(model.device)
        input_len = inputs["input_ids"].shape[1]

        # Generate
        with torch.no_grad():
            gen_kwargs = {
                "max_new_tokens": min(max_tokens, MAX_NEW_TOKENS),
                "do_sample": temperature > 0,
            }
            if temperature > 0:
                gen_kwargs["temperature"] = temperature
            outputs = model.generate(**inputs, **gen_kwargs)

        output_ids = outputs[0][input_len:]
        output_text = tokenizer.decode(output_ids, skip_special_tokens=True)
        output_len = len(output_ids)

        # OpenAI-compatible response
        response = {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "model": MODEL_ID,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": output_text},
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": input_len,
                "completion_tokens": output_len,
                "total_tokens": input_len + output_len,
            },
        }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Serving on http://localhost:{PORT}/v1/chat/completions")
    server.serve_forever()
