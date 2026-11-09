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
5. Verify that the release is available to the catalog entry; retain custom-repository installation as a fallback.

## Default catalog status

Accepted on **9 November 2026**: [hacs/default#13490](https://github.com/hacs/default/pull/13490), merged by `frenck`. Users can find **EnBW mobility+ History** through HACS search. Both READMEs lead with this route and retain custom repository installation only as a fallback, following the [review feedback](https://github.com/hacs/default/pull/13490#pullrequestreview-5825617592).

Catalog inclusion does not mean official EnBW support. The integration remains an unofficial client of a non-public account API.
