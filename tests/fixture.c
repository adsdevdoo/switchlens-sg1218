#include "sg_stats.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
/* Synthetic host-only fixture. Never connects to a switch. */
struct fixture {
 unsigned port, gets, begins, writes, finishes, forced_gets;
 int mode, fail_scope, unknown_poe, finish_fail;
 size_t bytes, chunk, stop;
 uint64_t counter;
 const char *description;
 size_t description_length;
};
static int begin(void *p,enum sg_scope scope,unsigned port){struct fixture *f=p;f->begins++;f->port=port;return (int)scope==f->fail_scope?-1:0;}
static int has_poe(void *p){struct fixture *f=p;return f->unknown_poe?-1:f->port<=16;}
static void str(struct sg_value *v,const char *s){v->kind=SG_TEXT;v->text=s;v->length=strlen(s);}
static int get(void *p,enum sg_field field,struct sg_value *v){
 struct fixture *f=p;f->gets++;*v=(struct sg_value){SG_NULL,0,0,0};
 if(field==SG_COUNTER_RX_DISCARDS||field==SG_COUNTER_TX_PACKETS_256_511)f->forced_gets++;
 if(f->mode==1)return 0;
 if(f->mode==2)return -1;
 if(f->mode==3){v->kind=SG_BOOL;v->number=2;return 0;}
 if(field>=SG_COUNTER_RX_BYTES&&field<=SG_COUNTER_TX_PACKETS_1519_MAX){v->kind=SG_UINT;v->number=f->counter;return 0;}
 v->kind=SG_UINT;v->number=0;
 switch(field){
 case SG_SYSTEM_MODEL:str(v,"TL-SG1218MPE");break;
 case SG_SYSTEM_HARDWARE_VERSION:str(v,"TL-SG1218MPE 5.0");break;
 case SG_SYSTEM_FIRMWARE_VERSION:str(v,"synthetic fixture");break;
 case SG_SYSTEM_DESCRIPTION:v->kind=SG_TEXT;v->text=f->description;v->length=f->description_length;break;
 case SG_SYSTEM_MAC:str(v,"02:00:00:00:00:01");break;
 case SG_SYSTEM_IP_ADDRESS:str(v,"192.0.2.10");break;
 case SG_SYSTEM_SUBNET_MASK:str(v,"255.255.255.0");break;
 case SG_SYSTEM_DEFAULT_GATEWAY:str(v,"192.0.2.1");break;
 case SG_SYSTEM_UPTIME_SECONDS:v->kind=SG_NULL;break;
 case SG_SYSTEM_UPTIME_TICKS_RAW:v->number=UINT32_MAX;break;
 case SG_GLOBAL_POE_BUDGET_W:v->number=250;break;
 case SG_GLOBAL_POE_CONSUMPTION_W:v->kind=SG_TENTHS;v->number=123;break;
 case SG_GLOBAL_POE_REMAINING_W:v->kind=SG_TENTHS;v->number=2377;break;
 case SG_GLOBAL_POE_CONSUMPTION_RAW:v->number=123;break;
 case SG_GLOBAL_POE_RECOVERY_ENABLED:case SG_PORT_ADMIN_ENABLED:case SG_PORT_LINK_UP:
 case SG_PORT_FLOW_CONTROL_CONFIGURED:case SG_PORT_FLOW_CONTROL_ACTIVE:case SG_POE_ENABLED:
 case SG_POE_MEASUREMENTS_VALID:case SG_POE_EXTEND_ENABLED:case SG_RECOVERY_ENABLED:case SG_LOOP_ENABLED:
  v->kind=SG_BOOL;v->number=1;break;
 case SG_PORT_SPEED_MBPS:v->number=1000;break;
 case SG_PORT_DUPLEX:str(v,"full");break;
 case SG_POE_STATUS_CODE:v->number=2;break;
 case SG_POE_STATUS:str(v,"ON");break;
 case SG_POE_POWER_W:v->kind=SG_TENTHS;v->number=123;break;
 case SG_POE_CURRENT_MA:v->number=246;break;
 case SG_POE_VOLTAGE_V:v->kind=SG_TENTHS;v->number=500;break;
 case SG_POE_PD_CLASS:v->number=4;break;
 case SG_POE_PD_CLASS_RAW:v->number=300;break;
 case SG_POE_POWER_LIMIT_MODE:str(v,"auto");break;
 case SG_POE_POWER_LIMIT_W:v->kind=SG_NULL;break;
 case SG_RECOVERY_PING_ADDRESS:str(v,"192.0.2.20");break;
 default:break;
 }
 return 0;
}
static int write_bytes(void *p,const char *data,size_t n){
 struct fixture *f=p;f->writes++;
 if(f->bytes>=f->stop)return f->mode==4?0:-1;
 if(n>f->chunk)n=f->chunk;
 if(n>f->stop-f->bytes)n=f->stop-f->bytes;
 if(fwrite(data,1,n,stdout)!=n)return -1;
 f->bytes+=n;return (int)n;
}
static int finish(void *p){struct fixture *f=p;f->finishes++;return f->finish_fail?-1:fflush(stdout);}
int main(int argc,char **argv){
 struct fixture f={0};
 f.chunk=128;f.stop=(size_t)-1;f.counter=UINT64_MAX;f.fail_scope=-1;
 f.description="Lab \"A\"\\\n\320\277\320\276\321\200\321\202";f.description_length=strlen(f.description);
 for(int i=1;i<argc;i++){
  if(i+1>=argc)return 99;
  const char *key=argv[i],*val=argv[++i];
  if(!strcmp(key,"--mode"))f.mode=atoi(val);
  else if(!strcmp(key,"--chunk"))f.chunk=(size_t)strtoull(val,0,10);
  else if(!strcmp(key,"--stop"))f.stop=(size_t)strtoull(val,0,10);
  else if(!strcmp(key,"--counter"))f.counter=(uint64_t)strtoull(val,0,10);
  else if(!strcmp(key,"--fail-scope"))f.fail_scope=atoi(val);
  else if(!strcmp(key,"--unknown-poe"))f.unknown_poe=atoi(val);
  else if(!strcmp(key,"--finish-fail"))f.finish_fail=atoi(val);
  else if(!strcmp(key,"--text-hex")){
   static char input[256];size_t len=strlen(val);
   if(len%2||len/2>sizeof input)return 99;
   for(size_t j=0;j<len/2;j++){unsigned x;if(sscanf(val+2*j,"%2x",&x)!=1)return 99;input[j]=(char)x;}
   f.description=input;f.description_length=len/2;
  }else return 99;
 }
 struct sg_source source={&f,begin,get,has_poe};struct sg_sink sink={&f,write_bytes,finish};struct sg_result r;
 int status=sg_stats_emit(&source,&sink,&r);
 fprintf(stderr,"{\"status\":%d,\"bytes\":%zu,\"unavailable\":%u,\"invalid\":%u,\"gets\":%u,\"begins\":%u,\"writes\":%u,\"finishes\":%u,\"forced_gets\":%u}\n",status,r.bytes_accepted,r.unavailable_fields,r.invalid_fields,f.gets,f.begins,f.writes,f.finishes,f.forced_gets);
 return status?1:0;
}
