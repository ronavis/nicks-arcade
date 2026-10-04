const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(require('node:path').join(__dirname,'../app.js'),'utf8');
const context=vm.createContext({});
vm.runInContext(source.slice(source.indexOf('function historyEntryLabel('),source.indexOf('function renderRecordHistory(')),context);
test('timeline status distinguishes current, original imported, corrected and removed records',()=>{
 const label=context.historyEntryLabel;
 assert.equal(label({id:'a'},'a'),'Current record');
 assert.equal(label({id:'a',corrected:true},'a'),'Current record · corrected');
 assert.equal(label({id:'a',deleted:true},'a'),'Removed record');
 assert.equal(label({id:'b',imported:true},'a'),'Imported starting record');
 assert.equal(label({id:'b',corrected:true},'a'),'Previous record');
});
