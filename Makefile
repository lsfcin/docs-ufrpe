# Verification contract — see code/ROADMAP-verify.md G5. The same checks the PR workflow runs, offline.
# verify-fast: JS syntax, every document header, the census unit tests. verify-full adds the search index build.
verify-fast:
	for f in site/*.js; do node --check "$$f" || exit 1; done
	python3 .github/scripts/verificar.py
	python3 -m unittest discover .github/scripts

verify-full: verify-fast
	python3 .github/scripts/indexar.py . --saida "$${TMPDIR:-/tmp}/busca.json"

.PHONY: verify-fast verify-full
