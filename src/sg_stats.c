#include "sg_stats.h"
#define COUNT(a) (sizeof(a)/sizeof((a)[0]))
enum format { F_NULL,F_COUNTER,F_BOOL,F_TEXT,F_NUMBER,F_UINT };
enum rule { R_NONE,R_SPEED,R_DUPLEX,R_LIMIT,R_CLASS,R_U32 };
struct field { const char *name; enum sg_field id; enum format format; enum rule rule; size_t max_bytes; };
#include "sg_fields.inc"
struct writer { const struct sg_sink *sink; struct sg_result *result; size_t used; int failed; char buffer[SG_JSON_BUFFER_SIZE]; };
static size_t slen(const char *s){size_t n=0;while(s[n])n++;return n;}
static int flush(struct writer *w){
 size_t off=0;
 if(w->failed)return -1;
 while(off<w->used){
  int n=w->sink->write(w->sink->context,w->buffer+off,w->used-off);
  if(n<=0||(size_t)n>w->used-off){w->failed=1;return -1;}
  off+=(size_t)n;w->result->bytes_accepted+=(size_t)n;
 }
 w->used=0;return 0;
}
static int byte(struct writer *w,char c){if(w->failed)return -1;if(w->used==sizeof w->buffer&&flush(w))return -1;w->buffer[w->used++]=c;return 0;}
static int text(struct writer *w,const char *s){while(*s){if(byte(w,*s++))return -1;}return 0;}
/* Strict UTF-8, rejects overlong encodings, surrogates and >U+10ffff. */
static int utf8(const char *s,size_t n){
 size_t i=0;
 while(i<n){uint32_t cp;unsigned rest;unsigned char c=(unsigned char)s[i++];
  if(c<0x80)continue;
  if(c>=0xc2&&c<=0xdf){cp=c&31;rest=1;}
  else if(c>=0xe0&&c<=0xef){cp=c&15;rest=2;}
  else if(c>=0xf0&&c<=0xf4){cp=c&7;rest=3;}
  else return 0;
  unsigned total=rest;if(rest>n-i)return 0;
  while(rest--){c=(unsigned char)s[i++];if((c&0xc0)!=0x80)return 0;cp=(cp<<6)|(c&63);}
  if((total==2&&cp<0x800)||(total==3&&cp<0x10000)||cp>0x10ffff||(cp>=0xd800&&cp<=0xdfff))return 0;
 }return 1;
}
static int quoted(struct writer *w,const char *s,size_t n){
 static const char hex[]="0123456789abcdef";
 if(byte(w,'"'))return -1;
 for(size_t i=0;i<n;i++){unsigned char c=(unsigned char)s[i];
  if(c=='"'||c=='\\'){if(byte(w,'\\')||byte(w,(char)c))return -1;}
  else if(c<32){if(text(w,"\\u00")||byte(w,hex[c>>4])||byte(w,hex[c&15]))return -1;}
  else if(byte(w,(char)c))return -1;
 }return byte(w,'"');
}
/* Base-256 long division needs only 32-bit arithmetic, including on MIPS o32.
   Avoid implicit libgcc 64-bit divide helpers in the freestanding payload. */
