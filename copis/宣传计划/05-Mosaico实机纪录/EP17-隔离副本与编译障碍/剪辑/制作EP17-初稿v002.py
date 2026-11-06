#!/usr/bin/env python3
"""EP17 内部初稿：字幕临时，画面隐私/口播/用户听感尚未验收，禁止发布。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import subprocess
P=Path(__file__).resolve().parent; R=P.parent
OUT=P/'EP17-初稿-v002-待验收.mp4'
if OUT.exists(): raise SystemExit('初稿已存在，拒绝覆盖')
ass=P/'字幕EP17-初稿v002.ass'
if ass.exists(): raise SystemExit('字幕已存在，拒绝覆盖')
T=26.0
header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Cap,Hiragino Sans GB,50,&H00FFFFFF,&H00FFFFFF,&H00101B22,&H00101B22,1,0,0,0,100,100,0,0,1,2.2,1.2,8,40,40,0,1
Style: Badge,Hiragino Sans GB,40,&H0064C8FA,&H0064C8FA,&H00101B22,&H00101B22,1,0,0,0,100,100,0,0,1,1.2,0,8,40,40,0,1
Style: T1,Hiragino Sans GB,74,&H00F8FFF8,&H00F8FFF8,&H00101B22,&H00101B22,1,0,0,0,100,100,2,0,1,2,1.5,8,40,40,0,1
Style: T2,Hiragino Sans GB,80,&H0064C8FA,&H0064C8FA,&H00101B22,&H00101B22,1,0,0,0,100,100,2,0,1,2,1.5,8,40,40,0,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
'''
rows=[header,
r'Dialogue: 0,0:00:00.00,0:00:26.00,Badge,,0,0,0,,{\pos(540,25)}── 织界探索日记 · EP17 ──',
r'Dialogue: 0,0:00:00.00,0:00:26.00,T1,,0,0,0,,{\pos(540,95)}先不装',
r'Dialogue: 0,0:00:00.00,0:00:26.00,T2,,0,0,0,,{\pos(540,174)}能在电脑里做什么？',
# 以下暂定区间，仅供观看初稿；尚未实际听检，不作为口播同步或锁版证据。
r'Dialogue: 0,0:00:00.50,0:00:06.09,Cap,,0,0,0,,{\pos(540,1580)}上次发现现场布局不同\N备份还没完成，所以先不安装',
r'Dialogue: 0,0:00:06.09,0:00:08.70,Cap,,0,0,0,,{\pos(540,1580)}这一轮，先在电脑里准备',
r'Dialogue: 0,0:00:08.70,0:00:12.60,Cap,,0,0,0,,{\pos(540,1580)}我们在独立副本里\N按现场布局做适配',
r'Dialogue: 0,0:00:12.60,0:00:15.47,Cap,,0,0,0,,{\pos(540,1580)}并准备关闭挂载失败后的\N自动格式化和部分覆盖路径',
r'Dialogue: 0,0:00:15.47,0:00:16.63,Cap,,0,0,0,,{\pos(540,1580)}{\c&H64C8FA&}五十八项电脑端测试通过',
r'Dialogue: 0,0:00:16.63,0:00:20.10,Cap,,0,0,0,,{\pos(540,1580)}但配置时，依赖管理器\N尝试联网获取',
r'Dialogue: 0,0:00:20.10,0:00:23.02,Cap,,0,0,0,,{\pos(540,1580)}在禁网的构建环境里失败了',
r'Dialogue: 0,0:00:23.02,0:00:25.40,Cap,,0,0,0,,{\pos(540,1580)}这一轮没有生成最终固件\N设备上的效果也还没验证']
ass.write_text('\n'.join(rows)+'\n',encoding='utf-8')
# 与源图对应；两段均避开 12–20 秒的不稳定滚动区，第二段源 22 秒以后为失败终态，不冒充滚动。
# 源图尺寸 1452x1058；box 在裁切/缩放之前覆盖，仅供候选，未完成隐私审查。
boxes=[(60,70,1325,58),(190,125,1195,34),(160,192,900,28),(75,280,800,52),(75,458,1310,31),(68,592,1320,64),(65,683,1322,110),(60,952,230,30)]
maskboxes=','.join(f'drawbox=x={x}:y={y}:w={w}:h={h}:color=0x101713:t=fill' for x,y,w,h in boxes)
tab='drawbox=x=60:y=952:w=230:h=30:color=0x101713:t=fill'
inputs=[R/'素材/224/Otty.mp4',R/'素材/224/MAC-camera-preview.mp4',P/'试听配音-EP17-v001.wav',P/'bgm-v1.wav',P.parents[1]/'EP12-新固件做出来了/剪辑/底部装饰-v009.png']
cmd=['ffmpeg','-nostdin','-v','error']
for x in inputs[:4]: cmd+=['-i',str(x)]
cmd+=['-loop','1','-framerate','30','-i',str(inputs[4])]
# 每幕半透明聚焦蒙层，仅压暗非重点区域；不承担隐私遮挡。
for j,(top,bottom) in enumerate([(550,760),(80,300)]):
 mpath=P/f'EP17-聚焦遮罩-v002-{j}.png'
 if mpath.exists(): raise SystemExit('聚焦遮罩已存在，拒绝覆盖')
 alpha=Image.new('L',(1080,800),170); ImageDraw.Draw(alpha).rectangle((0,top,1079,bottom),fill=0); alpha=alpha.filter(ImageFilter.GaussianBlur(30))
 mask=Image.new('RGBA',(1080,800),(0,0,0,0)); mask.putalpha(alpha); mask.save(mpath)
 cmd+=['-loop','1','-framerate','30','-i',str(mpath)]
# 必须执行关键行聚焦的正常→推入→保持→退出；原源保持清晰、不做整体模糊。
f=[]
segments=[(5,17,False,650),(22,9,True,70)]
for j,(start,dur,private,yfocus) in enumerate(segments):
 vtrim=(f'trim=start={start}:duration=6,setpts=PTS-STARTPTS,fps=30,loop=loop=2:size=180:start=0,trim=duration={dur},setpts=PTS-STARTPTS' if j==0 else f'trim=start={start}:duration={dur},setpts=PTS-STARTPTS')
 f.append(f'[0:v]{vtrim},{maskboxes if private else tab},crop=1428:1058:12:0,scale=2160:1600,fps=30,setsar=1[t{j}]')
 # 轻推到 1.16，保持后退出；yfocus 为超采样锚点，首帧正常。时间以 30fps 表达。
 z="if(lt(on,30),1,if(lt(on,54),1+0.16*(on-30)/24,if(lt(on,%d),1.16,if(lt(on,%d),1.16-0.16*(on-%d)/24,1))))"%(dur*30-48,dur*30-24,dur*30-48)
 f.append(f"[t{j}]zoompan=z='{z}':x='0':y='min(ih-ih/zoom,{yfocus})':d=1:s=1080x800:fps=30,setsar=1[zoom{j}]")
 f.append(f'[{5+j}:v]trim=duration={dur},setpts=PTS-STARTPTS,format=rgba,fade=t=in:st=1:d=0.8:alpha=1,fade=t=out:st={dur-1.6}:d=0.8:alpha=1[shade{j}]')
 f.append(f'[zoom{j}][shade{j}]overlay=0:0:shortest=1[term{j}]')
 f.append(f'[1:v]trim=start={start}:duration={dur},setpts=PTS-STARTPTS,crop=650:366:395:155,scale=1080:608,fps=30,setsar=1[cam{j}]')
f+=['[term0][term1]concat=n=2:v=1:a=0[screen]','[cam0][cam1]concat=n=2:v=1:a=0[camera]',f'color=c=0x283840:s=1080x1920:r=30:d={T}[base]','[base][camera]overlay=0:280[b1]','[b1][screen]overlay=0:888[b2]',f"[b2][4:v]overlay=0:1688,drawbox=x=0:y=0:w=1080:h=280:color=0x0a1014@0.88:t=fill,ass='{ass.name}'[v]",'[2:a]adelay=500|500,volume=1.15,aresample=44100[voice]',f'[3:a]aresample=44100,atrim=0:{T},volume=0.8,afade=t=out:st={T-2}:d=2[bgm]','[voice][bgm]amix=inputs=2:duration=longest:normalize=0,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.80:level=disabled[a]']
cmd+=['-filter_complex',';'.join(f),'-map','[v]','-map','[a]','-t',str(T),'-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(OUT)]
subprocess.run(cmd,cwd=P,check=True)
print('内部初稿已导出；字幕未听检，隐私未验收。')
