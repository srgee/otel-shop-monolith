import json

def json_formatter(record):
    log_record = {
        'level': record.levelname,
        'message': record.getMessage(),
        'timestamp': record.created,
        'module': record.module,
    }
    return json.dumps(log_record)
