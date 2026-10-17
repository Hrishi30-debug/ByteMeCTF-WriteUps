#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void soul_stone(void) {
    printf("\n[+] Soul Stone unlocked!\n");
    printf("OWASP{S0ul_St0ne_Buff3r_0v3rfl0w}\n");
    fflush(stdout);
}

void vault(void) {
    char name[32];

    printf("=================================\n");
    printf("       SOUL STONE VAULT\n");
    printf("=================================\n");
    printf("Enter your name: ");
    fflush(stdout);

    gets(name);

    printf("\nHello, %s!\n", name);
    printf("The Soul Stone remains sealed...\n");
    fflush(stdout);
}

int main(void) {
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    vault();

    return 0;
}
