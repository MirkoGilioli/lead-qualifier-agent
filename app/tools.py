# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Questo modulo definisce gli strumenti (Tools) a disposizione dell'agente.
Lo strumento principale è salva_qualificazione, il quale permette all'agente di storicizzare
i risultati della lead qualification all'interno di un database Firestore.
"""

import datetime
from google.cloud import firestore

# Inizializza il client Firestore utilizzando lo specifico database creato per il progetto
# Nome database: lead-qualifier-agent-db (creato tramite l'infrastruttura Terraform)
db = firestore.Client(database="lead-qualifier-agent-db")

def salva_qualificazione(tipo: str, volume: int) -> str:
    """
    Salva la qualificazione commerciale estratta nel database Firestore.
    Da chiamare SOLO quando l'utente ha fornito chiaramente sia il tipo di potenziale 
    (competitor, storico, proxy) sia il numero esatto associato.

    Args:
        tipo: Il tipo di qualificazione. Valori ammessi: 'competitor', 'storico', 'proxy'.
        volume: Il numero di lavoratori stimato o effettivo (intero).

    Returns:
        Stringa di conferma dell'avvenuto salvataggio.
    """
    try:
        # Crea un riferimento alla collection 'qualificazioni'
        doc_ref = db.collection("qualificazioni").document()
        
        # Dati da salvare
        data = {
            "tipo": tipo,
            "volume": volume,
            "timestamp": datetime.datetime.now(tz=datetime.timezone.utc)
        }
        
        # Salva i dati su Firestore
        doc_ref.set(data)
        
        return f"Qualificazione salvata con successo su Firestore: {tipo} con volume {volume}."
    except Exception as e:
        return f"Errore durante il salvataggio su Firestore: {str(e)}"
