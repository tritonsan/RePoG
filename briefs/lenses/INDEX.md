# Session 0 Lens Index

Lenses are composable Session 0 question packs. They help GPT-5.6 turn an
ambiguous pitch into useful choices without turning genre labels into hard
rules. Read only the selected candidate lens briefs during Session 0. Once the
Designer accepts a bundle, materialize the result in `campaign/play_profile.yaml`
and the campaign notes; do not load these briefs during ordinary play.

Available setting lenses:

- `fantasy.md`
- `realistic.md`
- `cyberpunk.md`

Available play lenses:

- `survival.md`

## Composition Contract

1. A campaign may use zero, one, or several lenses.
2. A lens proposes questions, world pressures, and optional mechanics.
3. No mechanic is enabled until the Designer approves it and it appears in
   `mechanics.modules`.
4. Resolve collisions using this precedence: explicit Designer decision;
   safety, canon, and research limits; approved mechanics; lens suggestion;
   general default.
5. Record every collision and its resolution in
   `play_profile.yaml.lens_conflicts_resolved` and the World Operating Model.
6. A custom setting may borrow selected questions without accepting a label.

## Starter Bundle Use

After the campaign pitch, produce 2 to 4 distinct bundles. Every bundle names
its lenses, feel, tracking load, approximate speed effect, optional mechanics,
and why it fits. Recommend one without silently selecting it. The Designer may
`accept`, `mix`, `change`, `default`, or `defer` as defined in
`campaign/session_zero.md`.
