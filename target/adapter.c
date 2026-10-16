/* Exact-image adapter. Evidence/unknowns: docs/FIRMWARE.md.
 * No configuration setters, PoE controller commands, MIB reset, or flash writes.
 * Globals are const (flash); request state lives on the existing task's stack.
 */
#include "sg_stats.h"
#include "sg_mib.h"
#define R8(a) (*(volatile const uint8_t *)(uintptr_t)(a))
#define R32(a) (*(volatile const uint32_t *)(uintptr_t)(a))
#define W32(a,v) (*(volatile uint32_t *)(uintptr_t)(a)=(uint32_t)(v))
#define HTTP_BUFFER 0xbf010f8cu
#define HTTP_END 0xbf011540u
#define FAST_TICKS 0xbf002e94u
#define REQUEST_TICK_BUDGET 40u /* raw IRQ ticks; wall-time unit unconfirmed */
extern int fw_strcmp(const char *,const char *);
extern int fw_http_init(void *);
extern int fw_http_status(void *,int);
extern int fw_http_header(void *,const char *);
extern int fw_http_raw(void *,const char *,unsigned);
extern int fw_socket_send(uint32_t,const char *,unsigned);
extern int fw_register_read(unsigned,uint32_t,uint32_t *);

struct context {
 void *request;
 uint32_t start_ticks,uptime,port,poe_count,global[3];
 uint32_t admin,link,speed,duplex,flow;
 unsigned link_ok,cfg_speed,cfg_flow;
 uint8_t poe[48],recovery[40],recovery_counts[6];
 char description[33],text[65];
};
static void copy(uint8_t *dst,uintptr_t address,unsigned n){
 for(unsigned i=0;i<n;i++)dst[i]=R8(address+i);
}
static uint32_t be32(const uint8_t *p){return (uint32_t)p[0]<<24|(uint32_t)p[1]<<16|(uint32_t)p[2]<<8|p[3];}
static int16_t be16(const uint8_t *p){return (int16_t)((unsigned)p[0]<<8|p[1]);}
static uintptr_t config(uintptr_t ram,uintptr_t flash){return R8(0xbf0015f0u)?ram:flash;}
static int expired(const struct context *c){return (uint32_t)(R32(FAST_TICKS)-c->start_ticks)>REQUEST_TICK_BUDGET;}
static int reg_read(void *opaque,uint32_t offset,uint32_t *value){
 struct context *c=opaque;if(expired(c))return -1;
 /* Stock BFC10768 propagates callback errors (unlike the MIB wrapper). */
 return fw_register_read(0,offset,value);
}
static int scalar(struct sg_value *v,enum sg_kind kind,uint64_t n){v->kind=kind;v->number=n;return 0;}
static int string(struct sg_value *v,const char *p,unsigned max){
 unsigned n=0;while(n<max&&p[n])n++;
 v->kind=SG_TEXT;v->text=p;v->length=n;return 0;
}
static int copied_string(struct context *c,struct sg_value *v,uintptr_t address,unsigned max){
 if(max>64)return -1;
 copy((uint8_t *)c->text,address,max);c->text[max]=0;
 return string(v,c->text,max);
}
static int boolean(struct sg_value *v,unsigned n){return n<=1?scalar(v,SG_BOOL,n):-1;}
static int decimal_byte(char *out,unsigned n){
 int used=0;if(n>=100){out[used++]=(char)('0'+n/100);n%=100;out[used++]=(char)('0'+n/10);}
 else if(n>=10)out[used++]=(char)('0'+n/10);
 out[used++]=(char)('0'+n%10);return used;
}
static int ip_string(struct context *c,struct sg_value *v,uintptr_t address){
 unsigned n=0;for(unsigned i=0;i<4;i++){
  if(i)c->text[n++]='.';
  n+=(unsigned)decimal_byte(c->text+n,R8(address+i));
 }c->text[n]=0;return string(v,c->text,n);
}
static int begin(void *opaque,enum sg_scope scope,unsigned port){
 struct context *c=opaque;if(expired(c))return -1;c->port=port;
 if(scope==SG_SYSTEM){
  copy((uint8_t *)c->description,config(0xbf0015fcu,0xb41fe008u),32);
  c->description[32]=0;c->uptime=R32(0xbf002e90u);
 }else if(scope==SG_GLOBAL_POE){
  c->global[0]=R32(0xbf0143f4u);c->global[1]=R32(0xbf014400u);
 }else if(scope==SG_PORT){
  if(port<1||port>18)return -1;
  unsigned i=port-1,physical=port<=16?i:port+7;
  uintptr_t cfg=config(0xbf001658u,0xb41fe064u);
  c->admin=R32(cfg+4*i);
  /* Equivalent to PortSettingRpm's packed configuration decoding. */
  unsigned autoneg=R8(cfg+0x64u+i)&1,full=R8(cfg+0x9eu+i)&1;
  c->cfg_speed=autoneg?(full?1:6):((R8(cfg+0xd8+i)&1)?5:((R8(cfg+0xbb+i)&1)?4:(full?3:2)));
  c->cfg_flow=R8(cfg+0x112+i)&1;
  uint32_t link,speed,duplex,rxflow,txflow,discard;
  c->link_ok=!(reg_read(c,0xa188,&discard)||reg_read(c,0xa188,&link)||
    reg_read(c,0xa190+4*(physical>>4),&speed)||reg_read(c,0xa19c,&duplex)||
    reg_read(c,0xa1a0,&rxflow)||reg_read(c,0xa1a4,&txflow));
  if(c->link_ok){
   c->link=(link>>physical)&1;c->speed=(speed>>(2*(physical&15)))&3;
   c->duplex=(duplex>>physical)&1;c->flow=((rxflow&txflow)>>physical)&1;
  }
  if(port<=16){
   copy(c->poe,0xbf014408u+48*i,sizeof c->poe);
   copy(c->recovery,config(0xbf002110u,0xb41feb1cu)+8+40*i,sizeof c->recovery);
   copy(c->recovery_counts,0xbf014774u+6*i,sizeof c->recovery_counts);
  }
 }
 return 0;
}
static int has_poe(void *opaque){struct context *c=opaque;return c->port<=c->poe_count;}

