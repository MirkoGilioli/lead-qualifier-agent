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

import datetime
from google.cloud import firestore

# Initialize Firestore client using the specific database created
# Database name: lead-qualifier-agent-db
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
        # Create a reference to the 'qualificazioni' collection
        doc_ref = db.collection("qualificazioni").document()
        
        # Data to be saved
        data = {
            "tipo": tipo,
            "volume": volume,
            "timestamp": datetime.datetime.now(tz=datetime.timezone.utc)
        }
        
        # Save the data to Firestore
        doc_ref.set(data)
        
        return f"Qualificazione salvata con successo su Firestore: {tipo} con volume {volume}."
    except Exception as e:
        return f"Errore durante il salvataggio su Firestore: {str(e)}"
