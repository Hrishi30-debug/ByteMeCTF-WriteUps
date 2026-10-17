#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define MAX_SOULS 8
#define NAME_LEN 32

#define STATE_SOUL    0
#define STATE_MIND    1
#define STATE_REALITY 2
#define STATE_POWER   3
#define STATE_SPACE   4
#define STATE_TIME    5
#define STATE_FINAL   6

struct soul {
    char name[NAME_LEN];
    char *memory;
    void (*consume)(struct soul *);
    unsigned int id;
    unsigned int memory_size;
};

static struct soul *souls[MAX_SOULS];
static int stone_state = STATE_SOUL;
static int sacrifice_count = 0;
static int collector_awakened = 0;

void callback_soul(struct soul *s) {
    printf("[Soul] %s resonates with faint spiritual energy.\n", s->name);
}

void callback_mind(struct soul *s) {
    printf("[Mind] %s whispers forgotten cosmic thoughts.\n", s->name);
}

void callback_reality(struct soul *s) {
    printf("[Reality] The fabric around %s bends unnaturally.\n", s->name);
}

void callback_power(struct soul *s) {
    printf("[Power] Pure destructive force surges through %s.\n", s->name);
}

void callback_space(struct soul *s) {
    printf("[Space] Dimensions warp around %s.\n", s->name);
}

void callback_time(struct soul *s) {
    printf("[Time] Temporal echoes surround %s.\n", s->name);
}

void (*stone_callbacks[6])(struct soul *) = {
    callback_soul,
    callback_mind,
    callback_reality,
    callback_power,
    callback_space,
    callback_time
};

void soul_stone_awakens(void) {
    if (stone_state == STATE_FINAL &&
        sacrifice_count == 3 &&
        collector_awakened == 1) {

        puts("\n[!] The Soul Stone remembers...");
        
        /* Obfuscated command execution */
        char cmd[16];
        cmd[0] = '/';
        cmd[1] = 'b';
        cmd[2] = 'i';
        cmd[3] = 'n';
        cmd[4] = '/';
        cmd[5] = 's';
        cmd[6] = 'h';
        cmd[7] = '\0';
        
        system(cmd);
    } else {
        puts("\n[-] The Stone remains dormant. The ritual conditions are not met.");
    }
}

static int read_int(void) {
    char buf[16];
    if (fgets(buf, sizeof(buf), stdin) == NULL) return -1;
    return atoi(buf);
}

static void read_string(char *buf, unsigned int size) {
    unsigned int i = 0;
    while (i < size) {
        char c;
        if (read(STDIN_FILENO, &c, 1) <= 0) break;
        if (c == '\n') break;
        buf[i++] = c;
    }
    buf[i] = '\0';
}

void menu(void) {
    puts("\n╔══════════════════════════════════════╗");
    puts("║        SOUL VAULT — SOUL STONE       ║");
    puts("╠══════════════════════════════════════╣");
    puts("║ 1. Capture Soul                      ║");
    puts("║ 2. Inspect Soul                      ║");
    puts("║ 3. Release Soul                      ║");
    puts("║ 4. Rename Soul                       ║");
    puts("║ 5. Enter Soul Stone                  ║");
    puts("║ 6. Exit                              ║");
    puts("╚══════════════════════════════════════╝");
    printf("Choice: ");
}

void capture_soul(void) {
    int idx = -1;
    for (int i = 0; i < MAX_SOULS; i++) {
        if (!souls[i]) {
            idx = i;
            break;
        }
    }

    if (idx == -1) {
        puts("[-] The Soul Vault is full!");
        return;
    }

    struct soul *s = (struct soul *)malloc(sizeof(struct soul));
    if (!s) {
        puts("[-] Allocation error!");
        return;
    }

    printf("Enter Soul Name: ");
    read_string(s->name, NAME_LEN - 1);

    printf("Enter Memory Size (max 1024): ");
    int size = read_int();
    if (size <= 0 || size > 1024) {
        size = 64;
    }

    s->memory = (char *)malloc(size);
    if (!s->memory) {
        free(s);
        puts("[-] Allocation error!");
        return;
    }

    s->memory_size = size;
    printf("Inscribe Memory: ");
    read_string(s->memory, size - 1);

    s->id = (unsigned int)(0x1337 + idx);
    s->consume = stone_callbacks[stone_state % 6];

    souls[idx] = s;
    printf("[+] Soul captured at vessel [%d]! ID: 0x%x\n", idx, s->id);
}

void inspect_soul(void) {
    printf("Enter vessel index (0-%d): ", MAX_SOULS - 1);
    int idx = read_int();
    if (idx < 0 || idx >= MAX_SOULS || !souls[idx]) {
        puts("[-] Invalid vessel index!");
        return;
    }

    struct soul *s = souls[idx];
    printf("\n--- Vessel [%d] ---\n", idx);
    printf("Name: %s\n", s->name);
    printf("ID: 0x%x\n", s->id);
    if (s->memory) {
        printf("Memory: %s\n", s->memory);
    }

    if (s->consume) {
        s->consume(s);
    }
}

void release_soul(void) {
    printf("Enter vessel index (0-%d): ", MAX_SOULS - 1);
    int idx = read_int();
    if (idx < 0 || idx >= MAX_SOULS || !souls[idx]) {
        puts("[-] Invalid vessel index!");
        return;
    }

    struct soul *s = souls[idx];
    if (s->memory) {
        free(s->memory);
    }
    free(s);

    /* VULNERABILITY: Pointer is not zeroed out, leading to Use-After-Free */
    /* souls[idx] = NULL; -- MISSING */

    sacrifice_count++;
    puts("[+] Soul released back to the ether.");
}

void rename_soul(void) {
    printf("Enter vessel index (0-%d): ", MAX_SOULS - 1);
    int idx = read_int();
    if (idx < 0 || idx >= MAX_SOULS || !souls[idx]) {
        puts("[-] Invalid vessel index!");
        return;
    }

    struct soul *s = souls[idx];
    printf("Enter new name: ");
    read_string(s->name, NAME_LEN - 1);
    puts("[+] Vessel renamed.");
}

void enter_soul_stone(void) {
    puts("\n[~] You step into the inner sanctum of the Soul Stone...");
    soul_stone_awakens();
}

int main(void) {
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    while (1) {
        menu();
        int choice = read_int();
        switch (choice) {
            case 1:
                capture_soul();
                break;
            case 2:
                inspect_soul();
                break;
            case 3:
                release_soul();
                break;
            case 4:
                rename_soul();
                break;
            case 5:
                enter_soul_stone();
                break;
            case 6:
                puts("Departing Soul Vault...");
                exit(0);
            default:
                puts("[-] Invalid choice!");
                break;
        }
    }

    return 0;
}
