/**
 * Daily Journal Job — placeholder skeleton.
 *
 * Current behaviour: execute on schedule, log execution, return success.
 * No AI.  No Ombre.  Scheduling verification only.
 */

import type { Job } from "../types.js";

export class DailyJournalJob implements Job {
  readonly id = "dailyJournal";
  readonly name = "Daily Journal";
  enabled = true;
  cron = "0 22 * * *"; // 22:00 UTC daily

  async execute(): Promise<void> {
    const now = new Date().toISOString();

    console.log("[Scheduler]");
    console.log(`DailyJournal started`);

    console.log("");
    console.log("Current Time:");
    console.log(now.replace("T", " ").slice(0, 16));
    console.log("");

    console.log("DailyJournal finished.");
  }
}
