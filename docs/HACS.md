# HACS publication and catalog admission

Repository: https://github.com/sluggyly1991/enbw-mobilityplus-homeassistant

- [Repository actions](https://github.com/sluggyly1991/enbw-mobilityplus-homeassistant/actions)
- [HACS and hassfest validation](https://github.com/sluggyly1991/enbw-mobilityplus-homeassistant/actions/workflows/validate.yml)
- [Tests](https://github.com/sluggyly1991/enbw-mobilityplus-homeassistant/actions/workflows/tests.yml)
- [Releases](https://github.com/sluggyly1991/enbw-mobilityplus-homeassistant/releases)
- [HACS general requirements](https://www.hacs.xyz/docs/publish/start/)
- [Integration requirements](https://hacs.xyz/docs/publish/integration/)
- [Default catalog submission](https://www.hacs.xyz/docs/publish/include/)
- [Catalog repository](https://github.com/hacs/default)

## Repository preparation

The package includes one integration under `custom_components/enbw_mobilityplus`, a versioned manifest with code owner/documentation/issue tracker, `hacs.json`, German/English translations, MIT attribution, packaged 256/512px brand icons, privacy-safe examples, issue templates and validation workflows. The published repository also needs a description, topics and enabled issues.

The standalone Python client source and history are preserved from the upstream MIT-licensed repository. This fork adds an independent Home Assistant integration, not a replacement for a core integration.

## Release sequence

1. Push the release commit to the public repository.
2. Enable GitHub Actions in the fork if GitHub has disabled them initially.
3. Wait for HACS and hassfest to pass with **no ignored or disabled checks**; also require all test matrix jobs to pass.
4. Publish a full GitHub release, not just a tag, for that exact commit after successful checks.
5. Verify custom-repository installation using that release.

## Admission to the default catalog

Only the owner or a major contributor can submit. Fork `hacs/default`, create a fresh branch from its current `master`, and add `sluggyly1991/enbw-mobilityplus-homeassistant` alphabetically to the `integration` JSON array.

Complete the current PR template truthfully, linking the release and the exact successful HACS/hassfest workflow runs. Submit from the personal account with maintainer edits enabled. Do not request individual reviews. The HACS team controls review and acceptance; there is no guaranteed date.

Repository preparation, a successful HACS validation, and availability as a custom repository **do not by themselves mean catalog acceptance**. Never claim that acceptance before the catalog PR has been merged.
