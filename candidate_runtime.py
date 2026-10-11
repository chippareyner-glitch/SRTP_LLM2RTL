"""Shared configuration and bounded API transport for candidate experiments."""
import json
import time
import uuid
from pathlib import Path

from config import DATASET_DIR, IVERILOG, VVP, ARK_MODEL
from llm_client import call_llm
from rtl_json_pipeline.api import transient

ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET = Path(DATASET_DIR)
DEFAULT_IVERILOG = Path(IVERILOG)
DEFAULT_VVP = Path(VVP)


def call_api(args, system, user):
    """Keep configured reasoning fixed for comparable experiments; never retry auth."""
    logs = Path(getattr(args, 'api_log_root', ROOT / 'experiments' / 'candidate_api_logs')) / uuid.uuid4().hex
    logs.mkdir(parents=True)
    attempts = []
    token_limit = args.max_tokens
    for index in range(3):
        try:
            content, meta = call_llm(
                system, user, model=args.model, reasoning_effort=args.reasoning_effort,
                max_tokens=token_limit, temperature=args.temperature,
                return_metadata=True, log_dir=logs,
            )
            attempts.append({'attempt': index + 1, 'status': 'success', 'max_tokens': token_limit})
            meta['request_attempts'] = len(attempts)
            meta['attempt_log'] = str(logs / 'attempts.json')
            return content, meta
        except Exception as exc:
            attempts.append({'attempt': index + 1, 'status': 'error', 'error': str(exc), 'max_tokens': token_limit})
            if str(exc).startswith("Incomplete completion: 'length'") and token_limit < 32768 and index < 2:
                token_limit = min(32768, token_limit * 2)
                print(f'API回复截断，增加输出预算到 {token_limit} 后重试。', flush=True)
                continue
            if index == 2 or not transient(exc):
                raise
            print(f'API 临时异常，准备重试 {index + 2}/3', flush=True)
            time.sleep(2 ** (index + 1))
        finally:
            (logs / 'attempts.json').write_text(json.dumps(attempts, ensure_ascii=False, indent=2), encoding='utf-8')


def as_text(value):
    return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else (value or '')
