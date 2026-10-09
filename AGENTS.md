# Shared instructions

Read STARTING-POINT.md, coordination/RULES.md and coordination/STATUS.md before working.

Keep the project basic and narrowly scoped. Do not invent an application architecture, add dependencies, or start parallel product implementation merely because folders exist.

The coordinator owns shared rules, assignments and status. Workers read their assigned file, stay within its ownership, and write questions to inbox and results to outbox. Workers must not overwrite each other's edits or change the agreed approach independently.

Do not ask the user to copy messages between agents. Use available authorized coordination tools and repository files. Clearly distinguish written conventions from implemented automatic coordination.
