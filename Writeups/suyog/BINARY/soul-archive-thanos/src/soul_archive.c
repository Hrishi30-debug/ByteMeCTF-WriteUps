#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>

#define MAX_ARCHIVE 8
#define SECRET_MAGIC 0x50574e534f554c53ULL /* "PWNSOULS" */

#define TYPE_HUMAN    0x1001
#define TYPE_AVENGER  0x1002
#define TYPE_GUARDIAN 0x1003
#define TYPE_TITAN    0x1004
#define TYPE_VOID     0x1005

struct Soul;

typedef void (*consume_fn)(struct Soul *);
typedef void (*inspect_fn)(struct Soul *);

struct Soul {
    char name[32];
    uint64_t essence;
    uint64_t type;
    consume_fn consume;
    inspect_fn inspect;
};

/* TransferRecord: Same size as struct Soul (32 + 8 + 8 + 8 + 8 = 64 bytes)
   This enables allocator reuse and deliberate type confusion */
struct TransferRecord {
    char realm_origin[24];
    uint32_t transfer_id;
    uint32_t flags;
    uint64_t timestamp;
    uint64_t raw_entropy;
    uint64_t auth_callback;
    uint64_t audit_callback;
};

/* Global archive state */
static struct Soul *archive[MAX_ARCHIVE];
static int total_captured = 0;
static int merges_performed = 0;
static int souls_erased = 0;

/* Custom internal cache that holds freed pointers (causing dangling pointers / UAF) */
static struct Soul *cached_souls[MAX_ARCHIVE];
static int cache_count = 0;

/* Decoy / Honeypot functions */
void fake_win(void) {
    puts("\n[!] The Soul Stone shatters into worthless dust... Decoy triggered.");
    exit(1);
}

void debug_shell(void) {
    puts("\n[-] Unauthorized access detected in debug sector.");
    exit(1);
}

void unused_callback(struct Soul *s) {
    printf("[*] Resonance echo from: %s\n", s ? s->name : "Unknown");
}

/* Legitimate Callbacks */
void inspect_human(struct Soul *s) {
    printf("[HUMAN SOUL] Name: %s | Essence: 0x%lx\n", s->name, s->essence);
}

void inspect_avenger(struct Soul *s) {
    printf("[AVENGER SOUL] Name: %s | Heroic Essence: 0x%lx\n", s->name, s->essence);
}

void inspect_guardian(struct Soul *s) {
    printf("[GUARDIAN SOUL] Name: %s | Cosmic Essence: 0x%lx\n", s->name, s->essence);
}

void inspect_titan(struct Soul *s) {
    printf("[TITAN SOUL] Name: %s | Unyielding Essence: 0x%lx\n", s->name, s->essence);
}

void inspect_void(struct Soul *s) {
    printf("[VOID RESIDUE] Name: %s | Echoes: 0x%lx\n", s->name, s->essence);
}

void consume_default(struct Soul *s) {
    printf("[~] Consuming essence from %s...\n", s->name);
    s->essence >>= 1;
}

/* Win condition function - requires satisfying both execution flow AND archive state */
void soul_ascension(struct Soul *s) {
    if (total_captured >= 6 &&
        merges_performed == 3 &&
        souls_erased == 1 &&
        s != NULL &&
        s->essence == SECRET_MAGIC) {

        puts("\n╔═══════════════════════════════════════════════════╗");
        puts("║          THE SOUL STONE ASCENSION AWAKENS         ║");
        puts("╚═══════════════════════════════════════════════════╝");
        puts("[+] You have mastered the memory of the cosmos.");

        /* Obfuscated flag reconstruction */
        char flag[] = {
            'O','W','A','S','P','{','T','h','4','n','0','s','_',
            'S','0','u','l','_','M','e','m','0','r','y','_',
            'U','A','F','_','T','y','p','e','_','C','o','n','f','u','s','i','o','n','}'
        };
        fwrite(flag, 1, sizeof(flag), stdout);
        putchar('\n');
        fflush(stdout);
    } else {
        printf("\n[-] The Soul Stone remains unmoved.\n");
        printf("    Archive requirements: Captured >= 6 (Current: %d)\n", total_captured);
        printf("    Merges == 3 (Current: %d)\n", merges_performed);
        printf("    Erased == 1 (Current: %d)\n", souls_erased);
        printf("    Target Essence: 0x%llx (Current: 0x%lx)\n", (unsigned long long)SECRET_MAGIC, s ? s->essence : 0);
        fflush(stdout);
    }
}

static int read_int(void) {
    char buf[32];
    if (!fgets(buf, sizeof(buf), stdin)) return -1;
    return atoi(buf);
}

static void read_str(char *buf, size_t max_len) {
    size_t i = 0;
    while (i < max_len - 1) {
        char c;
        if (read(STDIN_FILENO, &c, 1) <= 0) break;
        if (c == '\n') break;
        buf[i++] = c;
    }
    buf[i] = '\0';
}

void menu(void) {
    puts("\n================================");
    puts("       SOUL ARCHIVE v6.0");
    puts("================================");
    puts("Six souls. One archive. One memory.");
    puts("1. Capture soul");
    puts("2. Inspect soul");
    puts("3. Merge souls");
    puts("4. Erase soul");
    puts("5. Transfer soul (Record Log)");
    puts("6. Exit");
    printf("> ");
    fflush(stdout);
}

