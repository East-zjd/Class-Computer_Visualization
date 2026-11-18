const $=id=>document.getElementById(id), num=x=>Number(x).toLocaleString('zh-CN',{maximumFractionDigits:0}), money=x=>'¥'+num(x), pct=x=>(x*100).toFixed(2)+'%';
const categories=[...new Set(DATA.map(r=>r.Category))],channels=[...new Set(DATA.map(r=>r.Channel))];
for(const [id,items,label] of [['category',categories,'全部品类'],['channel',channels,'全部渠道']]){ $(id).add(new Option(label,''));items.forEach(x=>$(id).add(new Option(x,x)));}
function agg(rows){const n=rows.length;const sum=k=>rows.reduce((s,r)=>s+Number(r[k]),0);let g=sum('GMV'),a=sum('Ad_Spend');return {n,g,a,roas:a?g/a:0,c:n?sum('Conversion_Rate')/n:0,b:n?sum('Bounce_Rate')/n:0};}
function groups(rows,key){return [...new Set(rows.map(r=>r[key]))].map(name=>({name,...agg(rows.filter(r=>r[key]===name))}));}
let current=[],summary={},history=[];
function reset(){ $('start').value='2026-09-01';$('end').value='2026-09-30';$('category').value='';$('channel').value='';render();}
function render(){
 current=DATA.filter(r=>r.Date>=$('start').value&&r.Date<=$('end').value&&(!$('category').value||r.Category===$('category').value)&&(!$('channel').value||r.Channel===$('channel').value));summary=agg(current);
 $('count').textContent=current.length+' 条记录';
 $('kpis').innerHTML=[['成交总额 · GMV',money(summary.g),'当前筛选范围累计'],['广告花费',money(summary.a),'当前筛选范围累计'],['投放产出 · ROAS',summary.roas.toFixed(2)+'×','GMV / 广告花费'],['平均转化率',pct(summary.c),'记录算术均值'],['平均跳出率',pct(summary.b),'记录算术均值']].map(([l,v,n])=>`<div class="card kpi"><span class="muted">${l}</span><strong>${current.length?v:'—'}</strong><small>${n}</small></div>`).join('');
 trend();bars('categories',groups(current,'Category'),'g',money,'category');bars('channels',groups(current,'Channel'),'roas',x=>x.toFixed(2)+'×','channel');
 const pairs=[...new Set(current.map(r=>r.Category+' / '+r.Channel))].map(name=>({name,...agg(current.filter(r=>r.Category+' / '+r.Channel===name))})).sort((a,b)=>b.g-a.g);
 $('details').innerHTML=pairs.map(r=>`<tr><td>${r.name}</td><td>${money(r.g)}</td><td>${money(r.a)}</td><td class="badge">${r.roas.toFixed(2)}×</td><td>${pct(r.c)}</td><td>${pct(r.b)}</td></tr>`).join('')||'<tr><td colspan="6" class="empty">该范围没有数据，请调整筛选。</td></tr>';
 const best=groups(current,'Channel').sort((a,b)=>b.roas-a.roas)[0];$('insight').textContent=best?`经营快讯 · ${best.name} ROAS 为 ${best.roas.toFixed(2)}×，在当前渠道中最高。当前 GMV ${money(summary.g)}。`:'该范围暂无数据。';
}
function bars(id,rows,key,format,filter){rows.sort((a,b)=>b[key]-a[key]);const max=Math.max(...rows.map(r=>r[key]),1);$(id).innerHTML='';for(const r of rows){let el=document.createElement('button');el.className='barrow';el.style='background:none;border:0;padding:0;text-align:left';el.innerHTML=`<div class="barlabel"><span>${r.name}</span><span>${format(r[key])}</span></div><div class="track"><div class="fill" style="width:${100*r[key]/max}%"></div></div>`;el.onclick=()=>{$(filter).value=r.name;render();};$(id).append(el);}}
function trend(){
 const dates=[...new Set(current.map(r=>r.Date))].sort(),rows=dates.map(d=>agg(current.filter(r=>r.Date===d)));
 if(!rows.length){$('trend').innerHTML='<div class="empty">该范围暂无数据</div>';return;}
 const w=900,h=240,left=65,right=20,top=18,bottom=35,max=Math.max(...rows.map(r=>r.g),1)*1.1,x=i=>left+(w-left-right)*i/Math.max(rows.length-1,1),y=v=>h-bottom-(h-top-bottom)*v/max;
 let s=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="每日GMV和广告花费折线图">`;
 for(let i=0;i<=4;i++){let v=max*i/4;s+=`<line x1="${left}" y1="${y(v)}" x2="${w-right}" y2="${y(v)}" stroke="#24324a"/><text x="${left-9}" y="${y(v)+4}" text-anchor="end">${(v/10000).toFixed(1)}万</text>`;}
 for(const [key,color] of [['g','#49dec6'],['a','#6b9cff']]){s+=`<polyline fill="none" stroke="${color}" stroke-width="2.5" points="${rows.map((r,i)=>x(i)+','+y(r[key])).join(' ')}"/>`;rows.forEach((r,i)=>s+=`<circle cx="${x(i)}" cy="${y(r[key])}" r="3" fill="${color}"><title>${dates[i]} ${key==='g'?'GMV':'广告花费'}：${money(r[key])}</title></circle>`);}
 dates.forEach((d,i)=>{if(i%Math.max(1,Math.ceil(dates.length/7))===0||i===dates.length-1)s+=`<text x="${x(i)}" y="${h-10}" text-anchor="middle">${d.slice(5)}</text>`;});$('trend').innerHTML=s+'</svg>';
}
function localAnswer(q){
 if(/重置|全部数据|所有数据/.test(q))reset();
 else{let changed=false;for(const [id,items] of [['category',categories],['channel',channels]]){const found=items.find(x=>q.toLowerCase().includes(x.toLowerCase()));if(found){$(id).value=found;changed=true;}}if(changed)render();}
 if(!current.length)return '当前筛选没有数据，请调整日期或重置筛选。';
 const s=summary, cs=groups(current,'Channel').sort((a,b)=>b.roas-a.roas),cats=groups(current,'Category').sort((a,b)=>b.g-a.g);let scope=`范围：${$('start').value} 至 ${$('end').value}，${$('category').value||'全部品类'} / ${$('channel').value||'全部渠道'}，${s.n} 条记录。\n\n`;
 if(/异常|下降|波动|风险|为什么/.test(q)){
  const ds=groups(current,'Date').sort((a,b)=>a.name.localeCompare(b.name));const changes=ds.slice(1).map((r,i)=>({...r,change:ds[i].g?(r.g/ds[i].g-1):0})).sort((a,b)=>a.change-b.change);const worst=changes[0];
  return scope+(worst?`最大日环比下降发生在 ${worst.name}，GMV ${money(worst.g)}，较上一有数据日期变化 ${pct(worst.change)}。\n\n`:'当前仅一天数据，无法计算日环比。\n\n')+`当前跳出率均值 ${pct(s.b)}，转化率均值 ${pct(s.c)}。\n建议按品类、渠道交叉核查流量结构、投放活动与落地页变化。日环比是描述性信号，尚不能确定变化原因。`;
 }
 if(/优化|建议|预算|投放/.test(q))return scope+`效率排序：\n${cs.map((r,i)=>`${i+1}. ${r.name}：ROAS ${r.roas.toFixed(2)}×，广告花费 ${money(r.a)}`).join('\n')}\n\n建议：优先检查 ${cs.at(-1).name} 的品类结构及素材表现；可对 ${cs[0].name} 做小规模预算测试。测试前设定预算上限、观察周期与停止条件。当前数据无法证明追加预算仍有相同回报，也不能评估利润。`;
 if(/渠道|效率|ROAS/i.test(q))return scope+cs.map((r,i)=>`${i+1}. ${r.name}：ROAS ${r.roas.toFixed(2)}×；GMV ${money(r.g)}；广告花费 ${money(r.a)}；转化率均值 ${pct(r.c)}。`).join('\n')+`\n\n${cs[0].name} 在当前范围的投放产出最高。ROAS 未扣除商品成本、履约费及退款。`;
 if(/品类|贡献|销售|最高/.test(q))return scope+cats.map((r,i)=>`${i+1}. ${r.name}：GMV ${money(r.g)}，占比 ${pct(r.g/s.g)}，ROAS ${r.roas.toFixed(2)}×。`).join('\n');
 if(!/总结|表现|概览|转化|跳出|GMV|成交|分析|只看|筛选|重置|全部/i.test(q))return scope+'本地模式支持经营总结、渠道效率、品类贡献、日环比波动和投放建议，也可输入品类/渠道名称联动筛选。开放式问题请切换“大模型”模式并配置 API。';
 return scope+`GMV ${money(s.g)}，广告花费 ${money(s.a)}，ROAS ${s.roas.toFixed(2)}×。\n转化率均值 ${pct(s.c)}，跳出率均值 ${pct(s.b)}。\n\n贡献最高品类：${cats[0].name}（${money(cats[0].g)}，占 ${pct(cats[0].g/s.g)}）。\n效率最高渠道：${cs[0].name}（${cs[0].roas.toFixed(2)}×）。\n\n建议结合渠道与品类明细核查预算分配。当前缺少访客、订单及利润字段，无法计算整体加权转化率或利润。`;
}
function message(text,role='assistant'){const el=document.createElement('div');el.className='msg '+role;const label=document.createElement('small');label.textContent=role==='user'?'你':'✦ '+($('mode').value==='ai'?'大模型助手':'本地数据分析');el.append(label,document.createTextNode(text));$('messages').append(el);$('messages').scrollTop=$('messages').scrollHeight;}
async function ask(q){message(q,'user');$('send').disabled=true;try{if($('mode').value==='local'){message(localAnswer(q));}else{const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,history:history.slice(-6),scope:{start:$('start').value,end:$('end').value,category:$('category').value,channel:$('channel').value},summary,byChannel:groups(current,'Channel'),byCategory:groups(current,'Category'),daily:groups(current,'Date'),metricDefinitions:'g=GMV,a=广告花费,roas=GMV/广告花费,c=转化率记录均值,b=跳出率记录均值,n=记录数'})});const raw=await response.text();const ctype=response.headers.get('content-type')||'(无)';let data=null;try{data=JSON.parse(raw)}catch(e2){}if(!data){console.error('[chat] 非 JSON 响应',response.status,ctype,raw.slice(0,300));throw Error('服务端返回了非 JSON 内容（HTTP '+response.status+'，Content-Type '+ctype+'）：'+raw.replace(/\s+/g,' ').trim().slice(0,120)+'\n\n这段文字不是本服务写的。请确认页面是用 node server.mjs 打开的 http://127.0.0.1:8000，而不是编辑器内置预览或别的静态服务器。')}if(!response.ok)throw Error(data.error);message(data.answer);history.push({question:q,answer:data.answer});}}catch(e){message(e.message||'请求失败，请使用本地分析，或通过 node server.mjs 启动服务。');}finally{$('send').disabled=false;}}
for(const id of ['start','end','category','channel'])$(id).addEventListener('change',render);
$('reset').onclick=reset;$('form').onsubmit=e=>{e.preventDefault();const q=$('question').value.trim();if(q){$('question').value='';ask(q);}};document.querySelectorAll('.suggestions button').forEach(b=>b.onclick=()=>{if(!$('send').disabled)ask(b.textContent);});
$('export').onclick=()=>{const keys=['Date','Category','Channel','Ad_Spend','GMV','Conversion_Rate','Bounce_Rate'];const csv='\uFEFF'+[keys.join(','),...current.map(r=>keys.map(k=>r[k]).join(','))].join('\r\n');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='dashboard-filtered.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};render();
