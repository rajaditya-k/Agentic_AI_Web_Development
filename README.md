
# 🤖 Objective

The objective of this project is to check the feasibility of leveraging **Agentic AI** as a development partner in full-stack web development by automating the traditional development workflow. 

# 🤖 Agentic Full-Stack Web Development Automation

This is a **self-tried experimental project** aimed at automating the full-stack web development lifecycle using **Agentic AI** and the **LangGraph framework**.
The project demonstrates how autonomous AI agents can collaboratively handle each stage of web development — from wireframing and mockups to API design, coding, and documentation.

---

## 🔍 Key Highlights

* **Automate the full-stack web development lifecycle** using Agentic AI.
* **Replace traditional sequential development steps** (wireframing, mockups, API design, coding) with **dedicated AI agents** for each phase.
* **Enable seamless end-to-end project creation** and **automatic documentation updates**.
* **Used Azure MCP Servers** for simplified provisioning of Azure Resources. 

## 🔍 Benefits

* **Rapid generation** of modular full-stack codebases(frontend, backend, tests) leveraging AI models.
* The code can be scaled up into an **end to end full fledged application** by connecting to the appropriate database and by improving the frontend.
* **AI-Powered documentation** with line-by-line code explanations.
* **Customizable prompts** and agent nodes for tailored development workflows.
* **Easy-to-use** interface for project creation, updates, and downloads.

---

## ⚙️ Setup Instructions

Follow these steps to set up and run the project locally:

### 1. Clone the repository

```bash
git clone https://github.com/rajaditya-k/Agentic_AI_Web_Development.git
cd Agentic_AI_Web_Development
```

### 2. Create a `.env` file

Create a file named `.env` in the root directory and add the required environment variables (such as API keys or credentials).

Example:

```
OPENAI_API_KEY=your_api_key_here
LANGGRAPH_API_KEY=your_langgraph_key
```
For this project, the variables are 
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

Install all required packages:

```bash
pip install -r requirements.txt
```

### 4. Run the Streamlit application

Start the Streamlit interface:

```bash
streamlit run app.py
```

---

## 🧠 Tech Stack

* **Programming Language** - Python
* **Streamlit** – for building the interactive interface
* **LangGraph Framework** – To manage multi-agent workflows
* **Promt Management** – POML(Prompt Orchestration Markup Language)
* **OpenAI / LLM APIs** – for natural language reasoning and generation
* **Cloud Services** – Azure CosmoDB to store user details, Azure Blob Storage to store the generated web project content and Azure Event Hubs for streaming logs
* **Azure MCP Server** – Used to provision the Azure Cloud Services without manually creating them
* **IDE** – Cursor IDE

---

## 📁 Project Structure

```
Agentic_AI_Web_Development/
│
├── app.py                 # Streamlit application entry point
├── web_app_creator_pomls/ # Contains all the prompts in prompt orchestration markup language
├── include/               # Helper functions
├── graphs/                # Contains the Multi Agent Workflow steps
├── db/                    # Contains the functions to interact with Azure Cloud Services
├── core/                  # Reads all the variables in .env file that can be used within the project. Also contains the Agentic AI Langgraph State Models
├── auth/                  # Contains the logic to manage the users of the streamlit application
├── requirements.txt       # Dependencies
├── .env.example           # Example environment configuration
└── README.md              # Project documentation
```

---

## 🧩 How It Works

1. **User Input:** Define project requirements through the Streamlit UI.
2. **Agent Workflow:** LangGraph coordinates specialized AI agents — for wireframing, API design, frontend/backend code generation, and documentation.
3. **Output Delivery:** The system generates project artifacts and keeps documentation updated dynamically. The projects can also be viewed in a separate tab

---

## 📌 Notes

* This is a **self-experimented prototype**, showcasing the potential of AI-driven development workflows.
* The goal is to explore **how multiple AI agents can collaborate** to automate different stages of the software lifecycle.
* To expplore **Azure MCP Server**, refer to [https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/get-started/tools/cursor]
* Contributions, suggestions, and discussions are welcome!

---

## 🔍 Next Steps

* **Experiment with prompt variations** in POML to improve agent performance and output quality


---
## 🧑‍💻 Author

**Raj Aditya Kumar**
Sr Data Engineer | Passionate about Data Engineering and Autonomous AI Systems

📧 [adrj0596@gmail.com](mailto:adrj0596@gmail.com)

🌐 [Linkedin Profile](https://linkedin.com/in/rajadityakumar)

🌐 [Github Repository](https://github.com/rajaditya-k)



---










