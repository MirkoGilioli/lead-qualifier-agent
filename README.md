# B2B Lead Qualifier Agent 📞 (v2.0.0)

Questo progetto implementa un **agente conversazionale B2B avanzato** progettato per simulare una telefonata di qualificazione commerciale, avvalendosi di [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/).

Dalla versione **2.0.0**, il progetto adotta un'architettura **Multi-Agente (Delegation Pattern)** per separare la logica di ricerca dal dialogo di qualificazione.

## 🧠 Architettura Multi-Agente
Il sistema è composto da due entità che collaborano:

1.  **Root Agent (Qualificatore)**: Gestisce il dialogo con l'utente, l'empatia e la raccolta dei dati commerciali (Tiers).
2.  **Sub-Agent (Ricercatore)**: Un agente specializzato che utilizza il tool `google_search` per profilare l'azienda in tempo reale non appena l'utente ne fornisce il nome.

Questa separazione permette all'agente principale di essere più informato e professionale, citando dettagli reali dell'azienda (prodotti, brand, sedi) durante la conversazione.

## 🎯 Obiettivo e Albero Decisionale
L'agente identifica il potenziale del cliente seguendo tre livelli di priorità decrescente:

1.  **Presenza Competitor**: Il cliente si affida già a un'agenzia? (Volume massimo attuale).
2.  **Esperienza Passata**: Se attualmente non ha competitor, ha mai collaborato in passato con un'agenzia? (Volume massimo storico).
3.  **Proxy (Tempo Determinato)**: Se non ha mai usato agenzie, quanti dipendenti a tempo determinato ha attualmente?

## 🛠️ Tecnologie Utilizzate
- **Google ADK** per l'orchestrazione multi-agente e la logica di delegazione.
- **Google Gemini 3 Flash** (Vertex AI) per ragionamento veloce e supporto nativo a Google Search.
- **Google Cloud Firestore** per la persistenza dei dati (arricchiti con nome e descrizione azienda).
- **Python 3.11+** e `uv` per la gestione delle dipendenze.
- **Terraform** per l'infrastruttura Cloud e CI/CD.

## 📂 Struttura del Progetto (Modulare)
- `app/agent.py`: Entry point che definisce il Root Agent e la logica di delegazione.
- `app/agents/researcher.py`: Definizione del sub-agente specializzato nella ricerca.
- `app/prompts.py`: Contiene le istruzioni di sistema per entrambi gli agenti.
- `app/tools.py`: Strumenti personalizzati, incluso il salvataggio arricchito su Firestore.
- `tests/eval/`: Suite di valutazione qualitativa (**LLM-as-a-Judge**) per misurare empatia e precisione.

## 🚀 Come testarlo in locale

### 1. Installazione e Autenticazione
```bash
make install
gcloud auth application-default login
```

### 2. Esecuzione tramite Playground
L'ADK include un'interfaccia web per testare la delegazione in tempo reale:
```bash
make playground
```
*💡 Suggerimento: Prova a dire "Lavoro per Ferrero Spa" e osserva come il ricercatore entra in azione.*

### 3. Suite di Test e Valutazione
- **Unit & Integration**: `make test`
- **Qualitative Evaluation**: `make eval` (Utilizza un LLM per giudicare l'agente).

---
*Per maggiori dettagli sulla valutazione qualitativa, consulta [tests/eval/evalsets/README.md](tests/eval/evalsets/README.md).*
