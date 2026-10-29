# Realized Blend Application

`realized-blend-application` owns concrete runtime and JSON persistence adapters
for the dependency-light `realized-blend` domain.

Its public modules project governed artifacts and runtime capabilities into
canonical Blend operators, translate skill-composition payloads to Blend
workflows, adapt explicit skill-composition invocation to Blend execution, and
persist workflow plans, runs, and shared world metadata through the canonical
repository ports.

The package does not define Blend domain values, own workstation sessions,
select skills from natural-language requests, decide governance policy, supply
host realizers, invoke models, or parse user-facing exchange formats.
