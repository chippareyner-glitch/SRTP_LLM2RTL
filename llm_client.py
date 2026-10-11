"""DeepSeek API client shared by generation, review and repair."""
import os
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parent
for line in (ROOT / '.env').read_text(encoding='utf-8').splitlines() if (ROOT / '.env').exists() else []:
    if line.strip() and not line.lstrip().startswith('#') and '=' in line:
        name, value = line.split('=', 1)
        os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))

ARK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
REVIEWER_ARK_API_KEY = ARK_API_KEY
ARK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-flash')
REVIEWER_ARK_MODEL = os.getenv('DEEPSEEK_REVIEWER_MODEL', ARK_MODEL)

def call_llm(system_prompt, user_prompt, model=None, case_id=None, reasoning_effort=None,
             max_tokens=None, temperature=None, return_metadata=False, log_dir=None):
    if not ARK_API_KEY:
        raise RuntimeError('Missing DEEPSEEK_API_KEY; configure the local .env file.')
    selected = model or ARK_MODEL
    if selected.startswith('ep-'):
        raise ValueError('Ark endpoint IDs cannot be used with DeepSeek. Set DEEPSEEK_MODEL.')
    effort = reasoning_effort or os.getenv('DEEPSEEK_REASONING_EFFORT', 'high')
    payload = {'model': selected,
        'messages': [{'role':'system','content':system_prompt}, {'role':'user','content':user_prompt}],
        'stream':False, 'reasoning_effort':effort,
        'max_tokens':int(max_tokens if max_tokens is not None else os.getenv('DEEPSEEK_MAX_TOKENS','32768'))}
    if temperature is not None:
        payload['temperature']=temperature
    started=time.monotonic()
    request=urllib.request.Request('https://api.deepseek.com/chat/completions',
        headers={'Authorization':f'Bearer {ARK_API_KEY}','Content-Type':'application/json'},
        data=json.dumps(payload).encode('utf-8'),method='POST')
    try:
        with urllib.request.urlopen(request,timeout=300) as response:
            data=json.load(response)
    except urllib.error.HTTPError as error:
        labels={400:'invalid request/model/parameters',401:'invalid API key',402:'insufficient balance',429:'rate limited',500:'server error',503:'service unavailable'}
        try:detail=json.loads(error.read().decode('utf-8','replace')).get('error',{}).get('message','')
        except Exception:detail=''
        # A real input-too-long rejection arrives here as HTTP 400 with the server's message (e.g. context length).
        raise RuntimeError(f'DeepSeek HTTP {error.code}: {labels.get(error.code,"request failed")}. No RTL generated.'
                           +(f' Server: {detail[:300]}' if detail else '')) from None
    choices=data.get('choices') or []
    choice=choices[0] if choices else {}
    metadata={'time_utc':datetime.now(timezone.utc).isoformat(),'requested_model':selected,'case_id':case_id,
        'returned_model':data.get('model'),'id':data.get('id'),'usage':data.get('usage'),
        'finish_reason':choice.get('finish_reason'),'reasoning_effort':effort,
        'max_tokens':payload['max_tokens'],'temperature':temperature,'elapsed_seconds':time.monotonic()-started}
    logdir=Path(log_dir or os.getenv('LLM_LOG_DIR',str(ROOT/'experiments'/'api_logs')))
    logdir.mkdir(parents=True,exist_ok=True)
    (logdir/f'{uuid.uuid4().hex}.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    if choice.get('finish_reason')=='length':
        # Output cap, not input size: reasoning + answer used all of max_tokens before the answer finished.
        usage=data.get('usage') or {}
        reasoning=(usage.get('completion_tokens_details') or {}).get('reasoning_tokens')
        raise RuntimeError(f"Incomplete completion: 'length'; output hit max_tokens={payload['max_tokens']} "
            f"(prompt {usage.get('prompt_tokens')} tokens, completion {usage.get('completion_tokens')} of which "
            f"reasoning {reasoning}); the prompt was not too long; inspect API logs.")
    if choice.get('finish_reason')!='stop':
        raise RuntimeError(f"Incomplete completion: {choice.get('finish_reason')!r}; inspect API logs.")
    content=choice.get('message',{}).get('content')
    if not isinstance(content,str) or not content.strip():
        raise RuntimeError('Empty final content returned; no RTL generated.')
    return (content,metadata) if return_metadata else content

def call_reviewer_llm(system_prompt,user_prompt,model=None):
    return call_llm(system_prompt,user_prompt,model or REVIEWER_ARK_MODEL)
