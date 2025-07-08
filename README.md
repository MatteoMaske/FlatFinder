# 🏡 FlatFinder -ConversationalAgent

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://www.python.org/)
[![Transformers](https://img.shields.io/badge/Transformers-4.45%2B-red?logo=transformers)](https://pytorch.org/)

A modular Conversational Agent pipeline based on open source Large Language Models (LLMs), developed for the Human Machine Dialogue 2024/25 course.  
This agent can help users find rental properties in India, leveraging a real dataset and advanced NLU, DM, and NLG components.

---

## ✨ Features

- 🔍 **Natural Language Understanding (NLU):** Extracts intents and slots from user queries.
- 🧠 **Dialogue Management (DM):** Maintains conversation state and decides next actions.
- 🗣️ **Natural Language Generation (NLG):** Generates natural, context-aware responses.
- 🏘️ **Real Estate Domain:** Uses a real dataset of Indian rental properties.
- 🦙 **LLM Support:** Works with HuggingFace models and Ollama (Llama3).
- 🧪 **Evaluation Mode:** Automated NLU and DM evaluation with test sets.
- 🛠️ **Extensible:** Modular design for easy adaptation to other domains.

---

## 📂 Project Structure

```
.
├── pipeline.py                # Main entry point
├── evaluator.py               # Evaluation logic
├── components/                # NLU, DM, NLG, State Tracker modules
├── data/                      # Database interface
├── test/                      # NLU/DM test sets and confusion matrix
├── prompts/                   # Prompt templates for LLMs
└── utils/                     # Utility functions and templates
```

---

## 🚀 Quickstart

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ConversationalAgent.git
cd ConversationalAgent
```

### 2. Install Dependencies

> **Recommended:** Use a virtual environment (e.g., `venv` or `conda`).

```bash
pip install -r requirements.txt
```

### 3. Download the Dataset

The default dataset can be found at [Kaggle](https://www.kaggle.com/datasets/iamsouravbanerjee/house-rent-prediction-dataset)

If you want to use a different dataset, place your CSV in the same folder and update the `--database-path` argument.

### 4. Run the Conversational Agent

```bash
python pipeline.py llama3
```

or

```bash
python pipeline.py ollama
```


### 5. Evaluation Mode

To run automated tests on NLU/DM:

```bash
python pipeline.py llama3 --eval
```

---

## 🛠️ Usage

- **Start a conversation:**  
  The agent will prompt you for input. Type your queries (e.g., "Show me 2 BHK flats in Mumbai under 20,000 rupees").
- **Reset conversation:**  
  Type `reset` to clear the conversation and state.

---

> 🏠 Happy House Hunting with FlatFinder!
