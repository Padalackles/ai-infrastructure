/**
 * Scheduler Service — Shared Types
 *
 * Every type the Scheduler and its jobs agree on lives here.
 * New jobs only import `Job` and `ExecutionResult`.
 */

// ── Configuration ─────────────────────────────────────────────────

/** Per-job configuration block (from config.yaml). */
export interface JobConfig {
  enabled: boolean;
  cron: string; // 5-field cron expression
}

/**
 * Top-level scheduler configuration.
 * Supports arbitrary job-name keys whose values are JobConfig objects.
 */
export interface SchedulerConfig {
  enabled: boolean;
  [jobName: string]: boolean | JobConfig | undefined;
}

// ── Job Interface ─────────────────────────────────────────────────

/**
 * Contract every scheduled job must fulfill.
 *
 * Usage::
 *
 *   class MyJob implements Job {
 *     id = "my_job";
 *     name = "My Job";
 *     enabled = true;
 *     cron = "0 9 * * *";
 *
 *     async execute(): Promise<void> { ... }
 *   }
 *
 *   registry.register(new MyJob());
 */
export interface Job {
  /** Unique identifier — matches the config key. */
  readonly id: string;

  /** Human-readable name for logs. */
  readonly name: string;

  /** Whether this job is active (overridable via config). */
  enabled: boolean;

  /** 5-field cron expression (minute hour dom month dow). */
  cron: string;

  /** Execute the job. Throw on failure — the Scheduler catches it. */
  execute(): Promise<void>;
}

// ── Execution Result ──────────────────────────────────────────────

/** Structured record of a single job execution. */
export interface ExecutionResult {
  jobId: string;
  jobName: string;
  startTime: string; // ISO-8601 UTC
  endTime: string; // ISO-8601 UTC
  durationMs: number;
  success: boolean;
  error?: string;
}
