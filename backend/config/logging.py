"""Structured JSON log formatter (stdlib only)."""
import json
import logging
from datetime import datetime, timezone

_RESERVED = set(logging.LogRecord('', 0, '', 0, '', (), None).__dict__) | {'message', 'asctime'}


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            'timestamp': datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'message': record.getMessage(),
        }
        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith('_'):
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False, default=str)
