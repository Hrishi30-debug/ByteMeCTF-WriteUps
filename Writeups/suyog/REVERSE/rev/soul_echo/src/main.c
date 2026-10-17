#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/*
 * Soul Echoes: The Stonekeeper's Chronicle
 * A story-driven introductory reverse engineering challenge.
 */

static const char *SECRETS_OF_VORMIR = "OWASP{th3_st0n3k33p3r_wh1sp3rs_1nt0_th3_v01d}";

static void print_banner(void) {
    puts("╔═══════════════════════════════════════════════════════════════╗");
    puts("║                 SOUL ECHOES: THE CHRONICLES                   ║");
    puts("║               Memories from the Edge of Space                 ║");
    puts("╚═══════════════════════════════════════════════════════════════╝\n");
}

static void chapter_one(void) {
    puts("\n[+] CHAPTER I: THE EXILE");
    puts("-----------------------------------------------------------------");
    puts("The Space Stone did not kill me. It judged me.");
    puts("It ripped through the heavens and cast my broken spirit onto Vormir,");
    puts("a desolate world beneath twin dying suns.");
    puts("Here, flesh yields to shadow. I became a wraith, bound forever to");
    puts("guide wanderers to a treasure I can never possess.\n");
}

static void chapter_two(void) {
    puts("\n[+] CHAPTER II: THE WEIGHT OF KNOWLEDGE");
    puts("-----------------------------------------------------------------");
    puts("My curse is to know all who journey to this desolate pinnacle.");
    puts("I know their lineage. I know their triumphs, and I know their grief.");
    puts("They arrive consumed by ambition, yet when they look down into");
    puts("the yawning abyss, their courage falters.");
    puts("For the stone demands an everlasting exchange: a soul for a soul.\n");
}

static void chapter_three(void) {
    puts("\n[+] CHAPTER III: THE INSCRIPTION UPON THE OBSIDIAN CLIFF");
    puts("-----------------------------------------------------------------");
    puts("Before the silence reclaimed this mountain, I carved a final secret");
    puts("into the black stones above the clouds.");
    puts("A whisper etched into eternity for those who have eyes to see:");
    printf("\n    >>> %s <<<\n\n", SECRETS_OF_VORMIR);
    puts("May it guide you through the darkness of the cosmos.\n");
}

int main(void) {
    print_banner();

    puts("The chilling wind howling across the jagged peaks of Vormir carries");
    puts("faint whispers of an ancient ghost who has guarded the precipice for eons.");
    puts("");
    puts("The Stonekeeper floats before you in his tattered dark cowl.");
    puts("\"Seeker... what part of my sorrow do you wish to unveil?\"\n");

    puts("1. Read Chapter I: The Exile");
    puts("2. Read Chapter II: The Weight of Knowledge");
    puts("3. Read Chapter III: The Inscription upon the Obsidian Cliff");
    puts("4. Listen to the entire chronicle");
    puts("5. Depart from the precipice\n");

    printf("Choose your path (1-5): ");
    fflush(stdout);

    char choice[16];
    if (!fgets(choice, sizeof(choice), stdin)) {
        return 0;
    }

    int opt = atoi(choice);
    switch (opt) {
        case 1:
            chapter_one();
            break;
        case 2:
            chapter_two();
            break;
        case 3:
            chapter_three();
            break;
        case 4:
            chapter_one();
            chapter_two();
            chapter_three();
            break;
        case 5:
            puts("\nYou turn back down the winding staircase into the freezing mist.");
            puts("The whisper remains waiting for the worthy.");
            break;
        default:
            puts("\nThe wind scatters your words into the void.");
            break;
    }

    return 0;
}
