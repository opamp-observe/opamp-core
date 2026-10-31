# Contributing

Thank you for helping improve this project. Contributions of all sizes are welcome, including bug reports, documentation, tests, feature requests, accessibility improvements, and code.

This guide describes the contribution workflow and the project's approach to contributions under the Apache License, Version 2.0.

## Before you start

- Read the [README](README.md) for the project's purpose, supported environments, and development setup.
- Search existing issues, pull requests and roadmap documents to avoid duplicating work.
- For substantial features, architectural changes, new dependencies, or changes to public interfaces, open an issue to discuss the approach before implementation.
- Small fixes and documentation corrections can usually go straight to a pull request.
- If you are new to the project, look for issues labelled `good first issue` or `help wanted`, where available.

## Community conduct

Be respectful, constructive, and considerate. Discuss ideas and technical trade-offs without personal attacks. Welcome questions, explain your reasoning, and respect other contributors' time.

Follow the repository's code of conduct, if provided. Raise conduct concerns privately with the maintainers using the contact details published in the repository.

## Sharing your experiences and use cases

It helps the maintainers to hear about the use cases, experiences of using the solutions developed. This helps us understand the value of the community development and the prioritization of features.

## Reporting bugs

Use the repository's issue tracker and its issue template, if available. Include:

- A clear description of the problem and its impact.
- The project version or commit, operating system, and relevant dependency versions.
- The smallest reproducible example and the steps needed to run it.
- Expected behaviour and actual behaviour.
- Relevant logs, error messages, or screenshots, with sensitive information removed.
- Any workaround you have found.

Do not include credentials, access tokens, personal information, or confidential data.

### Security vulnerabilities

Report suspected security vulnerabilities privately. Follow `SECURITY.md` if present. Otherwise,  contact a maintainer(s) privately by opening a public issue requesting a security contact without disclosing the vulnerability.

## Suggesting improvements

Describe the problem you want to solve, who would benefit, and the proposed behaviour. Include examples, alternatives considered, compatibility implications, and any operational or maintenance costs. An agreed problem is a useful starting point even when the implementation is undecided.

## Development workflow

1. Fork the repository, or use a branch if you have write access.
2. Clone your fork and create a descriptive branch from the default branch, for example `fix/config-validation` or `docs/setup-guide`.
3. Follow the development setup instructions in the README or linked developer documentation. Use the supported toolchain and committed dependency lock files where provided.
4. Make a focused change. Keep unrelated refactoring and formatting changes separate.
5. Add or update tests and documentation as appropriate.
6. Run the relevant checks documented by the project and inspect your diff for accidental changes or sensitive data.
7. Commit your work and open a pull request against the default branch, unless a maintainer requests a different target.

If setup instructions are missing or incorrect, raise an issue or propose a documentation correction. Do not assume undocumented commands are required.

## Code, tests, and documentation

- Follow the surrounding code style, naming conventions, and existing architecture. If you're not sure, then reach out.
- Prefer clear, maintainable solutions and descriptive names.
- Explain non-obvious decisions in comments; document public interfaces and changed behaviour.
- Validate inputs and handle failures in a way consistent with the project.
- Add regression tests for bug fixes where practical. Cover relevant success paths, failure paths, and boundary conditions for new behaviour.
- Consider accessibility, security, performance, and compatibility where the change affects them.
- Update examples, configuration documentation, API specifications, and release notes when applicable.
- Avoid committing build outputs, local environment files, generated credentials, or unrelated editor settings.

Use the project's documented formatter, linter, type checker, and test commands. In your pull request, report which checks you ran and explain any checks you could not run. New dependencies should have a clear purpose and an acceptable maintenance and licensing impact.

## Commits and pull requests

Write commit messages that explain the change and its purpose. Follow any repository-specific commit convention; otherwise use a short, descriptive subject and additional context when needed.

Your pull request should include:

- The problem being addressed and the resulting behaviour.
- Links to related issues; use a closing keyword only when the change fully resolves an issue.
- A brief description of significant design decisions or trade-offs.
- Tests and other validation performed, including limitations.
- Screenshots or examples for visible changes, where useful.
- Any breaking changes, migration steps, or new dependencies.

Use a draft pull request when you want early feedback or the work is incomplete. Keep the description current as the implementation changes.

### Review and merge

Maintainers review contributions for correctness, maintainability, scope, tests, documentation, security, and licensing. Automated checks must pass where configured, and a maintainer must approve the change before merging.

Respond constructively to feedback and explain disagreements with examples or evidence. Maintainers may request changes, suggest a smaller scope, or decline work that does not fit the project's direction. Review timing depends on maintainer availability.

## Licensing and contribution rights

### Apache License 2.0

The project is licensed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0). The repository's [LICENSE](LICENSE) file contains the governing terms.

Unless you explicitly state otherwise, contributions you intentionally submit for inclusion in the project are submitted under Apache License 2.0, as described in Section 5 of that licence. If you propose different terms, raise them with the maintainers before submitting the material for inclusion; acceptance is not automatic.

You retain copyright in your original work. Contributing does not transfer copyright ownership to the maintainers. Apache License 2.0 includes copyright and patent grants subject to its terms; see Sections 2 and 3 for their scope and conditions.

Only submit material that you have the right to contribute. Obtain any necessary employer, client, or other rights-holder permission before submitting work.

### Third-party material and notices

- Identify copied or adapted code, documentation, images, data, and other third-party material in your pull request, including its source and licence.
- Check licensing compatibility and discuss uncertain cases with a maintainer before inclusion. Public availability alone is not permission to reuse material.
- Preserve applicable copyright, patent, trademark, attribution, and licence notices.
- Follow the repository's existing file-header convention. Where the project uses SPDX identifiers, use `SPDX-License-Identifier: Apache-2.0` for material licensed on that basis. An identifier does not replace the full project licence or third-party notices.
- Mark modified third-party files as changed where Apache License 2.0 requires it, following the project's established convention.
- Preserve relevant attribution from an upstream `NOTICE` file when incorporating Apache-licensed material. Update the project's `NOTICE` or third-party notices when required. A `NOTICE` file is not required merely because a project uses Apache License 2.0, and it must not be used to add licence restrictions.
- Do not replace third-party licence headers with the project's own header or claim ownership of another contributor's work.

### Contributor agreements and sign-off

This guide does not introduce a separate Contributor License Agreement (CLA) or mandatory Developer Certificate of Origin (DCO) sign-off. Apache License 2.0 does not itself require either process. If the repository separately requires a CLA or DCO, follow its published instructions; maintainers should make that requirement clear before accepting contributions.

A Git `Signed-off-by` trailer records a sign-off under the applicable contribution policy; it is different from a cryptographic commit signature.

## Getting help

Use the repository's discussions area or issue tracker for contribution questions. Include enough context for others to help, and link to existing discussions when relevant.

Thank you for contributing your time and expertise.
