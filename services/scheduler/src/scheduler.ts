/**
 * Scheduler — background job execution engine.
 *
 * Lifecycle::
 *
 *   const scheduler = new Scheduler(registry, config);
 *   await scheduler.start();   // spawns one timer per enabled job
 *   // … service runs …
 *   await scheduler.stop();    // cancels all timers, waits for drain
 *
 * The Scheduler does NOT block the event loop — every job runs on its
 * own timer.  One misbehaving job can never take down the Scheduler
 * or affect other jobs.
 */

import cronParser from "cron-parser";
import type { Job, ExecutionResult, SchedulerConfig, JobConfig } from "./types.js";
import type { JobRegistry } from "./registry.js";

// ── Helpers ───────────────────────────────────────────────────────

function iso(ts: number): string {
  return new Date(ts).toISOString();
}

function jobConfig(
  config: SchedulerConfig,
  jobId: string,
): JobConfig {
  const entry = config[jobId];
  if (typeof entry === "object" && entry !== null) {
    return { enabled: entry.enabled, cron: entry.cron };
  }
  return { enabled: true, cron: "" };
}

// ── Scheduler ─────────────────────────────────────────────────────

export class Scheduler {
  private readonly registry: JobRegistry;
  private readonly config: SchedulerConfig;
  private running = false;
  private readonly timers = new Map<string, NodeJS.Timeout>();
  /** Track in-flight execute() promises so stop() can drain them. */
  private readonly inFlight = new Set<Promise<void>>();

  constructor(registry: JobRegistry, config: SchedulerConfig) {
    this.registry = registry;
    this.config = config;
  }

  // ── Public API ─────────────────────────────────────────────────

  /** Start all enabled jobs.  Idempotent — safe to call more than once. */
  async start(): Promise<void> {
    if (!this.config.enabled) {
      console.log("[scheduler] disabled in config — skipping start");
      return;
    }
    if (this.running) {
      console.log("[scheduler] already running");
      return;
    }

    this.running = true;
    console.log(
      `[scheduler] starting with ${this.registry.count} registered job(s)`,
    );

    for (const job of this.registry.getAll()) {
      const cfg = jobConfig(this.config, job.id);

      // Config overrides
      if (cfg.cron) job.cron = cfg.cron;
      if (!cfg.enabled) {
        console.log(`[scheduler] job "${job.id}" disabled — skipping`);
        continue;
      }

      // Validate cron before scheduling
      try {
        cronParser.parseExpression(job.cron);
      } catch {
        console.error(
          `[scheduler] job "${job.id}" has invalid cron "${job.cron}" — skipping`,
        );
        continue;
      }

      this.scheduleJob(job);
      console.log(
        `[scheduler] job "${job.id}" scheduled (cron: ${job.cron})`,
      );
    }
  }

  /** Graceful stop.  Cancels all timers and drains in-flight executions. */
  async stop(): Promise<void> {
    this.running = false;

    // Cancel all timers
    for (const [id, timer] of this.timers) {
      clearTimeout(timer);
      this.timers.delete(id);
      console.log(`[scheduler] timer cancelled for "${id}"`);
    }

    // Wait for in-flight executions to finish
    if (this.inFlight.size > 0) {
      console.log(
        `[scheduler] waiting for ${this.inFlight.size} in-flight job(s)…`,
      );
      await Promise.allSettled([...this.inFlight]);
      this.inFlight.clear();
    }

    console.log("[scheduler] stopped");
  }

  // ── Internal ────────────────────────────────────────────────────

  /** Compute ms until the next cron fire time and arm a single-shot timer. */
  private scheduleJob(job: Job): void {
    const tick = () => {
      if (!this.running) return;

      try {
        const interval = cronParser.parseExpression(job.cron);
        const nextMs = interval.next().getTime();
        const delay = Math.max(0, nextMs - Date.now());

        this.timers.set(
          job.id,
          setTimeout(() => {
            this.timers.delete(job.id);
            void this.executeJob(job).finally(() => {
              // Reschedule for the *next* interval — no accumulated drift.
              if (this.running) this.scheduleJob(job);
            });
          }, delay),
        );
      } catch (err) {
        console.error(
          `[scheduler] cron parse error for "${job.id}":`,
          (err as Error).message,
        );
      }
    };

    tick(); // arm first timer
  }

  /** Execute one job, capture timing and outcome, log the result. */
  private async executeJob(job: Job): Promise<ExecutionResult> {
    const startMs = Date.now();
    const startTime = iso(startMs);
    let success = false;
    let error: string | undefined;

    console.log(`▶ [scheduler] job "${job.id}" started at ${startTime}`);

    const promise = job
      .execute()
      .then(() => {
        success = true;
      })
      .catch((err: unknown) => {
        error = (err as Error).message ?? String(err);
        console.error(
          `✖ [scheduler] job "${job.id}" failed — ${error}`,
        );
      })
      .finally(() => {
        this.inFlight.delete(promise);
      });

    this.inFlight.add(promise);
    await promise;

    const endMs = Date.now();
    const endTime = iso(endMs);
    const durationMs = endMs - startMs;
    const status = success ? "✓ success" : "✖ FAILURE";

    console.log(
      `◼ [scheduler] job "${job.id}" ${status}  ` +
        `start=${startTime}  end=${endTime}  duration=${durationMs} ms`,
    );

    return { jobId: job.id, jobName: job.name, startTime, endTime, durationMs, success, error };
  }
}
