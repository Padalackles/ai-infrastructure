#!/usr/bin/env node
/**
 * Scheduler Service — entry point.
 *
 * Starts with the Hub, stops with the Hub.  Designed to be launched
 * as a standalone Node.js process managed by docker-compose.
 *
 * Startup flow::
 *
 *   1. Load configuration           (config.yaml)
 *   2. Create JobRegistry
 *   3. Register built-in jobs       (DailyJournalJob, …)
 *   4. Create Scheduler
 *   5. scheduler.start()            (arms timers, waits for cron)
 *   6. idle — wait for SIGTERM/SIGINT
 *   7. scheduler.stop()             (cancels timers, drains)
 *   8. process.exit(0)
 */

import { Scheduler } from "./scheduler.js";
import { JobRegistry } from "./registry.js";
import { loadSchedulerConfig } from "./config.js";
import { DailyJournalJob } from "./jobs/dailyJournal.js";

// ═══════════════════════════════════════════════════════════════════
// 1. Load configuration
// ═══════════════════════════════════════════════════════════════════

const config = loadSchedulerConfig();
console.log("[scheduler] configuration loaded");

// ═══════════════════════════════════════════════════════════════════
// 2–3. Create registry + register built-in jobs
// ═══════════════════════════════════════════════════════════════════

const registry = new JobRegistry();

// Register every built-in job whose config section exists and is enabled.
const BUILTIN_JOBS: Array<{ key: string; factory: () => import("./types.js").Job }> = [
  {
    key: "dailyJournal",
    factory: () => new DailyJournalJob(),
  },
];

for (const { key, factory } of BUILTIN_JOBS) {
  const entry = config[key];
  // A missing config section means "use class defaults" → register it.
  // An explicit ``enabled: false`` skips registration entirely.
  if (typeof entry === "object" && entry !== null && entry.enabled === false) {
    console.log(`[scheduler] "${key}" disabled in config — skipping registration`);
    continue;
  }
  registry.register(factory());
}

// ═══════════════════════════════════════════════════════════════════
// 4–5. Create Scheduler + start
// ═══════════════════════════════════════════════════════════════════

const scheduler = new Scheduler(registry, config);

async function startup(): Promise<void> {
  await scheduler.start();
  console.log("[scheduler] service ready");
}

// ═══════════════════════════════════════════════════════════════════
// 6–7. Signal handling → graceful stop
// ═══════════════════════════════════════════════════════════════════

async function shutdown(signal: string): Promise<void> {
  console.log(`[scheduler] received ${signal} — shutting down`);
  await scheduler.stop();
  console.log("[scheduler] exit.");
  process.exit(0);
}

process.on("SIGTERM", () => void shutdown("SIGTERM"));
process.on("SIGINT", () => void shutdown("SIGINT"));

// Prevent unhandled rejections from silently killing the process.
process.on("unhandledRejection", (reason) => {
  console.error("[scheduler] unhandled rejection:", reason);
});

// ═══════════════════════════════════════════════════════════════════
// Go!
// ═══════════════════════════════════════════════════════════════════

void startup();
