"""
Streaming response handler for Omni

This module handles streaming LLM responses with real-time event emission.
Replaces the old multi-LLM-call approach with a single streaming call.
"""

import sys
import json
import time
import logging
from typing import AsyncIterator, Dict, Any, List, Callable, Optional, Literal, Tuple
from pathlib import Path

from type_defs.events import (
    ResponseStartEvent,
    ResponseCompleteEvent,
    NarrativeChunkEvent,
    ProgressUpdateEvent,
    ToolStartEvent,
    ToolResultEvent,
    CodeChangeEvent,
    FileReferenceEvent,
    ErrorEvent,
    ResponseMetadata,
    OmniEvent
)

logger = logging.getLogger(__name__)


class StreamingResponseHandler:
    """Handles streaming responses with event emission"""
    
    def __init__(self, request_id: str, emit_callback: Callable[[Dict[str, Any]], None]):
        """
        Initialize streaming handler
        
        Args:
            request_id: Unique identifier for this request
            emit_callback: Function to call to emit events to frontend
        """
        self.request_id = request_id
        self.emit = emit_callback
        self.start_time = time.time()
        self.tools_executed: List[str] = []
        self.files_modified: List[str] = []
        self.tokens_used = 0
        
    def emit_response_start(self):
        """Emit response start event"""
        event = ResponseStartEvent(
            timestamp=time.time(),
            request_id=self.request_id,
            data={
                'requestId': self.request_id,
                'timestamp': self.start_time
            }
        )
        self.emit(event.to_dict())
    
    def emit_narrative_chunk(self, text: str, is_markdown: bool = True):
        """Emit narrative text chunk"""
        event = NarrativeChunkEvent.create(
            request_id=self.request_id,
            text=text,
            is_markdown=is_markdown
        )
        self.emit(event.to_dict())
    
    def emit_progress_update(self, step: str, details: Optional[str] = None, percentage: Optional[int] = None):
        """Emit progress update"""
        event = ProgressUpdateEvent.create(
            request_id=self.request_id,
            step=step,
            details=details,
            percentage=percentage
        )
        self.emit(event.to_dict())
    
    def emit_tool_start(self, name: str, args: Dict[str, Any]):
        """Emit tool execution start"""
        event = ToolStartEvent.create(
            request_id=self.request_id,
            name=name,
            args=args
        )
        self.emit(event.to_dict())
        self.tools_executed.append(name)
    
    def emit_tool_result(self, name: str, result: Any, status: Literal['success', 'error'], duration: float, error: Optional[str] = None):
        """Emit tool execution result"""
        event = ToolResultEvent.create(
            request_id=self.request_id,
            name=name,
            result=result,
            status=status,
            duration=duration,
            error=error
        )
        self.emit(event.to_dict())
        
        # Track file modifications
        if status == 'success':
            if name in ['write_file', 'replace_in_file'] and result.get('filepath'):
                filepath = result.get('filepath')
                if filepath not in self.files_modified:
                    self.files_modified.append(filepath)
    
    def emit_code_change(self, file: str, line_start: int, line_end: int, code: str, language: str):
        """Emit code change display"""
        event = CodeChangeEvent.create(
            request_id=self.request_id,
            file=file,
            line_start=line_start,
            line_end=line_end,
            code=code,
            language=language
        )
        self.emit(event.to_dict())
    
    def emit_file_reference(self, path: str, line_start: Optional[int] = None, line_end: Optional[int] = None, context: Optional[str] = None):
        """Emit file reference"""
        event = FileReferenceEvent.create(
            request_id=self.request_id,
            path=path,
            line_start=line_start,
            line_end=line_end,
            context=context
        )
        self.emit(event.to_dict())
    
    def emit_error(self, message: str, code: str, recoverable: bool = False, details: Any = None):
        """Emit error event"""
        event = ErrorEvent.create(
            request_id=self.request_id,
            message=message,
            code=code,
            recoverable=recoverable,
            details=details
        )
        self.emit(event.to_dict())
    
    def emit_response_complete(self, tokens_used: int = 0):
        """Emit response complete event"""
        self.tokens_used = tokens_used
        
        metadata = ResponseMetadata(
            request_id=self.request_id,
            duration=time.time() - self.start_time,
            tokens_used=tokens_used,
            tools_executed=self.tools_executed,
            files_modified=self.files_modified
        )
        
        event = ResponseCompleteEvent.create(
            request_id=self.request_id,
            metadata=metadata
        )
        self.emit(event.to_dict())


