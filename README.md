# Sentinel: AI Agents Authorization System


# Sentinel
Sentinel is a proof-of-concept project developed during a one-day AI Agents hackathon. It showcases a novel approach to authorization systems designed specifically for AI Agents.

## What problem are we solving?
As AI Agents become more powerful and autonomous, traditional authorization systems need to be reimagined. Sentinel demonstrates a new approach to authz systems that caters to the unique needs of AI Agents, who are likely to be the primary consumers of software in the near future.

## Context
AI Agents are typically short-lived and operate across various tools and third-party interactions. Each agent's capabilities should be constrained to the minimum set of permissions required to perform its task.
While complex APIs often allow third-party integrations through API Keys and OAuth tokens, many lack granular control over permissions. Even APIs with more advanced scoping (like GitHub's) may not be ideal for short-lived auth tokens required by AI Agents.

## How does it work?

### The Server
We've built a GitHub API wrapper with three endpoints:

- `/create`: Creates an issue in our repository
- `/solve`: Adds the solved tag to an issue
- `/close`: Closes an issue

The server implements a custom authorization system using Macaroons. Before processing a request, it checks two policies:

- Can the client execute the requested method?
- Are the credentials expired?

### The Client
The client demonstrates the following workflow:

Generates an "admin" token with access to all three endpoints, expiring in 1 day.
Creates two sets of credentials by narrowing the scope of the admin token:

- Set 1: Can only use the create and solve endpoints
- Set 2: Can use all endpoints but expires after 10 seconds


Spawns two agents, each with a different set of credentials.

- Agent 1 (with Set 1 credentials):
   - Creates two issues
   - Marks an issue as solved
   - Attempts to close an issue (which fails due to lack of permissions)


- Agent 2 (with Set 2 credentials):
   - Closes the first issue
   - Waits briefly
   - Attempts to close the second issue (which fails due to expired credentials)



## Why is this important?
This simple scenario demonstrates the possibilities of authorization systems built on the Attribute-based access control (ABAC) paradigm.

By providing fine-grained, time-bound permissions, Sentinel offers a glimpse into how we can better secure and control AI Agent interactions with APIs and services.