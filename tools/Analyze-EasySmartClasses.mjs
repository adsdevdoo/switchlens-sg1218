#!/usr/bin/env node
// Static parser only: reads exported class bytes as data. No eval of class code,
// no Java/EXE execution, no network. Optional third input verifies the stock BIN.
import fs from "node:fs";
import path from "node:path";

function b64decode(s) {
 const alpha="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
 const out=[]; let acc=0,bits=0;
 for(const c of s){if(c==="=")break; const n=alpha.indexOf(c); if(n<0){if(/\s/.test(c))continue;throw Error("bad base64");} acc=(acc<<6)|n;bits+=6;if(bits>=8){bits-=8;out.push((acc>>>bits)&255);}}
 return out;
}
function sha256(input){
 const K=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
 const H=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
 const a=input.slice();const length=a.length; a.push(128);while(a.length%64!==56)a.push(0);
 const hi=Math.floor(length/0x20000000),lo=(length*8)>>>0;
 for(const v of [hi,lo])for(let s=24;s>=0;s-=8)a.push(v>>>s&255);
 const rr=(v,n)=>(v>>>n)|(v<<(32-n));
 for(let o=0;o<a.length;o+=64){const w=[];
 for(let t=0;t<16;t++)w[t]=((a[o+t*4]<<24)|(a[o+t*4+1]<<16)|(a[o+t*4+2]<<8)|a[o+t*4+3])>>>0;
 for(let t=16;t<64;t++){const x=w[t-15],y=w[t-2];w[t]=(w[t-16]+(rr(x,7)^rr(x,18)^(x>>>3))+w[t-7]+(rr(y,17)^rr(y,19)^(y>>>10)))>>>0;}
 let [b,c,d,e,f,g,h,i]=H;
 for(let t=0;t<64;t++){const t1=(i+(rr(f,6)^rr(f,11)^rr(f,25))+((f&g)^(~f&h))+K[t]+w[t])>>>0;const t2=((rr(b,2)^rr(b,13)^rr(b,22))+((b&c)^(b&d)^(c&d)))>>>0;i=h;h=g;g=f;f=(e+t1)>>>0;e=d;d=c;c=b;b=(t1+t2)>>>0;}
 [b,c,d,e,f,g,h,i].forEach((v,k)=>H[k]=(H[k]+v)>>>0);
 }
 return H.map(x=>x.toString(16).padStart(8,"0")).join("");
}
class Reader {
 constructor(a){this.a=a;this.p=0;}
 u1(){if(this.p>=this.a.length)throw Error("EOF");return this.a[this.p++];}
 u2(){return this.u1()*256+this.u1();}
 u4(){return (this.u2()*65536+this.u2())>>>0;}
 take(n){if(n<0||this.p+n>this.a.length)throw Error("EOF slice");const x=this.a.slice(this.p,this.p+n);this.p+=n;return x;}
}
function mutf8(a){let s="";for(let i=0;i<a.length;){let c=a[i++];if(c<128)s+=String.fromCharCode(c);else if((c&224)===192)s+=String.fromCharCode(((c&31)<<6)|(a[i++]&63));else if((c&240)===224){s+=String.fromCharCode(((c&15)<<12)|((a[i++]&63)<<6)|(a[i++]&63));}else throw Error("bad MUTF8");}return s;}
function parseClass(bytes){
 const r=new Reader(bytes);if(r.u4()!==0xcafebabe)throw Error("magic");
 const minor=r.u2(),major=r.u2(),count=r.u2(),cp=[null];
 for(let i=1;i<count;i++){const tag=r.u1();let v={tag};
 if(tag===1)v.value=mutf8(r.take(r.u2()));
 else if(tag===3)v.value=r.u4()|0;
 else if(tag===4)v.bits=r.u4();
 else if(tag===5||tag===6){v.hi=r.u4();v.lo=r.u4();cp[i]=v;cp[++i]=null;continue;}
 else if([7,8,16,19,20].includes(tag))v.a=r.u2();
 else if([9,10,11,12,17,18].includes(tag)){v.a=r.u2();v.b=r.u2();}
 else if(tag===15){v.a=r.u1();v.b=r.u2();}else throw Error("cp tag "+tag);
 cp[i]=v;
 }
 const utf=n=>cp[n]?.value;
 function attrs(){const list=[];for(let n=r.u2();n>0;n--){const name=utf(r.u2()),len=r.u4();list.push({name,data:r.take(len)});}return list;}
 function members(){const list=[];for(let n=r.u2();n>0;n--){const flags=r.u2(),name=utf(r.u2()),descriptor=utf(r.u2()),at=attrs();let code=null;
 const ca=at.find(x=>x.name==="Code");if(ca){const cr=new Reader(ca.data);const maxStack=cr.u2(),maxLocals=cr.u2(),len=cr.u4(),bc=cr.take(len),exceptions=[];for(let k=cr.u2();k>0;k--)exceptions.push({start:cr.u2(),end:cr.u2(),handler:cr.u2(),type:cr.u2()});const sub=[];for(let k=cr.u2();k>0;k--){const nm=utf(cr.u2()),sz=cr.u4();sub.push({name:nm,data:cr.take(sz)});}if(cr.p!==ca.data.length)throw Error("code trailing");code={maxStack,maxLocals,bytes:bc,exceptions,attributes:sub};}
 list.push({flags,name,descriptor,attributes:at.filter(x=>x.name!=="Code"),code});}return list;}
 const flags=r.u2(),thisClass=r.u2(),superClass=r.u2(),interfaces=[];for(let n=r.u2();n>0;n--)interfaces.push(r.u2());
 const fields=members(),methods=members(),attributes=attrs();if(r.p!==bytes.length)throw Error("class trailing");
 return {major,minor,flags,name:utf(cp[thisClass].a),superName:superClass?utf(cp[superClass].a):null,cp,interfaces,fields,methods,attributes};
}
function cpText(c,n,depth=0){if(depth>8)return "#"+n;const p=c.cp[n];if(!p)return "#"+n;if([1,3].includes(p.tag))return String(p.value);if([7,8,16].includes(p.tag))return cpText(c,p.a,depth+1);if(p.tag===12)return cpText(c,p.a,depth+1)+":"+cpText(c,p.b,depth+1);if([9,10,11].includes(p.tag))return cpText(c,p.a,depth+1)+"."+cpText(c,p.b,depth+1);return JSON.stringify(p);}
const OPCODES=("nop aconst_null iconst_m1 iconst_0 iconst_1 iconst_2 iconst_3 iconst_4 iconst_5 lconst_0 lconst_1 fconst_0 fconst_1 fconst_2 dconst_0 dconst_1 bipush sipush ldc ldc_w ldc2_w iload lload fload dload aload iload_0 iload_1 iload_2 iload_3 lload_0 lload_1 lload_2 lload_3 fload_0 fload_1 fload_2 fload_3 dload_0 dload_1 dload_2 dload_3 aload_0 aload_1 aload_2 aload_3 iaload laload faload daload aaload baload caload saload istore lstore fstore dstore astore istore_0 istore_1 istore_2 istore_3 lstore_0 lstore_1 lstore_2 lstore_3 fstore_0 fstore_1 fstore_2 fstore_3 dstore_0 dstore_1 dstore_2 dstore_3 astore_0 astore_1 astore_2 astore_3 iastore lastore fastore dastore aastore bastore castore sastore pop pop2 dup dup_x1 dup_x2 dup2 dup2_x1 dup2_x2 swap iadd ladd fadd dadd isub lsub fsub dsub imul lmul fmul dmul idiv ldiv fdiv ddiv irem lrem frem drem ineg lneg fneg dneg ishl lshl ishr lshr iushr lushr iand land ior lor ixor lxor iinc i2l i2f i2d l2i l2f l2d f2i f2l f2d d2i d2l d2f i2b i2c i2s lcmp fcmpl fcmpg dcmpl dcmpg ifeq ifne iflt ifge ifgt ifle if_icmpeq if_icmpne if_icmplt if_icmpge if_icmpgt if_icmple if_acmpeq if_acmpne goto jsr ret tableswitch lookupswitch ireturn lreturn freturn dreturn areturn return getstatic putstatic getfield putfield invokevirtual invokespecial invokestatic invokeinterface invokedynamic new newarray anewarray arraylength athrow checkcast instanceof monitorenter monitorexit wide multianewarray ifnull ifnonnull goto_w jsr_w breakpoint").split(" ");
function decode(c,m){
 if(!m.code)return [];const r=new Reader(m.code.bytes),out=[];
 const s16=()=>{const n=r.u2();return n>32767?n-65536:n;},s32=()=>r.u4()|0;
 while(r.p<r.a.length){const pc=r.p,op=r.u1(),name=OPCODES[op];if(!name)throw Error("opcode "+op);let args=[],ref=null,targets=[];
 if(op===16){const x=r.u1();args=[x>127?x-256:x];}
 else if(op===17)args=[s16()];
 else if(op===18||op===19||op===20||op>=178&&op<=184||[187,189,192,193].includes(op)){ref=op===18?r.u1():r.u2();args=[cpText(c,ref)];}
 else if(op===185||op===186){ref=r.u2();args=[cpText(c,ref),r.u1(),r.u1()];}
 else if(op>=21&&op<=25||op>=54&&op<=58||op===169||op===188)args=[r.u1()];
 else if(op===132){const loc=r.u1(),inc=r.u1();args=[loc,inc>127?inc-256:inc];}
 else if(op>=153&&op<=168||op===198||op===199){targets=[pc+s16()];args=targets;}
 else if(op===200||op===201){targets=[pc+s32()];args=targets;}
 else if(op===170||op===171){while(r.p%4)r.u1();const def=pc+s32();targets=[def];const pairs=[];
 if(op===170){const low=s32(),hi=s32();if(hi-low>100000)throw Error("switch");for(let k=low;k<=hi;k++){const dest=pc+s32();pairs.push([k,dest]);targets.push(dest);}}
 else {const n=s32();if(n<0||n>100000)throw Error("lookup");for(let k=0;k<n;k++){const val=s32(),dest=pc+s32();pairs.push([val,dest]);targets.push(dest);}}args=[{default:def,cases:pairs}];}
 else if(op===196){const sub=r.u1(),loc=r.u2();args=[OPCODES[sub],loc];if(sub===132)args.push(s16());}
 else if(op===197){ref=r.u2();args=[cpText(c,ref),r.u1()];}
 out.push({pc,op,name,args,ref,targets});
 }
 const boundaries=new Set(out.map(x=>x.pc));for(const x of out)for(const t of x.targets)if(!boundaries.has(t))throw Error("bad branch target "+t);
 return out;
}
function listing(c,m){return m.name+m.descriptor+"\n"+decode(c,m).map(x=>x.pc.toString().padStart(4)+" "+x.name+" "+x.args.map(a=>typeof a==="object"?JSON.stringify(a):a).join(" ")).join("\n");}

