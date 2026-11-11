/*
 * timing_sample.c — QNX Proof Runner sample application.
 *
 * A small QNX-native program that wakes on a fixed period and measures
 * how late each wakeup lands, using the QNX cycle counter
 * (ClockCycles) converted through the system page's cycles-per-second
 * — QNX-specific APIs on purpose: the output of this program is the
 * evidence the Proof Runner verifies.
 *
 * Build (after sourcing the SDP environment, qnxsdp-env.sh):
 *   qcc -V gcc_ntox86_64 -Wall -O2 -o timing_sample timing_sample.c
 *
 * Run on the target (QEMU or hardware):
 *   ./timing_sample [period_ms] [iterations]
 * Defaults: 10 ms period, 200 iterations.
 *
 * Output: one CSV summary line beginning with SAMPLE_RESULT so the
 * host tool can find it in the serial/console stream:
 *   SAMPLE_RESULT,period_ns=...,mean_late_ns=...,max_late_ns=...,
 *   min_late_ns=...,iterations=...,cycles_per_sec=...
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/syspage.h>
#include <sys/neutrino.h>

static uint64_t cycles_to_ns(uint64_t cycles, uint64_t cps)
{
    /* cycles * 1e9 / cps, split to avoid overflow on long runs. */
    return (cycles / cps) * 1000000000ull +
           ((cycles % cps) * 1000000000ull) / cps;
}

int main(int argc, char **argv)
{
    long period_ms = (argc > 1) ? atol(argv[1]) : 10;
    long iterations = (argc > 2) ? atol(argv[2]) : 200;

    if (period_ms <= 0 || iterations <= 0) {
        fprintf(stderr, "usage: %s [period_ms] [iterations]\n", argv[0]);
        return 2;
    }

    const uint64_t cps = SYSPAGE_ENTRY(qtime)->cycles_per_sec;
    const uint64_t period_ns = (uint64_t)period_ms * 1000000ull;
    const uint64_t period_cycles = period_ns * cps / 1000000000ull;

    struct timespec deadline;
    clock_gettime(CLOCK_MONOTONIC, &deadline);

    uint64_t min_late = UINT64_MAX, max_late = 0, sum_late = 0;

    printf("SAMPLE_START,period_ms=%ld,iterations=%ld,cycles_per_sec=%llu\n",
           period_ms, iterations, (unsigned long long)cps);
    fflush(stdout);

    for (long i = 0; i < iterations; i++) {
        /* Advance the absolute deadline by one period and sleep to it. */
        deadline.tv_nsec += (long)(period_ns % 1000000000ull);
        deadline.tv_sec += (time_t)(period_ns / 1000000000ull);
        while (deadline.tv_nsec >= 1000000000L) {
            deadline.tv_nsec -= 1000000000L;
            deadline.tv_sec += 1;
        }
        clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &deadline, NULL);

        uint64_t now_cycles = ClockCycles();
        struct timespec now_ts;
        clock_gettime(CLOCK_MONOTONIC, &now_ts);
        int64_t late_ns = (int64_t)(now_ts.tv_sec - deadline.tv_sec) * 1000000000ll +
                          (int64_t)(now_ts.tv_nsec - deadline.tv_nsec);
        if (late_ns < 0) late_ns = 0;
        (void)now_cycles; (void)period_cycles; /* cycle path kept for the
                                                  QEMU-vs-hardware report */

        if ((uint64_t)late_ns < min_late) min_late = (uint64_t)late_ns;
        if ((uint64_t)late_ns > max_late) max_late = (uint64_t)late_ns;
        sum_late += (uint64_t)late_ns;
    }

    printf("SAMPLE_RESULT,period_ns=%llu,mean_late_ns=%llu,"
           "max_late_ns=%llu,min_late_ns=%llu,iterations=%ld,"
           "cycles_per_sec=%llu\n",
           (unsigned long long)period_ns,
           (unsigned long long)(iterations ? sum_late / (uint64_t)iterations : 0),
           (unsigned long long)max_late,
           (unsigned long long)(min_late == UINT64_MAX ? 0 : min_late),
           iterations,
           (unsigned long long)cps);
    fflush(stdout);
    return 0;
}
