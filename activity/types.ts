/**
 * Activity Event Schema — TypeScript Type Contract
 *
 * Canonical programmatic definition of the unified Activity Event.
 * Every component in the pipeline (Gateway → Normalizer → Database →
 * Decision → Claude Trigger) uses these types.
 *
 * This file is the *contract*, not the implementation.
 * No logic lives here — only types.
 *
 * Version: 1
 * Task: A001
 */

// ── Event Sources ──────────────────────────────────────────────────

/** Originating platform. */
export type EventSource =
  | "android"
  | "ios"
  | "desktop"
  | "web"
  | "iot"
  | "service";

// ── Collectors ────────────────────────────────────────────────────

/** Software that captured the event. */
export type EventCollector =
  | "macrodroid"
  | "tasker"
  | "shortcuts"
  | "home-assistant"
  | "scheduler"
  | (string & {}); // future collectors — extensible

// ── Event Types (hierarchical dot-notation) ───────────────────────

/**
 * All known event types.
 * New types are added here as the subsystem grows.
 */
export type EventType =
  // Device
  | "device.awake"
  | "device.sleep"
  | "device.boot"
  | "device.shutdown"

  // Battery
  | "battery.low"
  | "battery.full"
  | "battery.charging.started"
  | "battery.charging.stopped"
  | "battery.level_changed"

  // App
  | "app.opened"
  | "app.closed"

  // Network
  | "network.connected"
  | "network.disconnected"
  | "network.wifi.connected"

  // Location
  | "location.changed"

  // Notification
  | "notification.received"
  | "notification.dismissed"

  // Call
  | "call.started"
  | "call.ended"
  | "call.missed"

  // Screen
  | "screen.on"
  | "screen.off"
  | "screen.unlocked"

  // Sensor
  | "sensor.reading"

  // Bluetooth
  | "bluetooth.connected"
  | "bluetooth.disconnected"

  // Wi-Fi
  | "wifi.connected"
  | "wifi.disconnected"

  // Schedule (internal)
  | "schedule.triggered"

  // Escape hatch for future types
  | (string & {});

// ── Payload Sub-Schemas ───────────────────────────────────────────

export interface DeviceAwakePayload {
  method: "power_button" | "tap" | "lift" | "notification" | "alarm";
}

export interface DeviceSleepPayload {
  method: "power_button" | "timeout" | "manual";
}

export interface BatteryLowPayload {
  level: number; // 0–100
  is_charging: boolean;
}

export interface BatteryFullPayload {
  level: number; // always 100
}

export interface BatteryChargingStartedPayload {
  level: number;
  method: "usb" | "wireless" | "unknown";
}

export interface BatteryChargingStoppedPayload {
  level: number;
}

export interface BatteryLevelChangedPayload {
  level: number;
  is_charging: boolean;
}

export interface AppOpenedPayload {
  package: string; // e.g. "com.whatsapp"
  label: string; // e.g. "WhatsApp"
}

export interface AppClosedPayload {
  package: string;
  label: string;
}

export interface NetworkConnectedPayload {
  type: "wifi" | "mobile" | "ethernet" | "bluetooth";
  name?: string; // Wi-Fi SSID, etc.
}

export interface NetworkDisconnectedPayload {
  type: "wifi" | "mobile" | "ethernet" | "bluetooth";
}

export interface NetworkWifiConnectedPayload {
  ssid: string;
  [key: string]: unknown; // preserve unknown collector fields
}

export interface LocationChangedPayload {
  latitude: number;
  longitude: number;
  accuracy_m: number;
  provider: "gps" | "network" | "fused";
}

export interface NotificationReceivedPayload {
  package: string;
  title?: string; // metadata only — full body in raw
  category?: string; // Android notification category
}

export interface NotificationDismissedPayload {
  package: string;
}

export interface CallStartedPayload {
  direction: "incoming" | "outgoing";
  number?: string; // may be empty for privacy
}

export interface CallEndedPayload {
  direction: "incoming" | "outgoing";
  duration_seconds: number;
}

