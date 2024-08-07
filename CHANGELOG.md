# Changelog

## [0.1.8](https://github.com/release-engineering/ASGI-Middlewares/compare/v0.1.7...v0.1.8) (2024-08-08)


### Bug Fixes

* Handle situations where client in scope is set to None. ([#18](https://github.com/release-engineering/ASGI-Middlewares/issues/18)) ([9821c3c](https://github.com/release-engineering/ASGI-Middlewares/commit/9821c3ce6c979e2e0c5f59a9072f2450f568f301))

## [0.1.7](https://github.com/release-engineering/ASGI-Middlewares/compare/v0.1.6...v0.1.7) (2024-07-09)


### Features

* Make PathId middleware not duplicate trace_id when Flask application is used. ([#16](https://github.com/release-engineering/ASGI-Middlewares/issues/16)) ([d7c492b](https://github.com/release-engineering/ASGI-Middlewares/commit/d7c492b5e0947dd1e4f3c707aa1356cba09ad5c8))

## [0.1.6](https://github.com/release-engineering/ASGI-Middlewares/compare/v0.1.5...v0.1.6) (2024-07-03)


### Features

* Improve documentation, make prometheus ignore invalid path_id by default. ([8b0de7e](https://github.com/release-engineering/ASGI-Middlewares/commit/8b0de7ebb7d05a9f1f56b42a052658c652804a83))

## [0.1.5](https://github.com/release-engineering/ASGI-Middlewares/compare/v0.1.4...v0.1.5) (2024-07-02)


### Features

* Improve PathID middleware. ([77a8cd5](https://github.com/release-engineering/ASGI-Middlewares/commit/77a8cd53c36865fb2f5c07c53c15a50bf2c6fb5a))

## [0.1.4](https://github.com/release-engineering/ASGI-Middlewares/compare/v0.1.3...v0.1.4) (2024-07-01)


### Bug Fixes

* Non-string parameters no longer cause errors in path-id parsing. ([#12](https://github.com/release-engineering/ASGI-Middlewares/issues/12)) ([b09435b](https://github.com/release-engineering/ASGI-Middlewares/commit/b09435bd55919360f3242ef768fdc66bbffae988))

## [0.1.3](https://github.com/release-engineering/ASGI-Middlewares/compare/v0.1.2...v0.1.3) (2024-06-28)


### Features

* Make context variables accessible from outside. ([#10](https://github.com/release-engineering/ASGI-Middlewares/issues/10)) ([2d06371](https://github.com/release-engineering/ASGI-Middlewares/commit/2d06371fdf489f28460750da9198a2ab8e37e0b1))

## [0.1.2](https://github.com/release-engineering/ASGI-Middlewares/compare/v0.1.1...v0.1.2) (2024-06-27)


### Bug Fixes

* Enable Bandit in CI/CD. ([#8](https://github.com/release-engineering/ASGI-Middlewares/issues/8)) ([b7636df](https://github.com/release-engineering/ASGI-Middlewares/commit/b7636df542ef92b04382de192f5b7189c01f6a56))

## [0.1.1](https://github.com/release-engineering/ASGI-Middlewares/compare/v0.1.0...v0.1.1) (2024-06-27)


### Bug Fixes

* Unify PyPI and pyproject project names. ([#6](https://github.com/release-engineering/ASGI-Middlewares/issues/6)) ([322c523](https://github.com/release-engineering/ASGI-Middlewares/commit/322c523100b02ef4976086d2825ca3e5abe0e18e))

## 0.1.0 (2024-06-26)


### Features

* Check if field is supported for extended logging. ([63d6c0c](https://github.com/release-engineering/ASGI-Middlewares/commit/63d6c0c34ef7a20c1f1bbf1a7384899892c5c58f))
