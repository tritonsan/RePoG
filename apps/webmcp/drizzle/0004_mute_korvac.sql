ALTER TABLE `sessions` ADD `runtime_session_id` text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE `sessions` ADD `runtime_status` text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE `sessions` ADD `turn_deadline` text DEFAULT '' NOT NULL;