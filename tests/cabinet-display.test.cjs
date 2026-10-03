const {test}=require('node:test');
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(require('node:path').join(__dirname,'../cabinets.js'),'utf8');
test('cabinet crop stays inside portrait, landscape and square photos at all control extremes',()=>{
 const context=vm.createContext({});vm.runInContext(source.slice(source.indexOf('function cabinetCropRect('),source.indexOf('function drawCabinetCrop(')),context);
 for(const [w,h] of [[1200,3000],[3000,1200],[2000,2000]])for(const zoom of [1,2,4])for(const x of [0,50,100])for(const y of [0,50,100]){
 const r=context.cabinetCropRect(w,h,zoom,x,y);assert.ok(r.x>=0&&r.y>=0&&r.x+r.w<=w+1e-8&&r.y+r.h<=h+1e-8);assert.equal(r.w/r.h,1.25);
 }
});
test('score polling retains cabinet DOM; changed photo, assignments and featured game rerender',()=>{
 let replacements=0;
 const element=()=>({dataset:{},style:{setProperty(){}},classList:{toggle(){}},append(){},setAttribute(){}});
 const target=element();target.replaceChildren=()=>replacements++;
 const context=vm.createContext({$:()=>target,node:element,cabinetButton:element,cabinetImage:element,cabinetPicture:c=>c.photoId||c.code,window:{},openWhereToPlay(){}});
 vm.runInContext(source.slice(source.indexOf('function renderFeaturedCabinets('),source.indexOf('function openWhereToPlay(')),context);
 const game={id:'galaga',title:'Galaga',cabinets:[{id:'pac',name:'Pac-Man',code:'PAC',photoId:'one'}]};
 context.renderFeaturedCabinets(game);assert.equal(replacements,1);
 context.renderFeaturedCabinets(JSON.parse(JSON.stringify(game)));assert.equal(replacements,1);
 game.record={score:123};context.renderFeaturedCabinets(game);assert.equal(replacements,1);
 game.cabinets[0].photoId='two';context.renderFeaturedCabinets(game);assert.equal(replacements,2);
 game.id='pacman';context.renderFeaturedCabinets(game);assert.equal(replacements,3);
 game.cabinets=[];context.renderFeaturedCabinets(game);assert.equal(replacements,4);
 context.renderFeaturedCabinets(game);assert.equal(replacements,4);
});