function analyzeExport(exported, stockBytes) {
 if(exported.exe_sha256!=="aa6e67c6e9be38cca002b704bc2eb1bf2b8fc199631e307a781cc7680c8d8619")
  throw Error("Unexpected EXE SHA-256; review this utility version separately.");
 if(sha256([])!=="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" ||
 sha256([97,98,99])!=="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
  throw Error("SHA-256 self-check failed");
 const parsed=[],inventory=[],paths=new Set();
 for(const item of exported.classes) {
  if(paths.has(item.path))throw Error("Duplicate class: "+item.path);paths.add(item.path);
  const bytes=b64decode(item.base64);
  if(bytes.length!==item.bytes||sha256(bytes)!==item.sha256.toLowerCase())
   throw Error("Class length/hash mismatch: "+item.path);
  const c=parseClass(bytes);let instructions=0,codeMethods=0;
  if(c.name+".class"!==item.path)throw Error("Class name/path mismatch");
  for(const m of c.methods)if(m.code){instructions+=decode(c,m).length;codeMethods++;}
  parsed.push(c);inventory.push({path:item.path,bytes:bytes.length,sha256:sha256(bytes),
    methods:c.methods.length,code_methods:codeMethods,instructions});
 }
 if(inventory.length!==exported.class_count ||
 inventory.reduce((n,x)=>n+x.bytes,0)!==exported.total_class_bytes)throw Error("Export totals mismatch");
 const of=parsed.find(x=>x.name.endsWith("/transfer/of"));
 if(!of)throw Error("Missing transfer/of");
 const ins=decode(of,of.methods.find(x=>x.name==="aM"));
 function literal(x) {
  if(x.op>=2&&x.op<=8)return x.op-3;
  if(x.op===16||x.op===17)return x.args[0];
  throw Error("Unexpected literal instruction");
 }
 const blob=Array(264),seen=new Set();
 for(let i=3;i<ins.length;i++)if(ins[i].name==="bastore"&&ins[i-3].name==="dup") {
  const index=literal(ins[i-2]);
  if(index<0||index>=264||seen.has(index))throw Error("Unexpected blob index");
  blob[index]=literal(ins[i-1])&255;seen.add(index);
 }
 if(seen.size!==264)throw Error("Incomplete encrypted legacy key");
 // Transcription of transfer/mine.V: signed Java ishr, 32-bit overflow, 32 rounds.
 const k=[2023708229,-158607964,-2120859654,1167043672],plain=[];
 const word=(a,o)=>(a[o]<<24)|(a[o+1]<<16)|(a[o+2]<<8)|a[o+3];
 const mix=(v,s,a,b)=>(((v<<4)+a)|0)^((v+s)|0)^(((v>>5)+b)|0);
 const pushWord=(out,w)=>out.push((w>>>24)&255,(w>>>16)&255,(w>>>8)&255,w&255);
 for(let off=0;off<blob.length;off+=8) {
  let a=word(blob,off),b=word(blob,off+4),s=-957401312;
  for(let r=0;r<32;r++){b=(b-mix(a,s,k[2],k[3]))|0;a=(a-mix(b,s,k[0],k[1]))|0;s=(s+1640531527)|0;}
  pushWord(plain,a);pushWord(plain,b);
 }
 if(plain[0]!==8)throw Error("Unexpected padding");
 const roundtrip=[];
 for(let off=0;off<plain.length;off+=8){
  let a=word(plain,off),b=word(plain,off+4),s=0;
  for(let r=0;r<32;r++){s=(s-1640531527)|0;a=(a+mix(b,s,k[0],k[1]))|0;b=(b+mix(a,s,k[2],k[3]))|0;}
  pushWord(roundtrip,a);pushWord(roundtrip,b);
 }
 if(!roundtrip.every((v,i)=>v===blob[i]))throw Error("Legacy blob roundtrip mismatch");
 const key=plain.slice(8),keyHash=sha256(key);
 if(keyHash!=="003d481f74298dfb9cd27e69c74405a1bb949af5c5591dedea18c284ea828b54")
  throw Error("Unexpected legacy key fingerprint");
 let stockComparison={provided:false};
 if(stockBytes){
  if(sha256(stockBytes)!=="c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32")
   throw Error("Unexpected stock BIN SHA-256");
  const slice=stockBytes.slice(0xcb2e8,0xcb3e8);
  stockComparison={provided:true,offset:"0xcb2e8",length:256,sha256:sha256(slice),
   matches_utility_key:slice.length===key.length&&slice.every((v,i)=>v===key[i])};
 }
 const report={format:"SwitchLens Easy Smart static class review v1",
  source_exe_sha256:exported.exe_sha256,application_executed:false,device_contacted:false,
  classes:inventory.length,methods:inventory.reduce((n,x)=>n+x.methods,0),
  code_methods:inventory.reduce((n,x)=>n+x.code_methods,0),
  instructions:inventory.reduce((n,x)=>n+x.instructions,0),class_bytes:exported.total_class_bytes,
  all_class_lengths_and_hashes_verified:true,all_decoded_branch_targets_valid:true,
  legacy_key:{blob_bytes:264,key_bytes:key.length,padding:8,sha256:keyHash,
   encryption_roundtrip_verified:true,stock_comparison:stockComparison},
  limitations:["Static parser, not a JVM verifier or runtime test.",
   "The supplied export is a selection of 100 classes, not all 913 JAR entries.",
   "Transport modes in the client do not establish the mode selected by the owner's switch.",
   "A shared encryption key does not establish a login bypass or explain factory field40."],
  inventory};
 const selected=new Set(["transfer/PacketHead","transfer/TLV","transfer/The","transfer/i",
  "transfer/V","transfer/V$1","transfer/of","transfer/mine","transfer/thing","transfer/From",
  "util/mine","Tempest","pages/switchdiscovery/bean/RSAKeyBean"]);
 const prefix="com/tplink/smb/easySmartUtility/";
 const disassembly=parsed.filter(c=>selected.has(c.name.slice(prefix.length)))
 .map(c=>"CLASS "+c.name+"\n"+c.methods.map(m=>listing(c,m)).join("\n\n")).join("\n\n");
 return {report,disassembly};
}

function main(args) {
 if(args.length<2||args.length>3)throw Error("Usage: node Analyze-EasySmartClasses.mjs <class-export.json> <output-directory> [stock-up.bin]");
 const [input,outdir,stock]=args;
 const exported=JSON.parse(fs.readFileSync(input,"utf8").replace(/^\uFEFF/,""));
 const result=analyzeExport(exported,stock?Array.from(fs.readFileSync(stock)):undefined);
 fs.mkdirSync(outdir,{recursive:true});
 for(const [name,contents] of [
  ["easysmart-static-analysis.json",JSON.stringify(result.report,null,2)+"\n"],
  ["easysmart-selected-bytecode.txt",result.disassembly+"\n"]]){
  const target=path.join(outdir,name);
  fs.writeFileSync(target,contents,{encoding:"utf8",flag:"wx"});
  console.log(target);
 }
 console.log("Static analysis complete. No switch contacted; no Java code executed.");
}
try {main(process.argv.slice(2));}catch(error){console.error(error.message);process.exitCode=1;}
