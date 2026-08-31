CREATE TABLE `demo_sessions` (
	`session_id` text PRIMARY KEY NOT NULL,
	`status` text DEFAULT 'awaiting' NOT NULL,
	`seat_revision` integer DEFAULT 0 NOT NULL,
	`operation_id` text,
	`payload_digest` text,
	`action` text,
	`approach` text,
	`speech` text,
	`outcome` text,
	`resolution_summary` text,
	`visible_consequences` text,
	`updated_at` text NOT NULL
);
