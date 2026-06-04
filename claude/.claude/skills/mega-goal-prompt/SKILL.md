# Mega-Goal Prompt Generator

This skill helps users define autonomous goals for Claude Code by conducting a structured interview. The process extracts key information about the task through six branches:

**Branch 1** focuses on the single, falsifiable outcome—what "done" looks like in one sentence.

**Branch 2** gathers context: project details, tech stack, current state, working directory, constraints, and audience.

**Branch 3** establishes 3–5 measurable success criteria, each tied to verifiable proof (test output, file counts, commands).

**Branch 4** identifies off-limits areas—files to preserve, actions requiring approval, tool restrictions.

**Branch 5** calibrates quality standards based on whether there's a UI, coding conventions, and deployment scope.

**Branch 6** specifies the final deliverable proof needed to confirm completion.

**Critical rules**: Ask one question at a time and wait for responses. Offer recommended answers users can accept or modify. Never move to implementation before resolving branches 1–3. Don't accept deferred decisions. Stop interviewing once branches 1–3 are complete and the user approves, then output the filled mega prompt as a code block ready to paste into Claude Code.

The skill references an external mega-prompt template file to structure the final output.
