const {test} = require('node:test');
const assert = require('node:assert/strict');
const {createObserver} = require('../record-celebrations.js');
const game = (id,score,extra={}) => ({id:'galaga',kind:'score',record:{id,score,initials:'RON',createdAt:100,revision:1,...extra}});
const snapshot = (g,time=100) => ({games:[g],updatedAt:time});
test('initial load and repeated polling never replay records',()=>{const o=createObserver();assert.deepEqual(o(snapshot(game('a','100'))),[]);assert.deepEqual(o(snapshot(game('a','100'),101)),[])});
test('new higher record celebrates once and keeps taunt',()=>{const o=createObserver();o(snapshot(game('a','100')));const g=game('b','200',{createdAt:101,taunt:'Your turn!'});assert.equal(o(snapshot(g,102))[0].record.taunt,'Your turn!');assert.equal(o(snapshot(g,103)).length,0)});
test('lower time wins, higher time does not',()=>{const o=createObserver();o(snapshot({...game('a','1:02.30'),kind:'time'}));assert.equal(o(snapshot({...game('b','1:01.20',{createdAt:101}),kind:'time'},101)).length,1);assert.equal(o(snapshot({...game('c','1:03.00',{createdAt:102}),kind:'time'},102)).length,0)});
test('admin correction, old fallback, tie and removed winner do not celebrate',()=>{for(const g of [game('b','200',{revision:2}),game('b','200',{createdAt:50}),game('b','100'),{id:'galaga',record:null}]){const o=createObserver();o(snapshot(game('a','100')));assert.equal(o(snapshot(g,101)).length,0)}});
test('first record after baseline celebrates',()=>{const o=createObserver();o(snapshot({id:'galaga',record:null}));assert.equal(o(snapshot(game('a','100'),101)).length,1)});
test('reconnection does not celebrate stale wins',()=>{const o=createObserver();o(snapshot(game('a','100')));assert.equal(o(snapshot(game('b','200',{createdAt:101}),200)).length,0)});
test('numeric comparison handles commas',()=>{const o=createObserver();o(snapshot(game('a','900')));assert.equal(o(snapshot(game('b','1,000'),101)).length,1)});
const {recordAge} = require('../record-celebrations.js');
test('record dates distinguish missing dates, today, elapsed days and corrections',()=>{
 assert.equal(recordAge(null),'No score posted yet');
 assert.equal(recordAge({createdAt:null}),'');
 assert.match(recordAge({createdAt:100,revision:1},100000),/^Set today/);
 assert.match(recordAge({createdAt:100,revision:1},100000+86400000),/^Set 1 day ago/);
 assert.match(recordAge({createdAt:100,revision:1},100000+3*86400000),/^Set 3 days ago/);
 assert.match(recordAge({createdAt:100,revision:2},100000),/^Submitted .*corrected$/);
});

test('record ages advance at midnight across time zones and daylight-saving changes',()=>{
 const {execFileSync}=require('node:child_process');
 for(const timezone of ['America/New_York','America/Los_Angeles','UTC']) {
  execFileSync(process.execPath,['-e',`
   const assert=require('node:assert/strict');
   const {recordAge}=require('./record-celebrations.js');
   const age=(created,now)=>recordAge({createdAt:created.getTime()/1000,revision:1},now.getTime());
   assert.match(age(new Date(2026,8,29,23,45),new Date(2026,9,1,0,5)),/^Set 2 days ago/);
   assert.match(age(new Date(2026,8,29,23,59),new Date(2026,8,30,0,0)),/^Set 1 day ago/);
   assert.match(age(new Date(2026,2,7,23,30),new Date(2026,2,9,0,5)),/^Set 2 days ago/);
   assert.match(age(new Date(2026,10,1,0,5),new Date(2026,10,1,23,55)),/^Set today/);
   assert.equal(recordAge({createdAt:'invalid'}),'');
  `],{cwd:require('node:path').resolve(__dirname,'..'),env:{...process.env,TZ:timezone}});
 }
});
test('open scoreboard refreshes age on its own timer and on resume without a network request',()=>{
 const vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
 const source=fs.readFileSync(path.join(__dirname,'../app.js'),'utf8');
 const code=source.slice(source.indexOf('function refreshRecordAge()'),source.indexOf('function feature(id)'));
 let now=new Date(2026,8,29,23,59).getTime(),tick,period;
 const label={textContent:''},events={};
 const record={createdAt:now/1000,revision:1};
 const state={boardGames:[{id:'test',record}],featured:'test',paused:true,connected:false};
 vm.runInNewContext(code,{
  state,$:()=>label,ArcadeCelebrations:{recordAge:r=>recordAge(r,now)},
  setInterval:(fn,ms)=>{tick=fn;period=ms},
  window:{addEventListener:(name,fn)=>events[name]=fn},
  document:{hidden:false,addEventListener:(name,fn)=>events[name]=fn}
 });
 assert.equal(period,30000);tick();assert.match(label.textContent,/^Set today/);
 now=new Date(2026,8,30,0,0).getTime();tick();assert.match(label.textContent,/^Set 1 day ago/);
 now=new Date(2026,9,1,0,0).getTime();events.visibilitychange();assert.match(label.textContent,/^Set 2 days ago/);
 state.boardGames=[];events.pageshow();assert.equal(label.textContent,'');
});
