#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
typedef uint64_t u64;
static u64 T;static int N=6,G;static u64 w[32];static int gi[32],gj[32],go[32];static int used[32];
static long long nodes=0;
static int edges[9][2]={{0,1},{1,2},{0,2},{3,4},{4,5},{3,5},{0,3},{1,4},{2,5}};
static void found(int n){printf("FOUND size %d\n",n-N);for(int k=N;k<n;k++)printf(" g%d = %s(w%d,w%d)\n",k,go[k]?"OR":"AND",gi[k],gj[k]);fflush(stdout);exit(0);}
static void dfs(int n){ // n wires present
  nodes++;
  int r=G-(n-N); // remaining gates
  int U=0;for(int k=0;k<n;k++)if(!used[k])U++;
  if(U-r>1)return;
  if(r==0)return;
  for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)for(int op=0;op<2;op++){
    if(n>N && i!=n-1 && j!=n-1){ // canonical order vs previous gate
      int pi=gi[n-1],pj=gj[n-1],po=go[n-1];
      if(j<pj || (j==pj && (i<pi || (i==pi && op<po))))continue;
    }
    u64 t=op?(w[i]|w[j]):(w[i]&w[j]);
    int dup=0;for(int k=0;k<n;k++)if(w[k]==t){dup=1;break;}
    if(dup)continue;
    int nU=U-(!used[i])-(!used[j])+1;
    if(nU-(r-1)>1)continue;
    if(r==1){ if(t==T && nU==1){w[n]=t;gi[n]=i;gj[n]=j;go[n]=op;found(n+1);} continue;}
    w[n]=t;gi[n]=i;gj[n]=j;go[n]=op;int ui=used[i],uj=used[j];used[i]++;used[j]++;used[n]=0;
    dfs(n+1);used[i]--;used[j]--;
  }
}
int main(int c,char**v){G=atoi(v[1]);
  for(int k=0;k<N;k++){w[k]=0;for(int x=0;x<64;x++)if(x>>k&1)w[k]|=1ULL<<x;}
  T=0;for(int x=0;x<64;x++){int f=0;for(int e=0;e<9;e++)if((x>>edges[e][0]&1)&&(x>>edges[e][1]&1))f=1;if(f)T|=1ULL<<x;}
  for(int k=0;k<32;k++)used[k]=0;
  dfs(N);printf("NONE at size %d, nodes %lld\n",G,nodes);}
