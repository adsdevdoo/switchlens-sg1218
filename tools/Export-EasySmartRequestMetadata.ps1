# Offline request metadata only. Does not execute the utility or contact a switch.
param(
    [string]$ZipPath = (Join-Path $env:USERPROFILE 'Downloads\EasySmartConfigurationUtility.zip'),
    [string]$OutputDirectory = 'C:\tmp'
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
if (-not ('SwitchLens.RequestMetadata' -as [type])) {
Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Text;
using System.Collections.Generic;

namespace SwitchLens {
public sealed class R {
 public byte[] B; public int P;
 public R(byte[] b) { B=b; }
 public byte U1(){ if(P>=B.Length)throw new InvalidDataException("Truncated class");return B[P++]; }
 public ushort U2(){return (ushort)((U1()<<8)|U1());}
 public uint U4(){return ((uint)U1()<<24)|((uint)U1()<<16)|((uint)U1()<<8)|U1();}
 public int I4(){return unchecked((int)U4());}
 public int Length(){uint n=U4();if(n>Int32.MaxValue)throw new InvalidDataException("Length overflow");return (int)n;}
 public byte[] Take(int n){if(n<0||n>B.Length-P)throw new InvalidDataException("Invalid length");byte[] a=new byte[n];Array.Copy(B,P,a,0,n);P+=n;return a;}
 public void Skip(int n){if(n<0||n>B.Length-P)throw new InvalidDataException("Invalid skip");P+=n;}
}
public sealed class CP {public int Tag,A,B,Number;public string Text;}
public sealed class Event {
 public int offset;
 public string kind;
 public int? number;
 public string symbol;
}
public sealed class Method {
 public string name,descriptor;
 public int code_bytes;
 public List<Event> request_metadata=new List<Event>();
}
public sealed class Field {public string name,descriptor;}
public sealed class Summary {
 public string name;
 public int major_version;
 public List<Field> fields=new List<Field>();
 public List<Method> methods=new List<Method>();
}
public static class RequestMetadata {
 static string Utf(CP[] cp,int i){if(i<=0||i>=cp.Length||cp[i]==null||cp[i].Tag!=1)throw new InvalidDataException("Bad UTF reference");return cp[i].Text;}
 static string Sym(CP[] cp,int i){
  if(i<=0||i>=cp.Length||cp[i]==null)throw new InvalidDataException("Bad pool reference");
  CP c=cp[i];
  if(c.Tag==1)return c.Text;
  if(c.Tag==7)return Utf(cp,c.A);
  if(c.Tag==12)return Utf(cp,c.A)+":"+Utf(cp,c.B);
  if(c.Tag==9||c.Tag==10||c.Tag==11)return Sym(cp,c.A)+"."+Sym(cp,c.B);
  if(c.Tag==18||c.Tag==17)return Sym(cp,c.B);
  return "[constant]";
 }
 static void Emit(List<Event> list,int pc,string kind,int? number,string symbol){
  list.Add(new Event{offset=pc,kind=kind,number=number,symbol=symbol});
 }
 static void Pool(CP[] cp,int index,int pc,bool enumClass,List<Event> events){
  CP c=cp[index];
  if(c==null)throw new InvalidDataException("Bad constant");
  if(c.Tag==3)Emit(events,pc,"integer",c.Number,null);
  // Only enum labels may be exported as string values. All other string contents are omitted.
  else if(c.Tag==8&&enumClass){
   string label=Utf(cp,c.A);
   if(System.Text.RegularExpressions.Regex.IsMatch(label,@"^[A-Z][A-Z0-9_]{0,31}$"))
    Emit(events,pc,"enum_label",null,label);
  }
 }
 static bool Selected(string cls,string method){
  if(cls.EndsWith("/DataBean$Request"))return method=="<clinit>";
  if(method.StartsWith("build")&&method.EndsWith("Request"))return true;
  if(method=="handleResponse"||method=="toArray")return true;
  return cls.EndsWith("/DataBean")&&method=="<init>";
 }
 static void Events(byte[] code,CP[] cp,bool enumClass,List<Event> events){
  R r=new R(code);
  while(r.P<code.Length){
   int pc=r.P,op=r.U1();
   if(op>=2&&op<=8)Emit(events,pc,"integer",op-3,null);
   else if(op==16)Emit(events,pc,"integer",unchecked((sbyte)r.U1()),null);
   else if(op==17)Emit(events,pc,"integer",unchecked((short)r.U2()),null);
   else if(op==18)Pool(cp,r.U1(),pc,enumClass,events);
   else if(op==19||op==20)Pool(cp,r.U2(),pc,enumClass,events);
   else if(op>=178&&op<=181)Emit(events,pc,"field_reference",null,Sym(cp,r.U2()));
   else if(op>=182&&op<=184)Emit(events,pc,"method_reference",null,Sym(cp,r.U2()));
   else if(op==185||op==186){Emit(events,pc,"method_reference",null,Sym(cp,r.U2()));r.Skip(2);}
   else if(op==187||op==189||op==192||op==193)r.Skip(2);
   else if(op==197)r.Skip(3);
   else if((op>=21&&op<=25)||(op>=54&&op<=58)||op==169||op==188)r.Skip(1);
   else if(op==132||(op>=153&&op<=168)||op==198||op==199)r.Skip(2);
   else if(op==200||op==201)r.Skip(4);
   else if(op==196){int sub=r.U1();r.Skip(sub==132?4:2);}
   else if(op==170||op==171){
    while((r.P&3)!=0)r.Skip(1);
    r.Skip(4);
    if(op==170){
     int low=r.I4(),high=r.I4();
     long count=(long)high-low+1;
     if(count<0||count>65536)throw new InvalidDataException("Invalid tableswitch");
     for(long j=0;j<count;j++){Emit(events,pc,"switch_case",(int)(low+j),null);r.Skip(4);}
    }else{
     int count=r.I4();if(count<0||count>65536)throw new InvalidDataException("Invalid lookupswitch");
     for(int j=0;j<count;j++){Emit(events,pc,"switch_case",r.I4(),null);r.Skip(4);}
    }
   }else if(op>201)throw new InvalidDataException("Unsupported JVM opcode");
  }
 }
 public static Summary Parse(byte[] bytes){
  R r=new R(bytes);
  if(r.U4()!=0xCAFEBABE)throw new InvalidDataException("Not a class");
  r.U2();int major=r.U2();
  int count=r.U2();CP[] cp=new CP[count];
  for(int i=1;i<count;i++){
   CP c=new CP();c.Tag=r.U1();cp[i]=c;
   switch(c.Tag){
    case 1:c.Text=Encoding.UTF8.GetString(r.Take(r.U2()));break;
    case 3:c.Number=r.I4();break;
    case 4:r.Skip(4);break;
    case 5:case 6:r.Skip(8);i++;break;
    case 7:case 8:case 16:case 19:case 20:c.A=r.U2();break;
    case 9:case 10:case 11:case 12:case 17:case 18:c.A=r.U2();c.B=r.U2();break;
    case 15:r.Skip(3);break;
    default:throw new InvalidDataException("Unknown pool tag");
   }
  }
  r.U2();Summary result=new Summary();result.name=Sym(cp,r.U2());result.major_version=major;r.U2();
  int interfaces=r.U2();r.Skip(interfaces*2);
  int fields=r.U2();
  for(int i=0;i<fields;i++){
   r.U2();Field f=new Field{name=Utf(cp,r.U2()),descriptor=Utf(cp,r.U2())};result.fields.Add(f);
   int attrs=r.U2();for(int a=0;a<attrs;a++){r.U2();r.Skip(r.Length());}
  }
  int methods=r.U2();
  for(int i=0;i<methods;i++){
   r.U2();Method m=new Method{name=Utf(cp,r.U2()),descriptor=Utf(cp,r.U2())};
   int attrs=r.U2();
   for(int a=0;a<attrs;a++){
    string attr=Utf(cp,r.U2());byte[] data=r.Take(r.Length());
    if(attr!="Code")continue;
    R cr=new R(data);cr.U2();cr.U2();byte[] code=cr.Take(cr.Length());m.code_bytes=code.Length;
    if(Selected(result.name,m.name))Events(code,cp,result.name.EndsWith("/DataBean$Request"),m.request_metadata);
   }
   result.methods.Add(m);
  }
  int classAttrs=r.U2();for(int a=0;a<classAttrs;a++){r.U2();r.Skip(r.Length());}
  if(r.P!=bytes.Length)throw new InvalidDataException("Trailing class data");
  return result;
 }
}
}
'@
}
$expectedHash = 'aa6e67c6e9be38cca002b704bc2eb1bf2b8fc199631e307a781cc7680c8d8619'
$sha = [Security.Cryptography.SHA256]::Create()
try {
 $outer = [IO.Compression.ZipFile]::OpenRead($ZipPath)
 try {
  $exeEntry = @($outer.Entries | Where-Object { $_.Name -eq 'Easy Smart Configuration Utility.exe' })
  if ($exeEntry.Count -ne 1 -or $exeEntry[0].Length -ne 1164102) { throw 'Unexpected launcher; stopped' }
  $stream=$exeEntry[0].Open();$memory=New-Object IO.MemoryStream
  try {$stream.CopyTo($memory);$exeBytes=$memory.ToArray()} finally {$stream.Dispose();$memory.Dispose()}
 } finally {$outer.Dispose()}
 $actualHash=([BitConverter]::ToString($sha.ComputeHash($exeBytes))).Replace('-','').ToLowerInvariant()
 if ($actualHash -ne $expectedHash) {throw 'Launcher SHA-256 does not match the inspected version'}
 $jarBytes=New-Object byte[] (1164102-63488)
 [Array]::Copy($exeBytes,63488,$jarBytes,0,$jarBytes.Length)
 $jarMemory=New-Object IO.MemoryStream
 $jarMemory.Write($jarBytes,0,$jarBytes.Length);$jarMemory.Position=0
 $jar=[IO.Compression.ZipArchive]::new($jarMemory,[IO.Compression.ZipArchiveMode]::Read,$false)
 $wanted=@(
  'com/tplink/smb/easySmartUtility/bean/DataBean$Request.class',
  'com/tplink/smb/easySmartUtility/bean/DataBean.class',
  'com/tplink/smb/easySmartUtility/pages/DeviceInfo.class',
  'com/tplink/smb/easySmartUtility/pages/switchdiscovery/bean/SwitchDiscoveryBean.class',
  'com/tplink/smb/easySmartUtility/pages/switchdiscovery/bean/SwitchLoginBean.class',
  'com/tplink/smb/easySmartUtility/pages/switchdiscovery/bean/SwitchModel.class'
 )
 $summaries=New-Object 'System.Collections.Generic.List[object]'
 try {
  foreach($entryPath in $wanted){
   $entry=$jar.GetEntry($entryPath)
   if($null -eq $entry -or $entry.Length -gt 65536){throw "Missing or oversized class: $entryPath"}
   $stream=$entry.Open();$memory=New-Object IO.MemoryStream
   try{$stream.CopyTo($memory);$bytes=$memory.ToArray()}finally{$stream.Dispose();$memory.Dispose()}
   $parsed=[SwitchLens.RequestMetadata]::Parse($bytes)
   if(($parsed.name+'.class') -cne $entryPath){throw 'Class name mismatch'}
   $summaries.Add([pscustomobject]@{
    path=$entryPath
    bytes=$bytes.Length
    sha256=([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()
    metadata=$parsed
   })
  }
 }finally{$jar.Dispose();$jarMemory.Dispose()}
}finally{$sha.Dispose()}
$null=New-Item -ItemType Directory -Path $OutputDirectory -Force
$output=Join-Path $OutputDirectory ('easysmart-request-metadata-'+[guid]::NewGuid().ToString('N')+'.json')
$report=[ordered]@{
 format='SwitchLens Easy Smart selected request metadata v1'
 timestamp_utc=[DateTime]::UtcNow.ToString('o')
 exe_sha256=$actualHash
 application_executed=$false
 device_contacted=$false
 full_bytecode_included=$false
 credentials_read=$false
 class_count=$summaries.Count
 limitations=@(
  'Static metadata only; not a runtime or server authorization test.',
  'References and integers are ordered by bytecode offset; no full control/data-flow inference.',
  'Only enum labels are exported as string values; no Java bytecode/base64 or key material.'
 )
 classes=$summaries.ToArray()
}
$json=$report | ConvertTo-Json -Depth 12
[IO.File]::WriteAllText($output,$json,[Text.UTF8Encoding]::new($false))
Write-Host "Saved: $output"
Write-Host "Classes: $($summaries.Count). No utility execution or switch requests."
Write-Host 'Attach this metadata JSON to GitHub issue #1 or upload it to the repository and send its link.'
