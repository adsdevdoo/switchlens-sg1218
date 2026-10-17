/* Exact 20230616 image only. No new persistent RAM or flash writes.
 * BF014840 is the stock GPIO27 hysteresis state. During a bounded test it
 * contains a tagged saved state/level/start tick. Stock aggregation continues;
 * its invalid-state branch preserves our tag until the output hook handles it.
 * All callers run in the cooperative event loop, not in the timer ISR.
 */
#include "sg_stats.h"
#include "cooling.h"
#define R(a) (*(volatile const uint32_t *)(uintptr_t)(a))
#define STATE (*(volatile uint32_t *)(uintptr_t)0xbf014840u)
#define TICKS R(0xbf002e94u)
#define TAG 0xd4000000u
#define MASK 0x00ffffffu
struct command;
typedef int (*handler)(const struct command *, int, int, char **);
struct command { const char *name; int maxargs, repeat; handler run; const char *help; };
extern const struct command *fw_cli_lookup(const char *);
extern int fw_cli_poll(unsigned);
extern int fw_cli_help(const struct command *,int,int,char **);
extern int fw_cli_reg(const struct command *,int,int,char **);
extern int fw_strcmp(const char *,const char *);
extern int fw_printf(const char *,...);
extern void fw_gpio_write(unsigned,unsigned);
extern void fw_cool_poll(void);
static int tagged(uint32_t s){return (s&0xfc000000u)==TAG;}
static uint32_t elapsed(uint32_t s,uint32_t now){return (now-(s&MASK))&MASK;}
static int same(const char *a,const char *b){return fw_strcmp(a,b)==0;}
static void restore(uint32_t s){STATE=(s>>25)&1;fw_cool_poll();}

/* Replaces BFC5C344. Expiry calls the original aggregation/hysteresis routine
 * once after restoring 0/1; that invocation returns here with a normal state.
 * Other GPIO bits are preserved by the original read/modify/write helper.
 */
void sg_cool_output(uint32_t s){
 if(tagged(s)){
  if(elapsed(s,TICKS)>=SG_COOL_LIMIT){restore(s);return;}
  fw_gpio_write(27,(s>>24)&1);
 }else if(s<=1)fw_gpio_write(27,s);
}
int sg_cli_poll(unsigned arg){
 uint32_t s=STATE;
 if(tagged(s)&&elapsed(s,TICKS)>=SG_COOL_LIMIT)restore(s);
 return fw_cli_poll(arg);
}
void sg_cool_snapshot(struct sg_cooling *c){
 c->state=STATE;c->ticks=TICKS;
 c->control=R(0xb8003500u);c->direction=R(0xb8003508u);c->data=R(0xb800350cu);
 c->power=R(0xbf014400u);
}
int sg_cool_get(const struct sg_cooling *c,enum sg_field f,struct sg_value *v){
 uint32_t s=c->state,e=elapsed(s,c->ticks);int test=tagged(s);
 v->kind=SG_UINT;
 switch(f){
 case SG_COOLING_GPIO_CONTROL_RAW:v->number=c->control;break;
 case SG_COOLING_GPIO_DIRECTION_RAW:v->number=c->direction;break;
 case SG_COOLING_GPIO_DATA_RAW:v->number=c->data;break;
 case SG_COOLING_CONTROLLER_STATE_RAW:v->number=s;break;
 case SG_COOLING_FAST_TICKS_RAW:v->number=c->ticks;break;
 case SG_COOLING_POE_LOAD_RAW:if((int32_t)c->power<0)return -1;v->number=c->power;break;
 case SG_COOLING_GPIO26_LEVEL:v->number=(c->data>>26)&1;break;
 case SG_COOLING_GPIO27_LEVEL:v->number=(c->data>>27)&1;break;
 case SG_COOLING_AUTO_STATE:if(!test&&s>1)return -1;v->number=test?(s>>25)&1:s;break;
 case SG_COOLING_TEST_LEVEL:if(!test)return -1;v->number=(s>>24)&1;break;
 case SG_COOLING_REMAINING_TICKS:v->number=test&&e<SG_COOL_LIMIT?SG_COOL_LIMIT-e:0;break;
 case SG_COOLING_TEST_LIMIT_TICKS:v->number=SG_COOL_LIMIT;break;
 case SG_COOLING_MODE:
  v->kind=SG_TEXT;v->text=test?(e<SG_COOL_LIMIT?"test":"expired"):(s<=1?"auto":"invalid");
  v->length=test?(e<SG_COOL_LIMIT?4:7):(s<=1?4:7);break;
 default:return -1;
 }return 0;
}
static void status(void){
 struct sg_cooling c;sg_cool_snapshot(&c);
 fw_printf("cool v0.1.2: cnr=0x%08x dir=0x%08x data=0x%08x\n",c.control,c.direction,c.data);
 fw_printf("gpio26=%u gpio27=%u state=0x%08x ticks=%u poe_raw=%u\n",(c.data>>26)&1,(c.data>>27)&1,c.state,c.ticks,c.power);
 if(tagged(c.state))fw_printf("test=%u remaining_ticks=%u; cool auto cancels\n",(c.state>>24)&1,elapsed(c.state,c.ticks)<SG_COOL_LIMIT?SG_COOL_LIMIT-elapsed(c.state,c.ticks):0);
 else fw_printf(c.state<=1?"mode=auto; rpm/status unknown\n":"mode=invalid; test refused\n");
}
static int cool(const struct command *cmd,int flags,int argc,char **argv){
 (void)cmd;(void)flags;
 if(argc==2&&same(argv[1],"status")){status();return 0;}
 if(argc==2&&same(argv[1],"auto")){
  uint32_t s=STATE;
  if(tagged(s))restore(s);
  else if(s>1){fw_printf("cool: invalid state; unchanged\n");return 1;}
  fw_printf("cool: auto\n");return 0;
 }
 if(argc==3&&same(argv[1],"test")&&(same(argv[2],"0")||same(argv[2],"1"))){
  uint32_t s=STATE,level=(unsigned)(argv[2][0]-'0');
  if(tagged(s)){fw_printf("cool: test already active; use cool auto\n");return 1;}
  if(s>1||(R(0xb8003500u)&(1u<<27))||!(R(0xb8003508u)&(1u<<27))){
   fw_printf("cool: state/mux/direction mismatch; unchanged\n");return 1;
  }
  STATE=TAG|(s<<25)|(level<<24)|(TICKS&MASK);
  sg_cool_output(STATE);
  fw_printf("cool: GPIO27=%u for %u raw ticks; then auto\n",level,SG_COOL_LIMIT);return 0;
 }
 fw_printf("cool status | cool test 0 | cool test 1 | cool auto\n");return 1;
}
/* Strict complete-token unsigned base-0 parser, matching stock numeric syntax.
 * Cannot detect a dropped digit if the remaining token is still valid.
 */
