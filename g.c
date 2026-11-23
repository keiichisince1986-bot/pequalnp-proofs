// exhaustive fan-in-2 AND/OR/NOT circuits of exactly size G computing T on N inputs; count those with/without NOT
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
typedef uint64_t u64;
static u64 T,MASK;static int N,G;static u64 w[40];static int gi[40],gj[40],go[40],used[40];
static long long cnt[2];static int printed=0;
static void report(int n){int hasnot=0;for(int k=N;k<n;k++)if(go[k]==2)hasnot=1;cnt[hasnot]++;
 if(hasnot&&printed<3){printed++;printf("NOT-circuit:");for(int k=N;k<n;k++){if(go[k]==2)printf(" g%d=NOT(w%d)",k,gi[k]);else printf(" g%d=%s(w%d,w%d)",k,go[k]?"OR":"AND",gi[k],gj[k]);}printf("\n");}}
static int key(int i,int j,int op){return (j*64+i)*3+op;}
static void dfs(int n){
  int r=G-(n-N);int U=0;for(int k=0;k<n;k++)if(!used[k])U++;
  if(U-r>1||r==0)return;
  for(int op=0;op<3;op++)for(int j=0;j<n;j++)for(int i=(op==2?j:0);i<(op==2?j+1:j);i++){
    if(n>N && i!=n-1 && j!=n-1){int pk=key(gi[n-1],gj[n-1],go[n-1]);if(key(i,j,op)<pk)continue;}
    u64 t= op==2? (~w[j])&MASK : op? (w[i]|w[j]) : (w[i]&w[j]);
    int dup=0;for(int k=0;k<n;k++)if(w[k]==t){dup=1;break;}
    if(dup)continue;
    int nU=U-(!used[j])-(op!=2 && !used[i])+1; if(nU-(r-1)>1)continue;
    gi[n]=i;gj[n]=j;go[n]=op;w[n]=t;
    if(r==1){if(t==T&&nU==1)report(n+1);continue;}
    used[j]++;if(op!=2)used[i]++;used[n]=0;dfs(n+1);used[j]--;if(op!=2)used[i]--;
  }
}
int main(int c,char**v){N=atoi(v[1]);G=atoi(v[2]);MASK=(N==6)?~0ULL:((1ULL<<(1<<N))-1);
 // edges as "ab" pairs in argv[3], A as digits in argv[4]
 int A[8]={0};for(char*p=v[4];*p;p++)if(*p!='-')A[*p-'0']=1;
 T=0;for(int x=0;x<(1<<N);x++){int f=0;for(int a=0;a<N;a++)if(A[a]&&(x>>a&1))f=1;
   for(char*p=v[3];p[0]&&p[1];p+=3)if((x>>(p[0]-'0')&1)&&(x>>(p[1]-'0')&1))f=1; if(f)T|=1ULL<<x;}
 for(int k=0;k<N;k++){w[k]=0;for(int x=0;x<(1<<N);x++)if(x>>k&1)w[k]|=1ULL<<x;}
 memset(used,0,sizeof used);
 for(G=1;G<=atoi(v[2]);G++){cnt[0]=cnt[1]=0;dfs(N);if(cnt[0]+cnt[1]){printf("%s A=%s min=%d monotone=%lld withNOT=%lld\n",v[3],v[4],G,cnt[0],cnt[1]);return 0;}}
 printf("%s none<=%s\n",v[3],v[2]);}
