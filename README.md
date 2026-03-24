# B2B Lead Qualifier Agent 📞

Questo progetto implementa un **agente conversazionale vocale/testuale B2B** progettato per simulare una telefonata di qualificazione commerciale, avvalendosi di [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/). 

L'agente si occupa di qualificare lead di aziende (con focus sulla somministrazione del personale) guidando in modo naturale una conversazione per determinare il potenziale del cliente tramite un preciso albero decisionale.

## 🎯 Obiettivo e Albero Decisionale
L'agente identifica il potenziale del cliente seguendo tre livelli di priorità decrescente:

1. **Presenza Competitor**: Il cliente si affida già a un'agenzia? Se sì, si richiede il **volume massimo attuale**.
2. **Esperienza Passata**: Se attualmente non ha competitor, ha mai collaborato in passato con un'agenzia? Se sì, si richiede il **volume massimo storico**.
3. **Proxy (Tempo Determinato)**: Se non ha mai usato agenzie, quanti **dipendenti a tempo determinato** ha attualmente? (Utilizzato per stimare un potenziale di conversione).

L'agente gestisce in modo proattivo **divagazioni e risposte vaghe**, richiedendo cordialmente una stima numerica. Una volta ottenuti i dati esatti (livello e volume), viene chiamato in automatico un **Tool Python** per il salvataggio dei dati.

## 🛠️ Tecnologie Utilizzate
- **Google ADK** (Agent Development Kit) per la logica dell'agente.
- **Python 3.11+** e il pacchetto `uv` per la gestione ottimizzata delle dipendenze.
- **SQLite3** come database di appoggio (salvataggio locale).
- **Pytest** per gli unit test.

## 📂 Struttura del Progetto
- `app/agent.py`: Definizione principale dell'agente e import dei tool/prompt.
- `app/prompts.py`: Il "System Prompt" (Instruction) contente l'albero decisionale, le istruzioni di comportamento (empatia, gestione vaghezza, divieti) e il ruolo.
- `app/tools.py`: Contiene lo strumento `salva_qualificazione`, chiamato dall'agente per storicizzare la lead nel DB locale SQLite (`qualificazioni.db`).
- `tests/unit/`: Test suite locale tramite `pytest` con mock del database.

## 🚀 Come testarlo in locale

### 1. Installazione
Assicurati di aver configurato le credenziali per i servizi Google/Vertex AI e di avere `uv` installato:
```bash
make install
```

### 2. Esecuzione tramite Playground
L'ADK include una pratica interfaccia web. Avviala tramite il Makefile:
```bash
make playground
```
Il server sarà disponibile (solitamente) all'indirizzo `http://localhost:8501`. Apri il browser, seleziona l'ambiente (es. "app") e inizia a interagire testualmente con l'agente.

### 3. Verifica del salvataggio
Alla fine della qualificazione, l'agente salverà automaticamente la conversione confermata in `qualificazioni.db`. Per visualizzare i lead:
```bash
sqlite3 qualificazioni.db "SELECT * FROM qualificazioni;"
```

### 4. Avviare i Test (Unit)
La suite di test verifica che il Tool SQLite operi correttamente con mocking in-memory, isolandolo dal database principale.
```bash
uv run pytest tests/unit/test_tools.py -v
```