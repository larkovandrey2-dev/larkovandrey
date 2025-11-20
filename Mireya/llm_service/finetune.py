# train_qwen_cpu.py
import os
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model
import torch

# --------------------------
MODEL_NAME = "Qwen/Qwen2.5-1.5B"             # заменить на точное имя
DATA_PATH = "dataset.jsonl"
OUT_DIR = "./finetuned-qwen-cpu"
EPOCHS = 2
BATCH = 1
GRAD_ACC = 8
LR = 2e-4
MAX_TOKENS = 512
# --------------------------

def main():

    device = "cpu"
    print("Device:", device)

    print("[1] Загружаю токенизатор...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=False)

    print("[2] Загружаю модель (float16 или float32)...")

    # На CPU fp16 запрещён → используем float32
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float32,
        device_map={"": "cpu"}       # заставляем модель работать на CPU
    )

    print("[3] Подключаю LoRA адаптер...")

    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.1,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, peft_config)

    print("[4] Загружаю датасет...")
    dataset = load_dataset("json", data_files=DATA_PATH, split="train")

    def tokenize_fn(ex):
        text = ex["prompt"] + ex["completion"]
        return tokenizer(text, truncation=True, max_length=MAX_TOKENS)

    tokenized = dataset.map(tokenize_fn, remove_columns=dataset.column_names)
    tokenized.set_format(type="torch")

    print("[5] Настраиваю обучение на CPU...")
    args = TrainingArguments(
        output_dir=OUT_DIR,
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH,
        gradient_accumulation_steps=GRAD_ACC,
        learning_rate=LR,
        logging_steps=10,
        save_steps=200,
        save_total_limit=3,
        fp16=False,     # CPU запрет
        bf16=False,     # CPU запрет
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=tokenized
    )

    print("[6] Запускаю обучение...")
    trainer.train()

    print("[+] Сохраняю LoRA адаптер…")
    model.save_pretrained(OUT_DIR)
    tokenizer.save_pretrained(OUT_DIR)

    print("Готово.")

if __name__ == "__main__":
    main()
