import { index, integer, sqliteTable, text, uniqueIndex } from 'drizzle-orm/sqlite-core';

export const sessions = sqliteTable('sessions', {
  sessionId: text('session_id').primaryKey(), scenarioId: text('scenario_id').notNull(), status: text('status').notNull().default('awaiting_join'),
  resolverMode: text('resolver_mode').notNull().default('fixture'), manifestJson: text('manifest_json').notNull().default('{}'), bridgeTokenHash: text('bridge_token_hash').notNull().default(''), inviteTokenHash: text('invite_token_hash').notNull().default(''), expiresAt: text('expires_at').notNull().default(''),
  revision: integer('revision').notNull().default(0), currentTurn: integer('current_turn').notNull().default(1), createdAt: text('created_at').notNull(), updatedAt: text('updated_at').notNull(),
}, (table) => [index('idx_sessions_status').on(table.status)]);

export const sessionSeats = sqliteTable('session_seats', {
  seatId: text('seat_id').primaryKey(), sessionId: text('session_id').notNull(), characterId: text('character_id').notNull(), status: text('status').notNull().default('ready'), boundAt: text('bound_at'), updatedAt: text('updated_at').notNull(),
}, (table) => [index('idx_session_seats_session').on(table.sessionId), uniqueIndex('idx_session_seats_character').on(table.sessionId, table.characterId)]);

export const turns = sqliteTable('turns', {
  turnId: text('turn_id').primaryKey(), sessionId: text('session_id').notNull(), turnNumber: integer('turn_number').notNull(), sceneId: text('scene_id').notNull(), sourceRevision: integer('source_revision').notNull(), briefJson: text('brief_json').notNull().default('{}'), status: text('status').notNull().default('queued'), openedAt: text('opened_at'), resolvedAt: text('resolved_at'),
}, (table) => [uniqueIndex('idx_turns_session_number').on(table.sessionId, table.turnNumber), index('idx_turns_session_status').on(table.sessionId, table.status)]);

export const intents = sqliteTable('intents', {
  intentId: text('intent_id').primaryKey(), sessionId: text('session_id').notNull(), turnId: text('turn_id').notNull(), seatId: text('seat_id').notNull(), operationId: text('operation_id').notNull(), payloadDigest: text('payload_digest').notNull(), intentPayload: text('intent_payload').notNull().default('{}'), action: text('action').notNull(), approach: text('approach').notNull(), speech: text('speech').notNull(), status: text('status').notNull(), outcome: text('outcome').notNull(), resolutionSummary: text('resolution_summary').notNull(), visibleConsequences: text('visible_consequences').notNull(), createdAt: text('created_at').notNull(), resolvedAt: text('resolved_at').notNull(),
}, (table) => [uniqueIndex('idx_intents_session_operation').on(table.sessionId, table.operationId), index('idx_intents_turn').on(table.turnId)]);

export const sessionEvents = sqliteTable('session_events', {
  eventId: text('event_id').primaryKey(), sessionId: text('session_id').notNull(), sequence: integer('sequence').notNull(), eventType: text('event_type').notNull(), publicPayload: text('public_payload').notNull(), seatPayload: text('seat_payload').notNull(), createdAt: text('created_at').notNull(),
}, (table) => [uniqueIndex('idx_session_events_sequence').on(table.sessionId, table.sequence)]);
