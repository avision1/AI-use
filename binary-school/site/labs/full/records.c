#include <stdio.h>
#include <stddef.h>
struct Item{
char tag;
int count;
short code;
}
;

struct Node{
int value;
struct Node *next;
}
;

int score(const struct Item *p){
return p->count+p->code;
}

int sum_counts(const struct Item *a,int n){
int s=0;
for(int i=0;
i<n;
i++)s+=a[i].count;
return s;
}

int total(struct Node *p){
int s=0;
while(p){
s+=p->value;
p=p->next;
}
return s;
}

int main(void){
struct Item a[3]={
{
'A',3,4}
,{
'B',5,6}
,{
'C',7,8}
}
;
struct Node b={
4,0}
,c={
2,&b}
;
printf("Item.size=%zu count.offset=%zu code.offset=%zu\n",sizeof(struct Item),offsetof(struct Item,count),offsetof(struct Item,code));
printf("Node.size=%zu next.offset=%zu\n",sizeof(struct Node),offsetof(struct Node,next));
printf("score=%d sum=%d linked=%d\n",score(&a[0]),sum_counts(a,3),total(&c));
return 0;
}

