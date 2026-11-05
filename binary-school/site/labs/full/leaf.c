int plus_two(int x){
return x+2;
}

int read_at(int *p,int i){
return p[i];
}

int signed_less(int a,int b){
return a<b;
}

int unsigned_less(unsigned a,unsigned b){
return a<b;
}

int quotient(int x){
return x/5;
}

int remainder(int x){
return x%5;
}

struct Node{
int value;
struct Node *next;
}
;

int node_value(struct Node *p){
return p->value;
}

struct Node *node_next(struct Node *p){
return p->next;
}

