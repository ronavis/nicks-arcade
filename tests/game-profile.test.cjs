const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(require('node:path').join(__dirname,'../cabinets.js'),'utf8');
const context=vm.createContext({});
vm.runInContext(source.slice(source.indexOf('function currentRecordInHistory(')),context);
test('public profile removes only an exact unchanged duplicate of the current record',()=>{
 const check=context.currentRecordInHistory,current={id:'a',score:'100',initials:'RON'};
 assert.equal(check(current,[{...current}]),true);
 assert.equal(check(current,[{...current,corrected:true}]),false);
 assert.equal(check(current,[{...current,score:'90'}]),false);
 assert.equal(check(current,[]),false);
 assert.equal(check(null,[]),false);
});
