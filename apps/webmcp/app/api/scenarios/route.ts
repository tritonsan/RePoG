import { scenarios } from '@/lib/scenarios';
import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    ok: true,
    scenarios: Object.values(scenarios).map((scenario) => ({
      scenario_id: scenario.scenarioId,
      title: scenario.title,
      genre: scenario.genre,
      character: { character_id: scenario.character.id, display_name: scenario.character.name, role: scenario.character.role },
      resolver_mode: 'fixture',
    })),
  }, { headers: { 'Cache-Control': 'public, max-age=300' } });
}
