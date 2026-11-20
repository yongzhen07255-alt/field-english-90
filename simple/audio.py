import hashlib,json,os,pathlib,re,subprocess,sys
import numpy as np,onnxruntime as ort,espeakng_loader
from kokoro_onnx import Kokoro
from kokoro_onnx.config import EspeakConfig
site,models=map(pathlib.Path,sys.argv[1:3]); shard,total=map(int,sys.argv[3:5]);assert 0<=shard<total
ffmpeg=os.environ.get('COURSE_FFMPEG','ffmpeg');data=os.environ.get('ESPEAK_DATA_PATH') or str(espeakng_loader.get_data_path())
model=models/'kokoro-v1.0.int8.onnx';voices=models/'voices-v1.0.bin'
for p,h in [(model,'6e742170d309016e5891a994e1ce1559c702a2ccd0075e67ef7157974f6406cb'),(voices,'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d')]:assert hashlib.sha256(p.read_bytes()).hexdigest()==h,p
opts=ort.SessionOptions();opts.intra_op_num_threads=2;opts.inter_op_num_threads=1
session=ort.InferenceSession(str(model),sess_options=opts,providers=['CPUExecutionProvider']);engine=Kokoro.from_session(session,str(voices),espeak_config=EspeakConfig(data_path=data))
lookup={'DHCP':'D H C P','DNS':'D N S','VPN':'V P N','WAN':'wan','Wi-Fi':'why fie','VLAN':'vee lan','VLANs':'vee lans','PoE':'P O E','IP':'I P','NAT':'nat','WPA3':'W P A three','WPA2':'W P A two','GHz':'gigahertz','LACP':'L A C P','IT':'I T','SSID':'S S I D','Fresnel':'freh nel'};pat=re.compile(r'\b(?:'+'|'.join(map(re.escape,lookup))+r')\b')
items=sorted(json.loads((site.parent/'simple-audio.json').read_text(encoding='utf8')).items())[shard::total];(site/'audio/simple').mkdir(parents=True,exist_ok=True)
for i,(name,en) in enumerate(items,1):
    p=site/name
    if p.is_file() and p.stat().st_size>2200:continue
    a,sr=engine.create(pat.sub(lambda m:lookup[m.group()],en),voice='bf_emma',speed=.9,lang='en-gb');idx=np.flatnonzero(np.abs(a)>.003);assert len(idx)>100,en
    a=a[max(0,idx[0]-int(.08*sr)):min(len(a),idx[-1]+int(.18*sr))];assert .3<len(a)/sr<25,en
    a=a*min(1.4,.82/max(.001,float(np.max(np.abs(a)))));tmp=p.with_suffix('.tmp.mp3')
    subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-y','-f','s16le','-ar',str(sr),'-ac','1','-i','pipe:0','-c:a','libmp3lame','-b:a','64k','-ar','24000',str(tmp)],input=(np.clip(a,-1,1)*32767).astype('<i2').tobytes(),check=True);assert tmp.stat().st_size>2200,en;tmp.replace(p)
    if i%25==0:print(shard,i,'/',len(items),flush=True)
print('Complete shard',shard,len(items),flush=True)
