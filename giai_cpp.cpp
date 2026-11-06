#include <bits/stdc++.h>
using namespace std;
typedef unsigned long long u64; typedef uint16_t u16;
int K,NT; const int CAP=4, UNK=15;
struct Key{u64 w[4]; bool operator==(const Key&o)const{return !memcmp(w,o.w,32);}};
struct St{ int t[16][4]; int len[16]; };
static inline u64 H(const Key&k){u64 h=1469598103934665603ULL;for(int i=0;i<4;i++){h^=k.w[i];h*=0x9E3779B97F4A7C15ULL;h^=h>>29;}return h;}
Key encode(const St&s){u16 c[16];for(int i=0;i<NT;i++){u16 x=0;for(int j=0;j<s.len[i];j++)x|=s.t[i][j]<<(4*j);c[i]=x;}
 sort(c,c+NT);Key k;memset(k.w,0,32);for(int i=0;i<NT;i++)k.w[i/4]|=(u64)c[i]<<(16*(i%4));return k;}
St decode(const Key&k){St s;for(int i=0;i<NT;i++){u16 x=(k.w[i/4]>>(16*(i%4)))&0xFFFF;int l=0;for(int j=0;j<4;j++){int v=(x>>(4*j))&15;s.t[i][j]=v;if(v)l=j+1;}s.len[i]=l;}return s;}
vector<Key> keys; vector<uint32_t> tab; u64 mask; size_t LIM;
int64_t findk(const Key&k,bool ins){u64 h=H(k)&mask;while(tab[h]!=UINT32_MAX){if(keys[tab[h]]==k)return tab[h];h=(h+1)&mask;}
 if(!ins)return -1; if(keys.size()>=LIM){fprintf(stderr,"LIMIT\n");exit(2);} tab[h]=keys.size();keys.push_back(k);return keys.size()-1;}
bool isdone(const St&s){for(int i=0;i<NT;i++){if(!s.len[i])continue;if(s.len[i]!=4)return false;for(int j=0;j<4;j++)if(s.t[i][j]!=s.t[i][0]||s.t[i][j]==UNK)return false;}return true;}
struct Move{int a,b;};
int genmoves(const St&s,Move*m){int n=0;for(int a=0;a<NT;a++){int la=s.len[a];if(!la)continue;int c=s.t[a][la-1];if(c==UNK)continue;int r=1;while(r<la&&s.t[a][la-1-r]==c)r++;
 if(r==la&&r==4)continue;bool ed=false;for(int b=0;b<NT;b++){if(a==b||s.len[b]>=4)continue;if(s.len[b]){if(s.t[b][s.len[b]-1]!=c)continue;}else{if(r==la||ed)continue;ed=true;}m[n++]={a,b};}}return n;}
St pour(const St&s,int a,int b){St x=s;int la=x.len[a];int c=x.t[a][la-1];int r=1;while(r<la&&x.t[a][la-1-r]==c)r++;int mm=min(r,4-x.len[b]);
 for(int i=0;i<mm;i++){x.t[b][x.len[b]++]=c;x.t[a][--x.len[a]]=0;}return x;}
void poolof(const St&s,int*p){for(int c=1;c<=K;c++)p[c]=4;for(int i=0;i<NT;i++)for(int j=0;j<s.len[i];j++)if(s.t[i][j]!=UNK)p[s.t[i][j]]--;}
// successors: calls f(kind,prob,idx)
template<class F> void succs(const St&s,F f){Move m[256];int n=genmoves(s,m);int p[16];poolof(s,p);int tot=0;for(int c=1;c<=K;c++)tot+=p[c];
 for(int i=0;i<n;i++){St x=pour(s,m[i].a,m[i].b);int a=m[i].a;
  if(x.len[a]&&x.t[a][x.len[a]-1]==UNK){f(i,'r',m[i],x,tot,p);} else f(i,'o',m[i],x,tot,p);}}
