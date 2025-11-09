"""
Omni Streaming Event Protocol - Python Types

Type definitions for streaming events between backend and frontend.
All events follow a consistent structure for type safety and validation.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Literal, Optional, Union
from datetime import datetime
import time


@dataclass
class BaseEvent:
    """Base structure for all events"""
    timestamp: float
    request_id: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization"""
        result = asdict(self)
        # Ensure camelCase for frontend compatibility
        result['requestId'] = result.pop('request_id')
        return result


@dataclass
class ResponseStartEvent(BaseEvent):
    """Emitted when response streaming begins"""
    type: Literal['response_start'] = 'response_start'
    data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.data:
            self.data = {
                'requestId': self.request_id,
                'timestamp': self.timestamp
            }


@dataclass
class ResponseMetadata:
    """Metadata about completed response"""
    request_id: str
    duration: float
    tokens_used: int
    tools_executed: List[str]
    files_modified: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'requestId': self.request_id,
            'duration': self.duration,
            'tokensUsed': self.tokens_used,
            'toolsExecuted': self.tools_executed,
            'filesModified': self.files_modified
        }


@dataclass
class ResponseCompleteEvent(BaseEvent):
    """Emitted when response streaming completes"""
    type: Literal['response_complete'] = 'response_complete'
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, request_id: str, metadata: ResponseMetadata):
        return cls(
            type='response_complete',
            timestamp=time.time(),
            request_id=request_id,
            data={'metadata': metadata.to_dict()}
        )


@dataclass
class NarrativeChunkEvent(BaseEvent):
    """Emitted for each chunk of narrative text"""
    type: Literal['narrative_chunk'] = 'narrative_chunk'
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, request_id: str, text: str, is_markdown: bool = True):
        return cls(
            type='narrative_chunk',
            timestamp=time.time(),
            request_id=request_id,
            data={
                'text': text,
                'isMarkdown': is_markdown
            }
        )


@dataclass
class ProgressUpdateEvent(BaseEvent):
    """Emitted for progress updates during processing"""
    type: Literal['progress_update'] = 'progress_update'
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, request_id: str, step: str, details: Optional[str] = None, percentage: Optional[int] = None):
        data: Dict[str, Any] = {'step': step}
        if details:
            data['details'] = details
        if percentage is not None:
            data['percentage'] = percentage

        return cls(
            type='progress_update',
            timestamp=time.time(),
            request_id=request_id,
            data=data
        )


@dataclass
class ToolStartEvent(BaseEvent):
    """Emitted when tool execution begins"""
    type: Literal['tool_start'] = 'tool_start'
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, request_id: str, name: str, args: Dict[str, Any]):
        return cls(
            type='tool_start',
            timestamp=time.time(),
            request_id=request_id,
            data={
                'name': name,
                'args': args,
                'timestamp': time.time()
            }
        )


@dataclass
class ToolResultEvent(BaseEvent):
    """Emitted when tool execution completes"""
    type: Literal['tool_result'] = 'tool_result'
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, request_id: str, name: str, result: Any, status: Literal['success', 'error'], 
               duration: float, error: Optional[str] = None):
        data = {
            'name': name,
            'result': result,
            'status': status,
            'duration': duration
        }
        if error:
            data['error'] = error

        return cls(
            type='tool_result',
            timestamp=time.time(),
            request_id=request_id,
            data=data
        )


@dataclass
class CodeChangeEvent(BaseEvent):
    """Emitted when showing code changes"""
    type: Literal['code_change'] = 'code_change'
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, request_id: str, file: str, line_start: int, line_end: int, 
               code: str, language: str):
        return cls(
            type='code_change',
            timestamp=time.time(),
            request_id=request_id,
            data={
                'file': file,
                'lineStart': line_start,
                'lineEnd': line_end,
                'code': code,
                'language': language
            }
        )


@dataclass
class FileReferenceEvent(BaseEvent):
    """Emitted when referencing a file"""
    type: Literal['file_reference'] = 'file_reference'
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, request_id: str, path: str, line_start: Optional[int] = None,
               line_end: Optional[int] = None, context: Optional[str] = None):
        data: Dict[str, Any] = {'path': path}
        if line_start is not None:
            data['lineStart'] = line_start
        if line_end is not None:
            data['lineEnd'] = line_end
        if context:
            data['context'] = context

        return cls(
            type='file_reference',
            timestamp=time.time(),
            request_id=request_id,
            data=data
        )


@dataclass
class ErrorEvent(BaseEvent):
    """Emitted when an error occurs"""
    type: Literal['error'] = 'error'
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, request_id: str, message: str, code: str, recoverable: bool = False,
               details: Optional[Any] = None):
        data = {
            'message': message,
            'code': code,
            'recoverable': recoverable
        }
        if details:
            data['details'] = details

        return cls(
            type='error',
            timestamp=time.time(),
            request_id=request_id,
            data=data
        )


# Union type of all events
OmniEvent = Union[
    ResponseStartEvent,
    ResponseCompleteEvent,
    NarrativeChunkEvent,
    ProgressUpdateEvent,
    ToolStartEvent,
    ToolResultEvent,
    CodeChangeEvent,
    FileReferenceEvent,
    ErrorEvent
]


def validate_event(event_dict: Dict[str, Any]) -> bool:
    """Validate event structure"""
    if not isinstance(event_dict, dict):
        return False

    required_fields = ['type', 'timestamp', 'requestId', 'data']
    for field in required_fields:
        if field not in event_dict:
            return False

    if not isinstance(event_dict['type'], str):
        return False

    if not isinstance(event_dict['timestamp'], (int, float)):
        return False

    if not isinstance(event_dict['requestId'], str):
        return False

    if not isinstance(event_dict['data'], dict):
        return False

    return True
