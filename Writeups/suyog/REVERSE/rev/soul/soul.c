#include <stdio.h>
#include <string.h>

void soul_stone(void) {
    unsigned char encoded[] = {
        0x4f, 0x57, 0x41, 0x53, 0x50,
        0x7b, 0x74, 0x68, 0x33, 0x5f,
        0x73, 0x30, 0x75, 0x6c, 0x5f,
        0x73, 0x74, 0x30, 0x6e, 0x33,
        0x5f, 0x77, 0x68, 0x31, 0x73,
        0x70, 0x33, 0x72, 0x7d
    };

    char flag[64];

    for (int i = 0; i < sizeof(encoded); i++)
        flag[i] = encoded[i];

    flag[sizeof(encoded)] = '\0';

    printf("\n[+] The stone recognizes your soul.\n");
    printf("[+] Access granted.\n\n");
    printf("Flag: %s\n", flag);
}

int main(void) {
    char input[64];

    printf("====================================\n");
    printf("        SOUL STONE VAULT\n");
    printf("====================================\n\n");

    printf("The Soul Stone remembers everything...\n\n");
    printf("Enter the secret phrase: ");

    scanf("%63s", input);

    char expected[] = "soul";

    if (strcmp(input, expected) == 0) {
        soul_stone();
    } else {
        printf("\n[-] The stone rejects your soul.\n");
    }

    return 0;
}
