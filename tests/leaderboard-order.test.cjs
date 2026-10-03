const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(require('node:path').join(__dirname,'../app.js'),'utf8');
const context=vm.createContext({});
vm.runInContext(source.slice(source.indexOf('function sortLeaderboard('),source.indexOf('async function fetchBoard()')),context);
const games=[{id:'z',title:'Zaxxon',record:{createdAt:200}},{id:'b',title:'BurgerTime',record:{createdAt:0}},{id:'a',title:'Asteroids',record:{createdAt:100}},{id:'c',title:'Centipede',record:null},{id:'d',title:'Dig Dug',record:{createdAt:200}}];
test('alphabetical and newest orders are stable, preserve records and place undated games last',()=>{
 const ids=list=>Array.from(list,g=>g.id);
 assert.deepEqual(ids(context.sortLeaderboard(games)),['a','b','c','d','z']);
 assert.deepEqual(ids(context.sortLeaderboard(games,'newest')),['d','z','a','b','c']);
 assert.deepEqual(ids(games),['z','b','a','c','d']);
 assert.deepEqual(ids(context.sortLeaderboard(context.sortLeaderboard(games,'newest'),'newest')),['d','z','a','b','c']);
});
