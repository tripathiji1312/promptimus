import argparse
import json
import os
import time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

def generate_plan(model, tokenizer, instruction):
    prompt = f"""### Instruction:
{instruction}

### Response:"""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=256,
        eos_token_id=tokenizer.eos_token_id,
    )
    response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    try:
        plan = response_text.split("### Response:")[1].strip()
        return plan
    except IndexError:
        return "Error: Could not parse model response."

def load_model(base_model_id, adapter_path, use_adapter=True):
    device = "cpu"
    model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        torch_dtype=torch.float16,
    ).to(device) # Explicitly move the model to the CPU

    tokenizer = AutoTokenizer.from_pretrained(base_model_id)
    tokenizer.pad_token = tokenizer.eos_token

    if use_adapter:
        print(f"Loading LoRA adapter from {adapter_path}...")
        # Load the adapter onto the CPU-bound model.
        model = PeftModel.from_pretrained(model, adapter_path, device_map={"": device})
        print("LoRA adapter loaded successfully.")
    else:
        print("Loading BASE model without adapter.")

    return model, tokenizer
def main():
    parser = argparse.ArgumentParser(description="A CLI agent powered by a fine-tuned LLM.")
    parser.add_argument("instruction", type=str, help="The natural-language instruction for the agent.")
    args = parser.parse_args()

    base_model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    adapter_path = "./tinyllama-cmd-adapter-final"

    # Now we call load_model with use_adapter=True by default for the agent
    print("Loading fine-tuned model...")
    model, tokenizer = load_model(base_model_id, adapter_path, use_adapter=True)

    print(f"\nGenerating plan for instruction: '{args.instruction}'")
    plan = generate_plan(model, tokenizer, args.instruction) # This line needs the generate_plan function
    print("\n--- Generated Plan ---")
    print(plan)
    print("----------------------\n")

    action_taken = "no-action"
    found_command = False
    command_prefixes = ('git', 'tar', 'grep', 'find', 'ssh', 'chmod', 'python', 'pip', 'venv', 'bash', 'ls', 'cd', 'mkdir', 'echo', 'cat')

    for line in plan.split('\n'):
        clean_line = line.strip().strip('`').strip()
        if clean_line.startswith(command_prefixes):
            dry_run_command = f"echo \"Executing (dry-run): {clean_line}\""
            print(dry_run_command)
            action_taken = f"dry-run: {clean_line}"
            found_command = True
            break

    if not found_command:
        print("No executable shell command found in the generated plan. No action taken.")

    os.makedirs("logs", exist_ok=True)
    log_file_path = os.path.join("logs", "trace.jsonl")

    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "instruction": args.instruction,
        "generated_plan": plan,
        "action_taken": action_taken
    }

    with open(log_file_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    print(f"\nTrace logged to {log_file_path}")

# --- This part remains the same ---
if __name__ == "__main__":
    main()