ALTER TABLE `intents` ADD `intent_payload` text DEFAULT '{}' NOT NULL;--> statement-breakpoint
ALTER TABLE `sessions` ADD `resolver_mode` text DEFAULT 'fixture' NOT NULL;--> statement-breakpoint
ALTER TABLE `sessions` ADD `manifest_json` text DEFAULT '{}' NOT NULL;--> statement-breakpoint
ALTER TABLE `sessions` ADD `bridge_token_hash` text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE `sessions` ADD `expires_at` text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE `turns` ADD `brief_json` text DEFAULT '{}' NOT NULL;