"""Real speech/cache smoke test on original text. No Gemini key required."""
from pathlib import Path
import time
from amazing_tts.storage import Library, DEFAULT_DATA
from amazing_tts.models import Script
from amazing_tts.pipeline import accept_script
from amazing_tts.audio import Renderer, export_mp3
url='https://novelping.com/book/original-audio-smoke-test'
lib=Library(DEFAULT_DATA / 'demo')
b=lib.book(url)
source={'number':1,'title':'Original cast test','url':url+'/chapter-1-test','text':'Mira stood beside the old gate. “Is anyone there?” “Yes,” Rowan answered. “Come inside.”','next_url':None}
script=Script.model_validate({'characters':[
{'id':'mira','name':'Mira','gender':'female','age':'young','traits':['bright'],'evidence':'Original test character: a young woman.'},
{'id':'rowan','name':'Rowan','gender':'male','age':'elder','traits':['deep'],'evidence':'Original test character: an elderly man.'}],
'segments':[
{'source':'Mira stood beside the old gate. ','text':'Mira stood beside the old gate.','speaker':'narrator','kind':'narration','confidence':1},
{'source':'“Is anyone there?” ','text':'Is anyone there?','speaker':'mira','kind':'dialogue','confidence':1},
{'source':'“Yes,” ','text':'Yes.','speaker':'rowan','kind':'dialogue','confidence':1},
{'source':'Rowan answered. ','text':'Rowan answered.','speaker':'narrator','kind':'narration','confidence':1},
{'source':'“Come inside.”','text':'Come inside.','speaker':'rowan','kind':'dialogue','confidence':1}],
'summary':'Mira meets Rowan.','notes':[]})
b.write('book.json',{'url':url,'title':'Original cast test'})
b.write('chapters/000001/source.json',source)
accept_script(b,source,script,approve=True)
t=time.monotonic();path=Renderer(lib).render(b,1,script,b.read('cast.json'));elapsed=time.monotonic()-t
before=path.stat().st_mtime_ns
cached=Renderer(lib).render(b,1,script,b.read('cast.json'))
assert cached.stat().st_mtime_ns==before
mp3=export_mp3(path)
print({'real_speech_seconds':round(elapsed,2),'duration':b.read('chapters/000001/audio.json')['duration_seconds'],'mp3':str(mp3),'cached_replay':True})
