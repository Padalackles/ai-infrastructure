/**
 * Job Registry
 *
 * Single source of truth for which jobs the Scheduler knows about.
 * Thread-safe in the sense that all mutations happen before
 * ``Scheduler.start()`` — no locks needed at runtime.
 *
 * Adding a new automation task::
 *
 *   registry.register(new MyJob());
 *
 * No other code changes required.
 */

import type { Job } from "./types.js";

export class JobRegistry {
  private readonly _jobs = new Map<string, Job>();

  // ── CRUD ──────────────────────────────────────────────────────

  /** Register a job instance.  Duplicate ``id`` replaces silently. */
  register(job: Job): void {
    if (!job.id) {
      throw new Error("Job must have a non-empty id");
    }
    this._jobs.set(job.id, job);
    console.log(`[scheduler] registered job "${job.id}" (cron: ${job.cron})`);
  }

  /** Remove a previously registered job by id.  Idempotent. */
  remove(id: string): boolean {
    return this._jobs.delete(id);
  }

  /** Look up a single job. */
  get(id: string): Job | undefined {
    return this._jobs.get(id);
  }

  /** All registered jobs (snapshot). */
  getAll(): Job[] {
    return [...this._jobs.values()];
  }

  /** Number of registered jobs. */
  get count(): number {
    return this._jobs.size;
  }

  // ── Bulk ──────────────────────────────────────────────────────

  /** Registered job ids. */
  ids(): IterableIterator<string> {
    return this._jobs.keys();
  }
}
