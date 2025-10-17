Absolutely 👍 — here’s the **ready-to-copy Markdown version** with all grammatical fixes and professional formatting preserved exactly as in your style:

---

# 🤖 Objective

The objective of this project is to evaluate the feasibility of leveraging **Agentic AI** as a development partner in full-stack web development by automating the traditional development workflow.

---

# 🤖 Agentic Full-Stack Web Development Automation

This is a **self-initiated experimental project** aimed at automating the full-stack web development lifecycle using **Agentic AI** and the **LangGraph framework**.
The project demonstrates how autonomous AI agents can collaboratively manage each stage of web development — from wireframing and mockups to API design, coding, and documentation.

---

## 🔍 Key Highlights

* **Automates the full-stack web development lifecycle** using Agentic AI.
* **Replaces traditional sequential development steps** (wireframing, mockups, API design, coding) with **dedicated AI agents** for each phase.
* **Enables seamless end-to-end project creation** and **automatic documentation updates**.
* **Utilizes Azure MCP Servers** for simplified provisioning of Azure resources.

---

## ⚡ Benefits

* **Rapid generation** of modular full-stack codebases (frontend, backend, and tests) using AI models.
* The generated code can be extended into an **end-to-end production-ready application** by integrating appropriate databases and enhancing the frontend.
* **AI-powered documentation** provides detailed, line-by-line code explanations for the generated web project.
* **Customizable prompts and agent nodes** for flexible and adaptive development workflows.
* **User-friendly interface** for creating, updating, and downloading projects.

---

## ⚙️ Setup Instructions

Follow these steps to set up and run the project locally:

### 1. Clone the repository

```bash
git clone https://github.com/rajaditya-k/Agentic_AI_Web_Development.git
cd Agentic_AI_Web_Development
```

### 2. Create a `.env` file

Create a file named `.env` in the root directory and add the required environment variables (such as API keys and credentials).

Example:

```
OPENAI_API_KEY=your_api_key_here
LANGGRAPH_API_KEY=your_langgraph_key
```

For this project, the required variables are:

1. OPENAI_API_KEY
2. COSMOS_ENDPOINT
3. COSMOS_KEY
4. EVENTHUB_CONN_STR
5. EVENTHUB_NAME
6. EVENT_HUB_BLOB_STORAGE_CONN_STR
7. EVENT_HUB_BLOB_CONTAINER_NAME
8. BLOB_CONN_STR
9. COSMOS_DATABASE
10. COSMOS_CONTAINER
11. BLOB_CONTAINER

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Streamlit application

```bash
streamlit run app.py
```

---

## 🧠 Tech Stack

* **Programming Language** – Python
* **Streamlit** – for building the interactive interface
* **LangGraph Framework** – to manage multi-agent workflows
* **Prompt Management** – POML (Prompt Orchestration Markup Language)
* **OpenAI / LLM APIs** – for natural language reasoning and generation
* **Cloud Services** –

  * Azure Cosmos DB: stores user details
  * Azure Blob Storage: stores generated web project content
  * Azure Event Hubs: streams logs
* **Azure MCP Server** – provisions Azure Cloud resources without manual setup
* **IDE** – Cursor IDE

---

## 📁 Project Structure

```
Agentic_AI_Web_Development/
│
├── app.py                 # Streamlit application entry point
├── web_app_creator_pomls/ # Contains all prompts in POML format
├── include/               # Helper functions
├── graphs/                # Contains the multi-agent workflow definitions
├── db/                    # Functions to interact with Azure Cloud Services
├── core/                  # Loads .env variables and defines LangGraph state models
├── auth/                  # Manages user authentication for the Streamlit app
├── requirements.txt       # Dependencies
├── .env.example           # Example environment configuration
└── README.md              # Project documentation
```

---

## 🧩 How It Works

1. **User Input:** The user defines project requirements through the Streamlit UI.
2. **Agent Workflow:** LangGraph coordinates specialized AI agents for wireframing, API design, frontend/backend code generation, and documentation.
3. **Output Delivery:** The system generates project artifacts and dynamically updates documentation.
   Generated projects can also be viewed in a separate tab.

---

## 📌 Notes

* This is a **self-experimented prototype**, showcasing the potential of AI-driven development workflows.
* The goal is to explore how **multiple AI agents can collaborate** to automate different stages of the software lifecycle.
* To learn more about **Azure MCP Server**, refer to the [official documentation](https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/get-started/tools/cursor).
* Contributions, suggestions, and discussions are welcome!

---

## 🔮 Next Steps

* **Experiment with prompt variations** in POML to improve agent performance and output quality.
* **Explore deployment strategies** to make the app accessible via the cloud.
* **Integrate new AI models** to expand the capabilities of each development agent.

---

## 🧑‍💻 Author

**Raj Aditya Kumar**
Senior Data Engineer | Passionate about Data Engineering and Autonomous AI Systems

📧 [adrj0596@gmail.com](mailto:adrj0596@gmail.com)
🌐 [LinkedIn Profile](https://linkedin.com/in/rajadityakumar)
🌐 [GitHub Repository](https://github.com/rajaditya-k)


