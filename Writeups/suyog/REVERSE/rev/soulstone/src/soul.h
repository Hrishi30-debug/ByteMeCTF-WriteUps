#ifndef SOUL_H
#define SOUL_H

#include <stdint.h>
#include <stddef.h>
#include "soul_data.h"
#include "crypto.h"

uint32_t soul_resonance(const char *sacrifice, uint32_t token);
int verify_sacrifice_name(const char *name);

#endif /* SOUL_H */
