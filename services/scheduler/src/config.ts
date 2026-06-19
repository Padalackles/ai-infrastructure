/**
 * Scheduler Configuration
 *
 * Reads ``config.yaml`` from the scheduler service directory.
 * Merges user overrides on top of sensible defaults.
 */

import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import yaml from "js-yaml";
import type { SchedulerConfig } from "./types.js";

// ── Paths ─────────────────────────────────────────────────────────

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const DEFAULT_CONFIG_PATH = resolve(__dirname, "..", "config.yaml");

// ── Defaults ──────────────────────────────────────────────────────

const DEFAULTS: SchedulerConfig = {
  enabled: true,
  dailyJournal: {
    enabled: true,
    cron: "0 22 * * *", // 22:00 UTC daily
  },
};

// ── Load ──────────────────────────────────────────────────────────

export function loadSchedulerConfig(
  configPath?: string,
): SchedulerConfig {
  const path = configPath ?? DEFAULT_CONFIG_PATH;

  let fileConfig: Partial<SchedulerConfig> = {};
  try {
    const raw = readFileSync(path, "utf-8");
    fileConfig = (yaml.load(raw) as Partial<SchedulerConfig>) ?? {};
  } catch {
    console.warn(
      `[scheduler] config file not found or unreadable: ${path} — using defaults`,
    );
  }

  // Deep-merge: file values override defaults.
  const merged: SchedulerConfig = { ...DEFAULTS };

  for (const [key, defaultVal] of Object.entries(DEFAULTS)) {
    const fileVal = fileConfig[key];
    if (fileVal !== undefined) {
      if (
        typeof defaultVal === "object" &&
        defaultVal !== null &&
        !Array.isArray(defaultVal) &&
        typeof fileVal === "object" &&
        fileVal !== null &&
        !Array.isArray(fileVal)
      ) {
        // Merge nested job config objects
        merged[key] = { ...defaultVal, ...fileVal } as JobConfig;
      } else {
        merged[key] = fileVal;
      }
    }
  }

  // Carry over any extra keys from file that aren't in defaults
  // (future jobs added purely via config).
  for (const [key, val] of Object.entries(fileConfig)) {
    if (!(key in merged)) {
      merged[key] = val;
    }
  }

  return merged;
}

// Re-export for convenience
import type { JobConfig } from "./types.js";