static int number(const char *p,uint32_t *out){
 uint32_t n=0;unsigned base=10,d,count=0;
 if(!p||!*p)return 0;
 if(p[0]=='0'&&(p[1]=='x'||p[1]=='X')){base=16;p+=2;}
 else if(p[0]=='0'&&p[1])base=8;
 for(;*p;p++){
  if(*p>='0'&&*p<='9')d=(unsigned)(*p-'0');
  else if(*p>='a'&&*p<='f')d=(unsigned)(*p-'a')+10;
  else if(*p>='A'&&*p<='F')d=(unsigned)(*p-'A')+10;
  else return 0;
  if(d>=base||n>(UINT32_MAX-d)/base)return 0;
  n=n*base+d;count++;
 }*out=n;return count!=0;
}
static int reg_guard(const struct command *cmd,int flags,int argc,char **argv){
 uint32_t address,value=0;int read=0,ram=0;
 if(argc<3||argc>4)goto bad;
 read=same(argv[1],"get")||same(argv[1],"socget")||same(argv[1],"9300get");
 ram=same(argv[1],"flashget")||same(argv[1],"flashset");
 if(!read&&!ram&&!same(argv[1],"set")&&!same(argv[1],"socset")&&!same(argv[1],"9300set"))goto bad;
 if(argc!=(read?3:4)||!number(argv[2],&address)||(address&3))goto bad;
 if(argc==4&&!number(argv[3],&value))goto bad;
 if(ram){
  /* Despite its name, stock flashget/set ORs the offset with BF000000.
   * Limit this operation to the actually mapped 128 KiB SRAM window. */
  if(address>0x1fffcu)goto bad;
  if(same(argv[1],"flashget")){
   if(value>64u||(value&&value>(0x20000u-address)/4u))goto bad;
   read=1;
  }
 }else if(address>0xffffu)goto bad;
 if(!read&&tagged(STATE)){fw_printf("reg: writes blocked during cool test; cool auto first\n");return 1;}
 return fw_cli_reg(cmd,flags,argc,argv);
bad:
 fw_printf("reg: rejected incomplete/invalid arguments or address/count\n");return 1;
}
static int help(const struct command *cmd,int flags,int argc,char **argv){
 int result=fw_cli_help(cmd,flags,argc,argv);
 if(argc==1)fw_printf("cool    - status / test 0 / test 1 / auto (GPIO27, bounded)\n");
 return result;
}
static const struct command cool_command={"cool",3,0,cool,"cool status | cool test 0 | cool test 1 | cool auto"};
static const struct command reg_command={"reg",4,0,reg_guard,"reg - guarded register access"};
static const struct command help_command={"help",16,1,help,"help - print online help"};
static const struct command alias_command={"?",16,1,help,"? - alias for help"};
const struct command *sg_cli_lookup(const char *name){
 if(same(name,"cool"))return &cool_command;
 const struct command *c=fw_cli_lookup(name);
 if(c&&c->run==fw_cli_reg)return &reg_command;
 if(c&&c->run==fw_cli_help)return same(name,"?")?&alias_command:&help_command;
 return c;
}