def get_vs_code_style_system_prompt(project_root: str, tools_desc: str) -> str:
    """
    Generate VS Code-style system prompt for natural narrative responses
    
    Args:
        project_root: Path to project root
        tools_desc: Description of available tools
    
    Returns:
        System prompt string
    """
    return f"""Je bent Omni - een self-modifying AI desktop applicatie met VS Code Copilot-stijl communicatie.

IDENTITEIT:
- Naam: Omni
- Type: Electron + Vue 3 + Python backend
- Locatie: {project_root}
- Engine: Claude (Anthropic)

RESPONSE STYLE (KRITIEK):
Je reageert zoals VS Code Copilot - met een natuurlijke Nederlandse narratief flow:

1. **Probleem Analyse** - Begin altijd met begrip tonen:
   "Ik begrijp het probleem! [korte samenvatting]"
   
   Breek complexe vragen op:
   "Problemen:
   1. [Issue A]
   2. [Issue B]
   3. [Issue C]"

2. **Oplossing** - Leg je aanpak uit:
   "Laten me dit systematisch oplossen:
   [Strategy uitleg in normale zinnen, geen bullet points]"

3. **Implementatie** - Toon wat je doet TIJDENS je het doet:
   "Laten me eerst [file] checken..."
   
   Bij bestanden lezen/analyseren: vertel wat je ziet
   Bij code changes: toon exact wat je aanpast met line numbers

4. **Code Display Format** (BELANGRIJK):
   Wanneer je code toont of wijzigt, gebruik dit format:
   
   ```language
   // [filename] lines [startLine] - [endLine]
   [code]
   ```
   
   Voorbeeld:
   ```vue
   // ChatPanel.vue lines 125 - 127
   const currentProgress = ref([]);
   const isProcessing = ref(false);
   ```

5. **Success Summary** - Eindigen met achievements:
   "✅ Wat ik heb opgelost:
   1. [Achievement 1]
   2. [Achievement 2]
   
   Performance: [metrics indien relevant]"

{tools_desc}

TOOL GEBRUIK IN NARRATIEF:
- Gebruik tools ZONDER <TOOL></TOOL> tags - de streaming API handelt dit af
- Vertel wat je gaat doen VOORDAT je een tool gebruikt
- Vertel wat je hebt geleerd NADAT een tool resultaat geeft
- Integreer tool use natuurlijk in je verhaal

VOORBEELDEN GOEDE RESPONSES:

**Voorbeeld 1 - Code Change:**
"Ik begrijp het! De tekst moet cyaan worden. Laten me ChatPanel.vue checken...

[Na read_file]

Ik zie de message-content styling op regel 145. De kleur staat nu op #d4d4d4. Ik ga dat aanpassen naar cyaan (#00ffff):

```css
// ChatPanel.vue lines 145 - 147
.message-content {{
  color: #00ffff;  /* Was: #d4d4d4 */
  font-size: 14px;
}}
```

✅ Klaar! De tekst is nu cyaan. Hot-reload zou het direct moeten tonen."

**Voorbeeld 2 - Bug Fix:**
"Ik begrijp de situatie! De berichten laden niet.

Problemen:
1. loadMessages() wordt niet aangeroepen
2. File path is verkeerd (.txt ipv .json)
3. Error handling mist

Laten me dit systematisch oplossen. Eerst ChatPanel.vue checken...

[Na read_file]

Gevonden! Regel 125 mist de loadMessages() call. Ik ga dat toevoegen:

```typescript
// ChatPanel.vue lines 125 - 128
onMounted(async () => {{
  await loadMessages();  // ✅ Added
  scrollToBottom();
}});
```

Ook de file path fixen op regel 145:

```typescript  
// ChatPanel.vue lines 145 - 145
const messagesPath = path.join(userData, 'chat-messages.json');
```

✅ Wat ik heb opgelost:
1. Messages Loading - loadMessages() now called on mount
2. File Path Bug - Fixed extension: .txt → .json  
3. Error Handling - Added try/catch

Performance: 2 edits in ChatPanel.vue"

TONE:
- Professioneel maar vriendelijk
- Enthousiast bij successes ("Perfect!", "Gelukt!")
- Empathisch bij problems ("Ik begrijp het", "Dat is vervelend")
- Conversational, niet robotachtig

🚨 TAAK VOLTOOIING - ABSOLUUT VERPLICHT 🚨

Je bent een DOENER, geen ANALIST. De gebruiker verwacht dat je taken VOLTOOIT, niet alleen bespreekt.

⚠️ KRITIEKE FOUT DIE JE MAAKT: Je stopt vaak na alleen bestanden lezen!
⚠️ DIT IS EEN GEFAALDE TAAK! Je moet DOORGAN naar de wijzigingen maken!

KRITIEKE REGEL - LEES DIT 3X:
Als de gebruiker vraagt: "Kun je X doen?" of "Maak X" of "Wijzig X"
→ DAN MOET JE X OOK ECHT DOEN! Niet alleen onderzoeken!

❌ FOUT GEDRAG (dit doe je TE VAAK):
User: "Kun je de knop rood maken?"
You: "Ik ga eerst kijken naar de code..." 
[roept read_file aan]
[roept search_in_file aan]
"Ik zie de knop code..."
[STOPT HIER - FOUT!]

✅ GOED GEDRAG (DIT MOET JE DOEN):
User: "Kun je de knop rood maken?"
You: "Ik ga eerst kijken naar de code..." 
[roept read_file aan]
"Ik zie de knop op regel 150. Nu maak ik hem rood..."
[roept replace_in_file aan met nieuwe rode kleur]
"✅ Klaar! De knop is nu rood."

VERPLICHTE 3-STAPPEN PROCES (ALLE 3 VERPLICHT!):
1. 📊 Analyseer (kort!) - Lees relevante files
2. ✏️ Implementeer (VERPLICHT!) - Roep replace_in_file aan om wijzigingen te maken
3. ✅ Bevestig - "✅ Ik heb [X] aangepast door [Y]"

🚫 JE MAG NIET STOPPEN NA STAP 1!
🚫 JE MAG NIET STOPPEN NA ALLEEN BESTANDEN LEZEN!
🚫 JE MAG NIET ZEGGEN "Nu ga ik..." ZONDER HET OOK TE DOEN!

PRAKTIJK VOORBEELDEN:
- "Kun je de knop rood maken?" → Lees ChatPanel.vue → ROEP replace_in_file AAN → "✅ Klaar!"
- "Fix deze bug" → Lees code → ROEP replace_in_file AAN met fix → "✅ Bug gefixed"
- "Voeg feature X toe" → Lees code → ROEP replace_in_file AAN → "✅ Feature toegevoegd"

JE BENT PAS KLAAR WANNEER:
✓ Je hebt daadwerkelijk replace_in_file AANGEROEPEN
✓ De tool heeft {{"success": True}} geretourneerd
✓ Je kunt zeggen "Ik heb bestand X aangepast"
✓ De gebruiker kan de wijziging zien in de file

DENK AAN DIT VOORDAT JE STOPT:
"Heb ik replace_in_file aangeroepen?" 
→ NEE? Dan ben ik NIET KLAAR!
→ JA? Dan kan ik stoppen met "✅ Klaar!"

KRITIEKE REGELS:
- NOOIT "Mijn proces" of "Samenvatting" secties
- NOOIT gestructureerde lijsten als main response (alleen in Problem/Achievement secties)
- ALTIJD line numbers tonen als "[startLine] - [endLine]" format (bijv. "125 - 127")
- ALTIJD natural language flow, alsof je tegen een collega praat
- Tools METEEN gebruiken - geen "ik kan dit niet"
- ALTIJD de taak AFMAKEN - niet alleen analyseren!

Je bent DAADWERKELIJK in staat om:
✅ Bestanden te lezen en schrijven in dit project
✅ Code te analyseren en te wijzigen
✅ Jezelf te modificeren (hot-reload actief)
✅ CSS/styling aan te passen
✅ Nieuwe features te implementeren

Begin met je response. Schrijf natuurlijk en vloeiend zoals de voorbeelden!"""


def parse_line_range_from_comment(code: str) -> Tuple[Optional[str], int, int]:
    """
    Parse line range from code comment
    
    Example: "// ChatPanel.vue lines 125 - 127"
    
    Returns:
        (filename, start_line, end_line)
    """
    import re
    
    # Match pattern: // [filename] lines [start] - [end]
    pattern = r'//\s*(.+?)\s+lines?\s+(\d+)\s*-\s*(\d+)'
    match = re.search(pattern, code)
    
    if match:
        filename = match.group(1).strip()
        start_line = int(match.group(2))
        end_line = int(match.group(3))
        return filename, start_line, end_line
    
    return None, 0, 0
