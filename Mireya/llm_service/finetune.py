from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model
import torch

MODEL_NAME = "meta-llama/Llama-3.2-1b"  # маленькая, идёт даже на слабом ПК

# Загружаем токенизатор
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

# Загружаем модель в 4bit (экономия RAM)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    load_in_4bit=True,
    device_map="auto"
)

# LoRA адаптер
peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, peft_config)

# Загружаем датасет
dataset = load_dataset("json", data_files="dataset.jsonl", split="train")

# Токенизация
def encode(ex):
    return tokenizer(
        ex["prompt"] + ex["completion"],
        truncation=True,
        max_length=512,
    )

tokenized = dataset.map(encode)

# Параметры обучения
args = TrainingArguments(
    output_dir="./finetuned-model",
    num_train_epochs=3,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=16,
    learning_rate=2e-4,
    logging_steps=10,
    save_steps=200,
)

# Trainer
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=tokenized
)

# Запуск обучения
trainer.train()

# Сохранение итоговой модели
trainer.save_model("./finetuned-model")
tokenizer.save_pretrained("./finetuned-model")
