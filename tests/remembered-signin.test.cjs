const {test}=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const source=fs.readFileSync(require('node:path').join(__dirname,'../app.js'),'utf8');
function fixture(remember=true){
 const storage=()=>{const values=new Map();return{setItem:(k,v)=>values.set(k,v),getItem:k=>values.get(k)||null,removeItem:k=>values.delete(k)}};
 const calls=[],elements=new Map();const user={admin:true,email:'test@example.com'};
 const context=vm.createContext({state:{config:{demo:false},initials:'RON'},location:{hash:'#play'},localStorage:storage(),sessionStorage:storage(),window:{},$:id=>{if(!elements.has(id))elements.set(id,{checked:remember,close(){},replaceChildren(){},setAttribute(){}});return elements.get(id)},api:async(path,options)=>{calls.push([path,options]);return options?.method==='POST'?{token:'arcade_test',user}:user},renderSession(){},setMessage(){},refreshAccount:async()=>{},applySavedTaunt(){},route(){}});
 vm.runInContext(source.slice(source.indexOf('async function signIn('),source.indexOf('function loadGoogle(')),context);return{context,calls};
}
test('remembered login persists app token, keeps score entry, restores without exchanging Google again',async()=>{
 const {context:c,calls}=fixture();await c.signIn('google');assert.equal(c.localStorage.getItem('arcade_session'),'arcade_test');assert.equal(c.sessionStorage.getItem('arcade_session'),null);assert.equal(c.location.hash,'#play');
 calls.length=0;await c.signIn('arcade_test',{restore:true,goToBoard:false});assert.equal(calls[0][1],undefined);assert.equal(calls.length,1);
 await c.signOut();assert.equal(calls.at(-1)[1].method,'DELETE');assert.equal(c.localStorage.getItem('arcade_session'),null);assert.equal(c.state.user,null);
});
test('unchecked remember uses tab storage; failed server logout retains session for retry',async()=>{
 const {context:c}=fixture(false);await c.signIn('google');assert.equal(c.localStorage.getItem('arcade_session'),null);assert.equal(c.sessionStorage.getItem('arcade_session'),'arcade_test');
 c.api=async()=>{throw new Error('offline')};await c.signOut();assert.equal(c.state.token,'arcade_test');assert.equal(c.sessionStorage.getItem('arcade_session'),'arcade_test');
});
