CREATE TABLE `intents` (
	`intent_id` text PRIMARY KEY NOT NULL,
	`session_id` text NOT NULL,
	`turn_id` text NOT NULL,
	`seat_id` text NOT NULL,
	`operation_id` text NOT NULL,
	`payload_digest` text NOT NULL,
	`action` text NOT NULL,
	`approach` text NOT NULL,
	`speech` text NOT NULL,
	`status` text NOT NULL,
	`outcome` text NOT NULL,
	`resolution_summary` text NOT NULL,
	`visible_consequences` text NOT NULL,
	`created_at` text NOT NULL,
	`resolved_at` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `idx_intents_session_operation` ON `intents` (`session_id`,`operation_id`);--> statement-breakpoint
CREATE INDEX `idx_intents_turn` ON `intents` (`turn_id`);--> statement-breakpoint
CREATE TABLE `session_events` (
	`event_id` text PRIMARY KEY NOT NULL,
	`session_id` text NOT NULL,
	`sequence` integer NOT NULL,
	`event_type` text NOT NULL,
	`public_payload` text NOT NULL,
	`seat_payload` text NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `idx_session_events_sequence` ON `session_events` (`session_id`,`sequence`);--> statement-breakpoint
CREATE TABLE `session_seats` (
	`seat_id` text PRIMARY KEY NOT NULL,
	`session_id` text NOT NULL,
	`character_id` text NOT NULL,
	`status` text DEFAULT 'ready' NOT NULL,
	`bound_at` text,
	`updated_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `idx_session_seats_session` ON `session_seats` (`session_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `idx_session_seats_character` ON `session_seats` (`session_id`,`character_id`);--> statement-breakpoint
CREATE TABLE `sessions` (
	`session_id` text PRIMARY KEY NOT NULL,
	`scenario_id` text NOT NULL,
	`status` text DEFAULT 'awaiting_join' NOT NULL,
	`revision` integer DEFAULT 0 NOT NULL,
	`current_turn` integer DEFAULT 1 NOT NULL,
	`created_at` text NOT NULL,
	`updated_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `idx_sessions_status` ON `sessions` (`status`);--> statement-breakpoint
CREATE TABLE `turns` (
	`turn_id` text PRIMARY KEY NOT NULL,
	`session_id` text NOT NULL,
	`turn_number` integer NOT NULL,
	`scene_id` text NOT NULL,
	`source_revision` integer NOT NULL,
	`status` text DEFAULT 'queued' NOT NULL,
	`opened_at` text,
	`resolved_at` text
);
--> statement-breakpoint
CREATE UNIQUE INDEX `idx_turns_session_number` ON `turns` (`session_id`,`turn_number`);--> statement-breakpoint
CREATE INDEX `idx_turns_session_status` ON `turns` (`session_id`,`status`);--> statement-breakpoint
-- Keep the v1 demo_sessions table as a non-authoritative rollback artifact.
--> statement-breakpoint
PRAGMA optimize;
