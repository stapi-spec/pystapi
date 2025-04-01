# Releasing

1. Determine which package you're releasing
2. Determine the next version, following [semantic versioning](https://semver.org/)
3. Create a release branch: `git checkout -b release/{package}-v{version}`
4. Update that package's CHANGELOG with:
    - A new header with the new version
    - A new link at the bottom of the CHANGELOG for that header
5. `git push -u origin`
6. Once approved, merge the PR
7. `git checkout main && git pull && git tag {package}-v{version} && git push {package}-v{version}`
8. Github actions will automatically publish the release on tag push
9. Create a new [release](https://github.com/stapi-spec/pystapi/releases) pointing to the new tag
