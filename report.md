# AI/ML Internship Technical Task Report

**Candidate:** Swarnim Tripathi

---

### 1. Project Objective

The goal of this project was to build a miniature, end-to-end command-line assistant. This involved collecting a specialized dataset, fine-tuning a small language model (≤ 2B parameters), and wrapping the result in a runnable Python agent capable of generating and executing shell commands.

---

### 2. Data Preparation

*   **Data Source:** A dataset of over 150 question-and-answer pairs was collected primarily from the Stack Exchange API, targeting sites like Stack Overflow and Unix & Linux Stack Exchange.
*   **Topics Covered:** The data focused on common command-line tools including Git, Bash, Grep, Find, Tar, SSH, and Docker.
*   **Curation:** An initial automated script was used to fetch raw data, followed by a non-destructive cleaning script to format the entries. The final curation was performed manually to ensure high quality and relevance, resulting in a final dataset of 324 pairs.

---

### 3. Model Fine-Tuning

*   **Base Model:** `TinyLlama/TinyLlama-1.1B-Chat-v1.0`
*   **Fine-Tuning Method:** QLoRA (4-bit quantization) was used to efficiently fine-tune the model.
*   **Training Environment:** The model was trained for **one epoch** on a free Google Colab T4 GPU instance.
*   **Key Hyperparameters:**
    *   Learning Rate: `2e-4`
    *   Batch Size: `4`
    *   Optimizer: `paged_adamw_32bit`
    *   LoRA Rank (`r`): `8`
*   **Training Time:** The fine-tuning process was completed in approximately **2 minutes**.

---

### 4. Evaluation Results Summary

A full analysis can be found in `eval_static.md` and `eval_dynamic.md`.

*   **Static Evaluation:** The fine-tuned model consistently produced more concise and command-oriented responses compared to the conversational base model. The fine-tuned model's ROUGE-L scores against reference answers were reasonable, though it notably confused `head` and `tail` in one test case, indicating areas for data quality improvement.

*   **Dynamic Evaluation:** The `agent.py` script successfully loaded the model and executed dry-runs for correctly formatted commands. A key limitation identified was the parser's inability to handle commands prefixed with shell prompts (e.g., `$`), preventing execution in 3 out of 7 test cases. This highlights a critical area for future enhancement.

---

### 5. Future Improvement Ideas

1.  **Robust Command Parsing:** The agent's command detection logic should be improved from a simple `startswith()` check to a regular expression-based parser. This would allow it to reliably extract commands by stripping common prefixes like `$`, `(venv) $`, `>` and ignoring surrounding markdown code blocks.

2.  **Data Quality and Complexity:** The model's confusion between `head` and `tail` suggests the training data could be improved. A future iteration would involve a more rigorous manual validation of answers in the dataset. Additionally, incorporating more complex, multi-step command sequences (e.g., pipes with `xargs`) into the training data would enhance the model's planning capabilities.