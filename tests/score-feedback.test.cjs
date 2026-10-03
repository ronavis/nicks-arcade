const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const line=fs.readFileSync(path.join(__dirname,'../app.js'),'utf8').split('\n').find(line=>line.includes("$('success-detail').textContent ="));
test('submission feedback distinguishes hidden records, visible records and non-record scores',()=>{
 const message=result=>{const label={};vm.runInNewContext(line,{$:()=>label,result:{record:{initials:'RON',score:'2,585'},...result},state:{selected:'game'},gameById:()=>({title:'Test game',showOnLeaderboard:1})});return label.textContent;};
 assert.match(message({isRecord:true,game:{showOnLeaderboard:0}}),/record is saved.*hidden.*Show on leaderboard/);
 assert.match(message({isRecord:true,game:{showOnLeaderboard:1}}),/record is on the board/);
 assert.match(message({isRecord:false,game:{showOnLeaderboard:0}}),/saved in the game’s history/);
});
