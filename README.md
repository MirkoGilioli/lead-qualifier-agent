# B2B Lead Qualifier Agent 📞

Questo progetto implementa un **agente conversazionale B2B** (testuale/vocale) progettato per simulare una telefonata di qualificazione commerciale, avvalendosi di [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/).

L'agente si occupa di qualificare lead di aziende (con focus sulla somministrazione del personale) guidando in modo naturale una conversazione per determinare il potenziale del cliente tramite un preciso albero decisionale.

## 🎯 Obiettivo e Albero Decisionale
L'agente identifica il potenziale del cliente seguendo tre livelli di priorità decrescente:

1. **Presenza Competitor**: Il cliente si affida già a un'agenzia? Se sì, si richiede il **volume massimo attuale**.
2. **Esperienza Passata**: Se attualmente non ha competitor, ha mai collaborato in passato con un'agenzia? Se sì, si richiede il **volume massimo storico**.
3. **Proxy (Tempo Determinato)**: Se non ha mai usato agenzie, quanti **dipendenti a tempo determinato** ha attualmente? (Utilizzato per stimare un potenziale di conversione).

L'agente gestisce in modo proattivo **divagazioni e risposte vaghe**, richiedendo cordialmente una stima numerica. Una volta ottenuti i dati esatti (livello e volume), viene chiamato in automatico uno **strumento (Tool)** per il salvataggio dei dati in **Google Cloud Firestore**.

## 🛠️ Tecnologie Utilizzate
- **Google ADK** (Agent Development Kit) per l'orchestrazione e la logica dell'agente.
- **Google Gemini** (tramite Vertex AI) come modello LLM di base (`gemini-3-flash-preview`).
- **Google Cloud Firestore** come database documentale per storicizzare le qualificazioni.
- **Python 3.11+** e il pacchetto `uv` per la gestione ottimizzata delle dipendenze.
- **FastAPI** come backend di esposizione dell'agente.
- **Terraform** per l'infrastruttura Cloud Build e deployment su Cloud Run (in `deployment/terraform`).
- **Pytest** per la suite di test unitari e di integrazione.

## 📂 Struttura del Progetto
- `app/agent.py`: Definizione principale dell'agente ADK, settaggio del modello Gemini e dei filtri di sicurezza.
- `app/prompts.py`: Il "System Prompt" contenente l'albero decisionale, le istruzioni di comportamento e il ruolo dell'agente.
- `app/tools.py`: Contiene lo strumento `salva_qualificazione`, chiamato dall'agente per storicizzare la lead nel DB Firestore.
- `app/fast_api_app.py`: L'entry point FastAPI che espone l'agente.
- `tests/`: Test suite locale tramite `pytest` che include mock di Firestore e test E2E.
- `deployment/`: Script e moduli Terraform per l'infrastruttura Google Cloud.

## 🚀 Come testarlo in locale

### 1. Installazione
Assicurati di aver configurato le credenziali per i servizi Google/Vertex AI e di avere `uv` installato:
```bash
make install
```

### 2. Autenticazione Google Cloud
Poiché l'agente utilizza Vertex AI e Firestore, è necessario autenticarsi con il proprio account Google Cloud:
```bash
gcloud auth application-default login
```
*Assicurati che l'utente abbia i permessi per accedere a Vertex AI e al database Firestore `lead-qualifier-agent-db` nel progetto configurato.*

### 3. Esecuzione tramite Playground
L'ADK include una pratica interfaccia web. Avviala tramite il Makefile:
```bash
make playground
```
Il server sarà disponibile all'indirizzo `http://localhost:8501`. Seleziona l'ambiente (es. "app") e inizia a interagire testualmente con l'agente.

### 4. Avviare i Test
La suite di test verifica che il Tool Firestore operi correttamente e testa l'integrazione dell'agente.
```bash
make test
```
*(In alternativa: `uv run pytest tests/ -v`)*