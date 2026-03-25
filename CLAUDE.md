# research-papers-plugin

## Release Process

Version lives in `plugins/research-papers/.claude-plugin/plugin.json` (`"version"` field).
Tags use `v{version}` format. Commit message is the bare version number.

```
1. Edit plugin.json — bump "version"
2. git add plugins/research-papers/.claude-plugin/plugin.json
3. git commit -m "{version}"
4. git tag v{version}
5. git push && git push --tags
```
