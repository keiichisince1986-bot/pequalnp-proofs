/*
  T2 / L-meta-618 independent re-check (Antigravity-Mac).

  Question: is there a circuit of fan-in-2 AND/OR gates with at most 8 gates computing, on 6
  inputs, the edge function of the triangular prism (edges 01 12 02 34 45 35 03 14 25)?

  Method (different from s.c): depth-first search over straight-line programs whose wires are
  evaluated only on the 22 inputs of weight <= 2 (empty set, 6 singletons, 15 pairs).
  This is a relaxation: a circuit correct on all 64 inputs is correct on these 22, so
  "no program of size s matches on the 22 points" implies "no circuit of size s exists".

  A smallest matching program can be assumed to have:
    - no gate equal (on the 22 points) to an earlier wire, and no constant-false gate
      (both can be deleted, consumers simplified, size shrinks);
    - no gate reading one wire twice, no constant or one-input gate (they are copies or
      constants, deletable likewise);
    - every gate except the output read by a later gate (otherwise delete it);
    - gates ordered by the greedy topological order that always picks the available gate
      with the smallest truth table; in that order, if gate i+1 does not read gate i then
      tt(gate i) < tt(gate i+1).
  So for each size s = 1..8 we search exactly such programs with output = last gate = target.
  Pruning: with u gates unread after placing gate k and r = s - (k+1) gates left, need u - 1 <= r.

  Usage: prism_dfs <s> <first-choice index or -1 for all>
*/
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#define NIN 6
#define MAXW 32

static uint32_t tt[MAXW];
static int ga[MAXW], gb[MAXW], gop[MAXW];
static int reads[MAXW];
static int S;
static uint32_t T;
static long long nodes = 0, found = 0;
static int pidx[NIN][NIN];

static void print_prog(void) {
  printf("FOUND size %d:", S);
  for (int k = 0; k < S; k++) {
    int w = NIN + k;
    printf(" w%d=%s(w%d,w%d)", w, gop[w] ? "OR" : "AND", ga[w], gb[w]);
  }
  printf("\n");
  fflush(stdout);
}

static inline void try_last(int k, int a, int b) {
  int nw = NIN + k;
  uint32_t ta = tt[a], tb = tt[b];
  int prev = nw - 1;
  for (int op = 0; op < 2; op++) {
    uint32_t t = op ? (ta | tb) : (ta & tb);
    if (t != T) continue;
    if (k >= 1 && a != prev && b != prev && !(t > tt[prev])) continue;
    nodes++;
    tt[nw] = t; ga[nw] = a; gb[nw] = b; gop[nw] = op;
    found++;
    print_prog();
  }
}

static void dfs(int k, int unread, int first_choice) {
  int nw = NIN + k;
  int r = S - (k + 1);
  if (r == 0) {
    /* Last gate: must reduce unread to 1 (meaning u = 1), so must read all unread gates. */
    int ulist[2], uc = 0;
    for (int w = NIN; w < nw; w++) {
      if (reads[w] == 0) {
        if (uc < 2) ulist[uc] = w;
        uc++;
      }
    }
    if (uc == 2) {
      int a = ulist[0], b = ulist[1];
      if (a > b) { int tmp = a; a = b; b = tmp; }
      try_last(k, a, b);
    } else if (uc == 1) {
      int u = ulist[0];
      for (int w = 0; w < nw; w++) {
        if (w == u) continue;
        int a = w < u ? w : u;
        int b = w < u ? u : w;
        try_last(k, a, b);
      }
    } else if (uc == 0) {
      for (int a = 0; a < nw; a++)
        for (int b = a + 1; b < nw; b++)
          try_last(k, a, b);
    }
    return;
  }

  /* Need u <= r + 1, where u = unread + 1 - deg_unread, so deg_unread >= unread - r. */
  int need_unread = unread - r;
  int choice = 0;
  for (int a = 0; a < nw; a++) {
    int ra = (a >= NIN && reads[a] == 0) ? 1 : 0;
    if (need_unread == 2 && !ra) continue;
    for (int b = a + 1; b < nw; b++) {
      int rb = (b >= NIN && reads[b] == 0) ? 1 : 0;
      if (ra + rb < need_unread) continue;
      for (int op = 0; op < 2; op++, choice++) {
        if (k == 0 && first_choice >= 0 && choice != first_choice) continue;
        uint32_t t = op ? (tt[a] | tt[b]) : (tt[a] & tt[b]);
        if (t == 0) continue;
        int dup = 0;
        for (int w = 0; w < nw; w++) if (tt[w] == t) { dup = 1; break; }
        if (dup) continue;
        if (k >= 1) {
          int prev = nw - 1;
          if (a != prev && b != prev && !(t > tt[prev])) continue;
        }
        int u = unread + 1 - ra - rb;
        nodes++;
        tt[nw] = t; ga[nw] = a; gb[nw] = b; gop[nw] = op; reads[nw] = 0;
        reads[a]++; reads[b]++;
        dfs(k + 1, u, first_choice);
        reads[a]--; reads[b]--;
      }
    }
  }
}

int main(int argc, char **argv) {
  if (argc < 3) { fprintf(stderr, "usage: %s s first_choice\n", argv[0]); return 1; }
  S = atoi(argv[1]);
  int fc = atoi(argv[2]);
  int bit = 7;
  for (int i = 0; i < NIN; i++) for (int j = i + 1; j < NIN; j++) pidx[i][j] = pidx[j][i] = bit++;
  for (int i = 0; i < NIN; i++) {
    uint32_t m = 1u << (1 + i);
    for (int j = 0; j < NIN; j++) if (j != i) m |= 1u << pidx[i][j];
    tt[i] = m;
    reads[i] = 0;
  }
  int E[9][2] = {{0,1},{1,2},{0,2},{3,4},{4,5},{3,5},{0,3},{1,4},{2,5}};
  T = 0;
  for (int e = 0; e < 9; e++) T |= 1u << pidx[E[e][0]][E[e][1]];
  dfs(0, 0, fc);
  printf("DONE size %d first_choice %d nodes %lld found %lld\n", S, fc, nodes, found);
  return 0;
}
