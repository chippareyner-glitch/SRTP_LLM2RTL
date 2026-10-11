"""Bounded recovery for interrupted responses, with per-attempt evidence."""
import http.client
import json
import os
import ssl
import time
import urllib.error
from pathlib import Path
from llm_client import call_llm

def transient(error):
    if isinstance(error,urllib.error.HTTPError):return error.code in (429,500,502,503,504)
    if isinstance(error,ssl.SSLCertVerificationError):return False
    if isinstance(error,urllib.error.URLError):
        return not isinstance(error.reason,ssl.SSLCertVerificationError)
    if isinstance(error,(http.client.IncompleteRead,http.client.RemoteDisconnected,ConnectionError,TimeoutError,ssl.SSLEOFError)):
        return True
    return any(f'DeepSeek HTTP {code}:' in str(error) for code in (429,500,502,503,504))

def request_json(system,user,directory,invoke=None,sleep=time.sleep):
    invoke=invoke or call_llm
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    os.environ['LLM_LOG_DIR']=str(directory/'api_logs')
    effort=os.getenv('JSON_REASONING_EFFORT','none')
    attempts=[];length_fallback=False
    for index in range(3):
        record={'attempt':index+1,'reasoning_effort':effort,'started_unix':time.time()}
        try:
            value=invoke(system,user,reasoning_effort=effort)
            record['status']='success';attempts.append(record)
            (directory/'request_attempts.json').write_text(json.dumps(attempts,ensure_ascii=False,indent=2),encoding='utf-8')
            return value
        except Exception as exc:
            message=str(exc)
            record.update(status='error',error_type=type(exc).__name__,error=message)
            attempts.append(record)
            (directory/'request_attempts.json').write_text(json.dumps(attempts,ensure_ascii=False,indent=2),encoding='utf-8')
            is_length=message.startswith("Incomplete completion: 'length'")
            if is_length and not length_fallback and effort!='none' and index<2:
                effort='none';length_fallback=True
                print('API 输出截断：下一次改用非思考模式生成紧凑 JSON（已记录配置变化）。',flush=True)
                user+='\nReturn compact JSON only. Use repeat/model variables instead of enumerating long traces.'
                continue
            if transient(exc) and index<2:
                print(f'API 连接或服务暂时异常，{2**(index+1)} 秒后重试（最多3次请求）。',flush=True)
                sleep(2**(index+1));continue
            raise