export interface CallMissedPayload {
  number?: string;
}

export interface ScreenOnPayload {
  method: "power_button" | "tap" | "lift" | "notification";
}

export interface ScreenOffPayload {
  method: "power_button" | "timeout" | "manual";
}

export interface ScreenUnlockedPayload {
  method: "pin" | "pattern" | "fingerprint" | "face" | "none";
}

export interface SensorReadingPayload {
  sensor: string;
  values: Record<string, number>;
}

export interface BluetoothConnectedPayload {
  device_name: string;
  device_address: string;
}

export interface BluetoothDisconnectedPayload {
  device_name: string;
  device_address: string;
}

export interface WifiConnectedPayload {
  ssid: string;
  bssid?: string;
}

export interface WifiDisconnectedPayload {
  ssid: string;
}

export interface ScheduleTriggeredPayload {
  job_id: string;
  job_name: string;
}

// ── Discriminated Payload Union ───────────────────────────────────

/**
 * Maps each EventType to its typed payload.
 * Decision Scripts narrow on `type` to access typed payload fields.
 *
 * Example::
 *
 *   if (event.type === "battery.low") {
 *     console.log(event.payload.level);  // number, guaranteed
 *   }
 */
export type EventPayload<T extends EventType = EventType> =
  T extends "device.awake" ? DeviceAwakePayload :
  T extends "device.sleep" ? DeviceSleepPayload :
  T extends "battery.low" ? BatteryLowPayload :
  T extends "battery.full" ? BatteryFullPayload :
  T extends "battery.charging.started" ? BatteryChargingStartedPayload :
  T extends "battery.charging.stopped" ? BatteryChargingStoppedPayload :
  T extends "battery.level_changed" ? BatteryLevelChangedPayload :
  T extends "app.opened" ? AppOpenedPayload :
  T extends "app.closed" ? AppClosedPayload :
  T extends "network.connected" ? NetworkConnectedPayload :
  T extends "network.disconnected" ? NetworkDisconnectedPayload :
  T extends "network.wifi.connected" ? NetworkWifiConnectedPayload :
  T extends "location.changed" ? LocationChangedPayload :
  T extends "notification.received" ? NotificationReceivedPayload :
  T extends "notification.dismissed" ? NotificationDismissedPayload :
  T extends "call.started" ? CallStartedPayload :
  T extends "call.ended" ? CallEndedPayload :
  T extends "call.missed" ? CallMissedPayload :
  T extends "screen.on" ? ScreenOnPayload :
  T extends "screen.off" ? ScreenOffPayload :
  T extends "screen.unlocked" ? ScreenUnlockedPayload :
  T extends "sensor.reading" ? SensorReadingPayload :
  T extends "bluetooth.connected" ? BluetoothConnectedPayload :
  T extends "bluetooth.disconnected" ? BluetoothDisconnectedPayload :
  T extends "wifi.connected" ? WifiConnectedPayload :
  T extends "wifi.disconnected" ? WifiDisconnectedPayload :
  T extends "schedule.triggered" ? ScheduleTriggeredPayload :
  Record<string, unknown>; // fallback for unknown future types

// ── Root Event ────────────────────────────────────────────────────

/**
 * The unified Activity Event — every component in the pipeline
 * produces or consumes this shape.
 */
export interface ActivityEvent<T extends EventType = EventType> {
  /** Schema version.  Bump on breaking changes. */
  version: 1;

  /** Globally unique ID.  Generated by Gateway (ULID format: evt_<ulid>). */
  id: string;

  /** ISO 8601 timestamp with millisecond precision — when the event occurred. */
  timestamp: string;

  /** Originating platform. */
  source: EventSource;

  /** Software that captured the event. */
  collector: EventCollector;

  /** Human-readable device identifier. */
  device: string;

  /** Hierarchical event type (dot-notation). */
  type: T;

  /** Normalized, typed event data.  Schema varies by type. */
  payload: EventPayload<T>;

  /** Original, unmodified event as received from the collector. */
  raw: Record<string, unknown>;
}