struct metric { unsigned char field,selector; };
static const struct metric metrics[]={
 {SG_COUNTER_RX_BYTES,1},{SG_COUNTER_TX_BYTES,9},
 {SG_COUNTER_RX_UNICAST_PACKETS,2},{SG_COUNTER_RX_MULTICAST_PACKETS,4},{SG_COUNTER_RX_BROADCAST_PACKETS,6},
 {SG_COUNTER_TX_UNICAST_PACKETS,10},{SG_COUNTER_TX_MULTICAST_PACKETS,12},{SG_COUNTER_TX_BROADCAST_PACKETS,14},
 {SG_COUNTER_TX_DROP_PACKETS,16},{SG_COUNTER_TX_BAD_PACKETS,21},
 {SG_COUNTER_RX_BRIDGE_DISCARDS,125},{SG_COUNTER_RX_MAC_DISCARDS,84},{SG_COUNTER_RX_UNDERSIZE_DROPS,65},
 {SG_COUNTER_RX_CRC_ALIGN_ERRORS,31},{SG_COUNTER_SYMBOL_ERRORS,22},{SG_COUNTER_RX_UNKNOWN_CONTROL_OPCODES,23},
 {SG_COUNTER_RX_PAUSE_FRAMES,24},{SG_COUNTER_TX_PAUSE_FRAMES,25},{SG_COUNTER_DROP_EVENTS,26},
 {SG_COUNTER_RX_UNDERSIZE_PACKETS,35},{SG_COUNTER_TX_UNDERSIZE_PACKETS,36},
 {SG_COUNTER_RX_OVERSIZE_PACKETS,38},{SG_COUNTER_TX_OVERSIZE_PACKETS,39},
 {SG_COUNTER_RX_FRAGMENTS,40},{SG_COUNTER_RX_JABBERS,43},{SG_COUNTER_COLLISIONS,46},
 {SG_COUNTER_TX_SINGLE_COLLISION_FRAMES,17},{SG_COUNTER_TX_MULTIPLE_COLLISION_FRAMES,18},
 {SG_COUNTER_TX_DEFERRED_TRANSMISSIONS,19},{SG_COUNTER_TX_LATE_COLLISIONS,20},{SG_COUNTER_TX_EXCESSIVE_COLLISIONS,21},
 {SG_COUNTER_RX_PACKETS_64,48},{SG_COUNTER_TX_PACKETS_64,49},
 {SG_COUNTER_RX_PACKETS_65_127,51},{SG_COUNTER_TX_PACKETS_65_127,52},
 {SG_COUNTER_RX_PACKETS_128_255,54},{SG_COUNTER_TX_PACKETS_128_255,55},
 {SG_COUNTER_RX_PACKETS_256_511,57},
 {SG_COUNTER_RX_PACKETS_512_1023,60},{SG_COUNTER_TX_PACKETS_512_1023,61},
 {SG_COUNTER_RX_PACKETS_1024_1518,63},{SG_COUNTER_TX_PACKETS_1024_1518,64},
 {SG_COUNTER_RX_PACKETS_1519_MAX,66},{SG_COUNTER_TX_PACKETS_1519_MAX,67}
};
static int counter(struct context *c,enum sg_field field,struct sg_value *v){
 struct sg_registers io={c,reg_read};uint64_t value;
 if(field==SG_COUNTER_RX_GOOD_PACKETS||field==SG_COUNTER_TX_GOOD_PACKETS){
  unsigned first=field==SG_COUNTER_RX_GOOD_PACKETS?2:10;uint64_t sum=0;
  for(unsigned i=0;i<3;i++){if(sg_mib_read(&io,c->port,first+2*i,&value))return -1;sum+=value;}
  return scalar(v,SG_UINT,sum);
 }
 if(field==SG_COUNTER_RX_BAD_PACKETS){
  /* Preserve the web aggregate, including its unusual TX categories and
   * 32-bit subtotal wrap: selector37 + selector34 +43 +40 +31. */
  const unsigned char selectors[]={38,39,35,36,43,40,31};
  uint64_t sum=0;uint32_t subtotal=0;
  for(unsigned i=0;i<7;i++){
   if(sg_mib_read(&io,c->port,selectors[i],&value))return -1;
   if(i<4){subtotal+=(uint32_t)value;if(i&1){sum+=subtotal;subtotal=0;}}
   else sum+=value;
  }return scalar(v,SG_UINT,sum);
 }
 for(unsigned i=0;i<sizeof metrics/sizeof metrics[0];i++)if(metrics[i].field==field){
  if(sg_mib_read(&io,c->port,metrics[i].selector,&value))return -1;
  return scalar(v,SG_UINT,value);
 }return -1;
}
static int get(void *opaque,enum sg_field field,struct sg_value *v){
 struct context *c=opaque;if(expired(c))return -1;
 if(field>=SG_COUNTER_RX_BYTES&&field<=SG_COUNTER_TX_PACKETS_1519_MAX)return counter(c,field,v);
 switch(field){
 case SG_SYSTEM_MODEL:return string(v,"TL-SG1218MPE",12);
 case SG_SYSTEM_HARDWARE_VERSION:return copied_string(c,v,0xbfce02f4u,32);
 case SG_SYSTEM_FIRMWARE_VERSION:return copied_string(c,v,0xbf014348u,64);
 case SG_SYSTEM_DESCRIPTION:return string(v,c->description,32);
 case SG_SYSTEM_UPTIME_TICKS_RAW:return scalar(v,SG_UINT,c->uptime);
 case SG_SYSTEM_MAC:{
  uint8_t mac[6];uint32_t hi,lo;static const char hex[]="0123456789abcdef";
  if(reg_read(c,0xa9ec,&hi)||reg_read(c,0xa9f0,&lo))return -1;
  mac[0]=(uint8_t)(hi>>8);mac[1]=(uint8_t)hi;
  for(unsigned i=0;i<4;i++)mac[i+2]=(uint8_t)(lo>>(24-8*i));
  for(unsigned i=0;i<6;i++){c->text[i*3]=hex[mac[i]>>4];c->text[i*3+1]=hex[mac[i]&15];c->text[i*3+2]=i==5?0:':';}
  return string(v,c->text,17);
 }
 case SG_SYSTEM_IP_ADDRESS:return ip_string(c,v,0xbf016d3au);
 case SG_SYSTEM_SUBNET_MASK:return ip_string(c,v,0xbf016d3eu);
 case SG_SYSTEM_DEFAULT_GATEWAY:return ip_string(c,v,0xbf016d42u);
 case SG_GLOBAL_POE_BUDGET_W:return (int32_t)c->global[0]>=0?scalar(v,SG_TENTHS,c->global[0]):-1;
 case SG_GLOBAL_POE_CONSUMPTION_W:return (int32_t)c->global[1]>=0?scalar(v,SG_TENTHS,c->global[1]):-1;
 case SG_GLOBAL_POE_CONSUMPTION_RAW:return (int32_t)c->global[1]>=0?scalar(v,SG_UINT,c->global[1]):-1;
 case SG_GLOBAL_POE_REMAINING_W:
  if((int32_t)c->global[0]<0||(int32_t)c->global[1]<0)return -1;
  return scalar(v,SG_TENTHS,c->global[0]>c->global[1]?c->global[0]-c->global[1]:0);
 case SG_GLOBAL_POE_RECOVERY_ENABLED:return boolean(v,R8(config(0xbf002110u,0xb41feb1cu)+4));
 case SG_PORT_ADMIN_ENABLED:return scalar(v,SG_BOOL,c->admin!=0);
 case SG_PORT_FLOW_CONTROL_CONFIGURED:return boolean(v,c->cfg_flow);
 case SG_PORT_SPEED_CONFIG_CODE:return scalar(v,SG_UINT,c->cfg_speed);
 case SG_PORT_LINK_UP:return c->link_ok?boolean(v,c->link):-1;
 case SG_PORT_SPEED_ACTUAL_CODE:
  if(!c->link_ok)return -1;
  return scalar(v,SG_UINT,!c->link?0:(c->speed<2?2+2*c->speed+c->duplex:(c->speed==2&&c->duplex?6:1)));
 case SG_PORT_SPEED_MBPS:
  if(!c->link_ok||!c->link||c->speed>2)return -1;
  return scalar(v,SG_UINT,c->speed==0?10:(c->speed==1?100:1000));
 case SG_PORT_DUPLEX:if(!c->link_ok||!c->link)return -1;return string(v,c->duplex?"full":"half",4);
 case SG_PORT_FLOW_CONTROL_ACTIVE:return c->link_ok?boolean(v,c->link&&c->flow):-1;
 case SG_POE_ENABLED:{int n=be16(c->poe+2);return n>=0?scalar(v,SG_BOOL,n!=0):-1;}
 case SG_POE_STATUS_CODE:return scalar(v,SG_UINT,be32(c->poe+24));
 case SG_POE_STATUS:{
  static const char *const status[]={"OFF","TURNING-ON","ON","OVERLOAD","SHORT","NOSTANDARD-PD","VOLTAGE-HIGH","VOLTAGE-LOW","HARDWARE-FAULT","OVERTEMPERATURE"};
  unsigned n=be32(c->poe+24);return n<10?string(v,status[n],32):-1;
 }
 case SG_POE_POWER_W:case SG_POE_CURRENT_MA:case SG_POE_VOLTAGE_V:{
  unsigned offset=field==SG_POE_POWER_W?18:(field==SG_POE_CURRENT_MA?14:16);
  int n=be16(c->poe+offset);if(n<=0)return -1; /* web shows zero as unavailable */
  return scalar(v,field==SG_POE_CURRENT_MA?SG_UINT:SG_TENTHS,(unsigned)n);
 }
 case SG_POE_PD_CLASS_RAW:return scalar(v,SG_UINT,be32(c->poe+20));
 case SG_POE_PD_CLASS:{
  uint32_t n=be32(c->poe+20);const unsigned short codes[]={330,40,70,154,300};
  for(unsigned i=0;i<5;i++)if(n==codes[i])return scalar(v,SG_UINT,i);
  return -1;
 }
 case SG_POE_PRIORITY_CODE:return scalar(v,SG_UINT,be32(c->poe+8));
 case SG_POE_POWER_LIMIT_MODE:{int n=be16(c->poe+4);return n>=0?string(v,n==330?"auto":"fixed",5):-1;}
 case SG_POE_POWER_LIMIT_W:{int n=be16(c->poe+4);return n>=0&&n!=330?scalar(v,SG_TENTHS,(unsigned)n):-1;}
 case SG_RECOVERY_PING_ADDRESS:
  for(unsigned i=0;i<16;i++)c->text[i]=(char)c->recovery[8+i];
  c->text[16]=0;
  return string(v,c->text,16);
 case SG_RECOVERY_STARTUP_DELAY_SECONDS:case SG_RECOVERY_INTERVAL_SECONDS:
 case SG_RECOVERY_FAILURE_THRESHOLD:case SG_RECOVERY_BREAK_SECONDS:{
  unsigned offset=24+4*(field-SG_RECOVERY_STARTUP_DELAY_SECONDS);
  return scalar(v,SG_UINT,be32(c->recovery+offset));
 }
 case SG_RECOVERY_FAILURES_CURRENT:case SG_RECOVERY_REBOOTS_RAW:case SG_RECOVERY_PINGS_RAW:{
  int n=be16(c->recovery_counts+2*(field-SG_RECOVERY_FAILURES_CURRENT));
  return n>=0?scalar(v,SG_UINT,(unsigned)n):-1;
 }
 case SG_LOOP_RLDP_MASK_RAW:return scalar(v,SG_UINT,R32(0xbf00e280u));
 case SG_LOOP_RLPP_MASK_RAW:return scalar(v,SG_UINT,R32(0xbf00e2a0u));
 case SG_LOOP_RLPP_SELF_MASK_RAW:return scalar(v,SG_UINT,R32(0xbf00e2a4u));
 default:return -1; /* Unknown uptime unit, validity, lag, extend, loop mode etc. */
 }
}
static int write_body(void *opaque,const char *bytes,size_t length){
 struct context *c=opaque;
 if(expired(c)||length>SG_JSON_BUFFER_SIZE)return -1;
 return fw_http_raw(c->request,bytes,(unsigned)length)==0?(int)length:-1;
}
static int finish(void *opaque){
 struct context *c=opaque;uint32_t end=R32(HTTP_END);
 if(expired(c)||end<HTTP_BUFFER||end>HTTP_END)return -1;
 if(end==HTTP_BUFFER)return 0;
 int result=fw_socket_send(R32((uintptr_t)c->request),(const char *)(uintptr_t)HTTP_BUFFER,end-HTTP_BUFFER);
 W32(HTTP_END,HTTP_BUFFER);return result;
}
/* 0=stock statistics,1=JSON,2=no match. Assembly translates this to strcmp ABI. */
int sg_route_kind(const char *path,const char *stock){
 static const char route[]="/stats.json";
 unsigned i=0;while(i<sizeof route&&path[i]==route[i]){if(!route[i])return 1;i++;}
 return fw_strcmp(path,stock)==0?0:2;
}
int sg_http_stats(void *request){
 struct context c={0};c.request=request;c.start_ticks=R32(FAST_TICKS);
 c.poe_count=R32(0xbf0143e0u);
 if(!request||c.poe_count!=16)return -1;
 if(fw_http_init(request)||fw_http_status(request,200)||
    fw_http_header(request,"Content-Type: application/json\r\nCache-Control: no-store\r\nX-SwitchLens-Build: experimental-1"))return -1;
 const struct sg_source source={&c,begin,get,has_poe};
 const struct sg_sink sink={&c,write_body,finish};struct sg_result result;
 int status=sg_stats_emit(&source,&sink,&result);
 if(status)W32(HTTP_END,HTTP_BUFFER); /* discard unsent partial tail */
 return status;
}