static unsigned decimal_step(uint64_t *value){
 uint32_t hi=(uint32_t)(*value>>32),lo=(uint32_t)*value;
 uint32_t qhi=hi/10u,rem=hi%10u,qlo=0;
 for(unsigned n=0;n<4;n++){
  uint32_t part=(rem<<8)|(lo>>24);lo<<=8;
  qlo=(qlo<<8)|(part/10u);rem=part%10u;
 }
 *value=((uint64_t)qhi<<32)|qlo;return rem;
}
static int number(struct writer *w,uint64_t value){char digits[20];size_t n=0;do{digits[n++]=(char)('0'+decimal_step(&value));}while(value);while(n){if(byte(w,digits[--n]))return -1;}return 0;}
static int equals(const struct sg_value *v,const char *s){size_t n=slen(s);if(v->length!=n)return 0;for(size_t i=0;i<n;i++)if(v->text[i]!=s[i])return 0;return 1;}
static int valid(const struct field *f,const struct sg_value *v){
 if(v->kind==SG_NULL)return 1;
 if(f->format==F_TEXT){
  if(v->kind!=SG_TEXT||!v->text||v->length>f->max_bytes||!utf8(v->text,v->length))return 0;
  if(f->rule==R_DUPLEX)return equals(v,"half")||equals(v,"full");
  if(f->rule==R_LIMIT)return equals(v,"auto")||equals(v,"fixed");
  return 1;
 }
 if(f->format==F_BOOL)return v->kind==SG_BOOL&&v->number<=1;
 if(f->format==F_NUMBER){if(v->kind!=SG_UINT&&v->kind!=SG_TENTHS)return 0;}
 else if(v->kind!=SG_UINT)return 0;
 if(f->rule==R_SPEED)return v->number==10||v->number==100||v->number==1000;
 if(f->rule==R_CLASS)return v->number<=4;
 if(f->rule==R_U32)return v->number<=UINT32_MAX;
 return 1;
}
static int value(struct writer *w,const struct sg_source *s,const struct field *f){
 struct sg_value v={SG_NULL,0,0,0};
 if(f->format==F_NULL)return text(w,"null");
 if(s->get(s->context,f->id,&v)!=0){w->result->unavailable_fields++;v.kind=SG_NULL;}
 if(!valid(f,&v)){w->result->invalid_fields++;v.kind=SG_NULL;}
 if(v.kind==SG_NULL)return text(w,"null");
 if(v.kind==SG_TEXT)return quoted(w,v.text,v.length);
 if(v.kind==SG_BOOL)return text(w,v.number?"true":"false");
 if(f->format==F_COUNTER){if(byte(w,'"')||number(w,v.number))return -1;return byte(w,'"');}
 if(v.kind==SG_TENTHS){unsigned rem=decimal_step(&v.number);if(number(w,v.number)||byte(w,'.'))return -1;return byte(w,(char)('0'+rem));}
 return number(w,v.number);
}
static int fields(struct writer *w,const struct sg_source *s,const struct field *f,size_t n){
 for(size_t i=0;i<n;i++){
  if(i&&byte(w,','))return -1;
  if(quoted(w,f[i].name,slen(f[i].name))||byte(w,':')||value(w,s,&f[i]))return -1;
 }return 0;
}
#define FIELDS(w,s,g) fields(w,s,g##_fields,COUNT(g##_fields))
int sg_stats_emit(const struct sg_source *s,const struct sg_sink *sink,struct sg_result *result){
 struct writer w;
 if(!s||!sink||!result||!s->begin||!s->get||!s->has_poe||!sink->write||!sink->finish)return -3;
 *result=(struct sg_result){0,0,0};w=(struct writer){.sink=sink,.result=result,.used=0,.failed=0};
 if(s->begin(s->context,SG_SYSTEM,0))return -2;
 if(text(&w,"{\"schema_version\":1,\"system\":{")||FIELDS(&w,s,system)||text(&w,"},\"poe\":{"))return -1;
 if(s->begin(s->context,SG_GLOBAL_POE,0))return -2;
 if(FIELDS(&w,s,global_poe)||text(&w,"},\"ports\":["))return -1;
 for(unsigned port=1;port<=SG_PORTS;port++){
  if(s->begin(s->context,SG_PORT,port))return -2;
  int has_poe=s->has_poe(s->context);if(has_poe!=0&&has_poe!=1)return -2;
  if((port>1&&byte(&w,','))||text(&w,"{\"port\":")||number(&w,port)||byte(&w,',')||FIELDS(&w,s,port)||text(&w,",\"counters\":{"))return -1;
  if(FIELDS(&w,s,counter)||text(&w,"},\"poe\":"))return -1;
  if(has_poe){
   if(byte(&w,'{')||FIELDS(&w,s,poe)||text(&w,",\"recovery\":{")||FIELDS(&w,s,recovery)||text(&w,"}}"))return -1;
  }else if(text(&w,"null"))return -1;
  if(byte(&w,'}'))return -1;
 }
 if(text(&w,"],\"loop_prevention\":{"))return -1;
 if(s->begin(s->context,SG_LOOP,0))return -2;
 if(FIELDS(&w,s,loop)||byte(&w,'}'))return -1;
#ifdef SG_COOLING
 if(s->begin(s->context,SG_COOLING_SCOPE,0))return -2;
 if(text(&w,",\"cooling\":{")||FIELDS(&w,s,cooling)||byte(&w,'}'))return -1;
#endif
 if(byte(&w,'}')||flush(&w))return -1;
 return sink->finish(sink->context)==0?0:-1;
}