void capture_soul(void) {
    int idx = -1;
    for (int i = 0; i < MAX_ARCHIVE; i++) {
        if (!archive[i]) {
            idx = i;
            break;
        }
    }

    if (idx == -1) {
        puts("[-] Archive is full!");
        return;
    }

    struct Soul *s = (struct Soul *)malloc(sizeof(struct Soul));
    if (!s) {
        puts("[-] Allocation failed!");
        return;
    }

    printf("Soul name: ");
    read_str(s->name, sizeof(s->name));

    puts("Select Type:");
    puts("1. Human  2. Avenger  3. Guardian  4. Titan  5. Void");
    printf("Type: ");
    int t = read_int();
    switch (t) {
        case 1: s->type = TYPE_HUMAN; s->inspect = inspect_human; break;
        case 2: s->type = TYPE_AVENGER; s->inspect = inspect_avenger; break;
        case 3: s->type = TYPE_GUARDIAN; s->inspect = inspect_guardian; break;
        case 4: s->type = TYPE_TITAN; s->inspect = inspect_titan; break;
        default: s->type = TYPE_VOID; s->inspect = inspect_void; break;
    }

    s->consume = consume_default;
    printf("Initial Essence (hex value e.g. 1000): ");
    char hexbuf[32];
    if (fgets(hexbuf, sizeof(hexbuf), stdin)) {
        s->essence = strtoull(hexbuf, NULL, 16);
    } else {
        s->essence = 0x1000;
    }

    archive[idx] = s;
    total_captured++;
    printf("[+] Soul registered in vessel [%d].\n", idx);
}

void inspect_soul(void) {
    printf("Enter vessel index (0-%d): ", MAX_ARCHIVE - 1);
    int idx = read_int();
    if (idx < 0 || idx >= MAX_ARCHIVE || !archive[idx]) {
        puts("[-] Vessel is empty or invalid!");
        return;
    }

    struct Soul *s = archive[idx];
    printf("--- Vessel [%d] ---\n", idx);
    printf("Soul Name: %s\n", s->name);
    printf("Type: 0x%lx\n", s->type);
    printf("Essence: 0x%lx\n", s->essence);
    printf("Inspect Callback: %p\n", (void *)s->inspect);

    if (s->inspect) {
        s->inspect(s);
    }
}

void merge_souls(void) {
    printf("First vessel index to merge: ");
    int a = read_int();
    printf("Second vessel index to merge: ");
    int b = read_int();

    if (a < 0 || a >= MAX_ARCHIVE || !archive[a] ||
        b < 0 || b >= MAX_ARCHIVE || !archive[b] || a == b) {
        puts("[-] Invalid vessel selection!");
        return;
    }

    /* Bug: Soul B is freed, added to internal cached_souls, but archive[b] is NOT cleared */
    struct Soul *s_a = archive[a];
    struct Soul *s_b = archive[b];

    s_a->essence += s_b->essence;
    strncat(s_a->name, "+", sizeof(s_a->name) - strlen(s_a->name) - 1);
    strncat(s_a->name, s_b->name, sizeof(s_a->name) - strlen(s_a->name) - 1);

    if (cache_count < MAX_ARCHIVE) {
        cached_souls[cache_count++] = s_b;
    }

    free(s_b);
    /* Notice: archive[b] still holds s_b pointer! UAF created */

    merges_performed++;
    printf("[+] Souls merged into vessel [%d]. Vessel [%d] spirit dissolved.\n", a, b);
}

void erase_soul(void) {
    printf("Enter vessel index to erase (0-%d): ", MAX_ARCHIVE - 1);
    int idx = read_int();
    if (idx < 0 || idx >= MAX_ARCHIVE || !archive[idx]) {
        puts("[-] Invalid vessel!");
        return;
    }

    free(archive[idx]);
    archive[idx] = NULL;
    souls_erased++;
    puts("[+] Vessel thoroughly wiped from the archive.");
}

/* Creates a TransferRecord object of the same size (64 bytes)
   This triggers allocator reuse and allows controlled type confusion over freed Soul objects */
void transfer_soul(void) {
    struct TransferRecord *tr = (struct TransferRecord *)malloc(sizeof(struct TransferRecord));
    if (!tr) {
        puts("[-] Record allocation failed!");
        return;
    }

    printf("Realm of origin: ");
    read_str(tr->realm_origin, sizeof(tr->realm_origin));

    printf("Transfer ID (decimal): ");
    tr->transfer_id = (uint32_t)read_int();

    printf("Entropy Flags (decimal): ");
    tr->flags = (uint32_t)read_int();

    printf("Timestamp (hex e.g. 1337): ");
    char hexbuf[32];
    if (fgets(hexbuf, sizeof(hexbuf), stdin)) {
        tr->timestamp = strtoull(hexbuf, NULL, 16);
    }

    printf("Raw Entropy / Essence (hex): ");
    if (fgets(hexbuf, sizeof(hexbuf), stdin)) {
        tr->raw_entropy = strtoull(hexbuf, NULL, 16);
    }

    printf("Audit Callback Address (hex, 0 for default): ");
    if (fgets(hexbuf, sizeof(hexbuf), stdin)) {
        uint64_t cb = strtoull(hexbuf, NULL, 16);
        tr->audit_callback = cb;
        tr->auth_callback = cb;
    }

    printf("[+] Transfer record inscribed at %p.\n", (void *)tr);
}

int main(void) {
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    while (1) {
        menu();
        int choice = read_int();
        switch (choice) {
            case 1: capture_soul(); break;
            case 2: inspect_soul(); break;
            case 3: merge_souls(); break;
            case 4: erase_soul(); break;
            case 5: transfer_soul(); break;
            case 6:
                puts("Exiting Soul Archive...");
                exit(0);
            default:
                puts("[-] Unknown command.");
                break;
        }
    }
    return 0;
}