int main(int argc,char**argv){
 FILE*fi=fopen(argv[1],"r");fscanf(fi,"%d %d",&K,&NT);St s0;memset(&s0,0,sizeof s0);for(int i=0;i<NT;i++){fscanf(fi,"%d",&s0.len[i]);for(int j=0;j<s0.len[i];j++)fscanf(fi,"%d",&s0.t[i][j]);}
 LIM=atoll(argv[2]);u64 sz=1;while(sz<LIM*2)sz<<=1;tab.assign(sz,UINT32_MAX);mask=sz-1;keys.reserve(min<size_t>(LIM,1<<20));
 findk(encode(s0),true);
 for(size_t i=0;i<keys.size();i++){St s=decode(keys[i]);if(isdone(s))continue;
  succs(s,[&](int,char kind,Move m,St&x,int tot,int*p){
   if(kind=='o')findk(encode(x),true);
   else{int a=m.a;for(int c=1;c<=K;c++){if(p[c]<=0)continue;St y=x;y.t[a][y.len[a]-1]=c;findk(encode(y),true);}}});
  if(i%2000000==0)fprintf(stderr,"explored %zu/%zu\n",i,keys.size());}
 size_t N=keys.size();printf("states %zu\n",N);fflush(stdout);
 vector<uint8_t> done(N),win(N);vector<float> P(N,0);
 for(size_t i=0;i<N;i++){St s=decode(keys[i]);done[i]=isdone(s);win[i]=done[i];P[i]=done[i];}
 // value evaluation helper
 auto val=[&](const St&x,char kind,Move m,int tot,int*p,bool&allwin)->double{
  if(kind=='o'){size_t j=findk(encode(x),false);allwin=win[j];return P[j];}
  double v=0;allwin=true;int a=m.a;for(int c=1;c<=K;c++){if(p[c]<=0)continue;St y=x;y.t[a][y.len[a]-1]=c;size_t j=findk(encode(y),false);v+=(double)p[c]/tot*P[j];if(!win[j])allwin=false;}return v;};
 bool ch=true;int it=0;
 while(ch){ch=false;for(size_t ii=N;ii-->0;){if(win[ii])continue;St s=decode(keys[ii]);bool w=false;
   succs(s,[&](int,char kind,Move m,St&x,int tot,int*p){if(w)return;bool aw;val(x,kind,m,tot,p,aw);if(aw)w=true;});
   if(w){win[ii]=1;ch=true;}}fprintf(stderr,"win sweep %d\n",++it);}
 printf("WIN_CERTAIN %d\n",(int)win[0]);fflush(stdout);
 for(it=0;it<5000;it++){double d=0;for(size_t ii=N;ii-->0;){if(done[ii])continue;St s=decode(keys[ii]);double b=P[ii];
   succs(s,[&](int,char kind,Move m,St&x,int tot,int*p){bool aw;double v=val(x,kind,m,tot,p,aw);if(v>b)b=v;});
   if(b>P[ii]+1e-9){d=max(d,b-P[ii]);P[ii]=b;}}
  fprintf(stderr,"P sweep %d d=%g P0=%f\n",it,d,P[0]);if(d<1e-7)break;}
 printf("PROB %.4f\n",P[0]);
 // BFS along optimal moves to next reveal
 deque<pair<St,vector<Move>>> q;set<array<u64,4>> vis;q.push_back({s0,{}});
 vector<Move> found;bool ok=false;
 while(!q.empty()&&!ok){auto cur=q.front();q.pop_front();St s=cur.first;if(isdone(s))continue;
  vector<tuple<double,Move,St,char>> em;
  succs(s,[&](int,char kind,Move m,St&x,int tot,int*p){bool aw;double v=val(x,kind,m,tot,p,aw);em.push_back({v,m,x,kind});});
  double top=0;for(auto&e:em)top=max(top,get<0>(e));
  for(auto&e:em){if(get<0>(e)<top-1e-6)continue;auto path=cur.second;path.push_back(get<1>(e));
   if(get<3>(e)=='r'){found=path;ok=true;break;}
   Key k=encode(get<2>(e));array<u64,4> kk={k.w[0],k.w[1],k.w[2],k.w[3]};if(vis.insert(kk).second)q.push_back({get<2>(e),path});}}
 printf("PATH");for(auto&m:found)printf(" %d %d",m.a+1,m.b+1);printf("\n");
}
