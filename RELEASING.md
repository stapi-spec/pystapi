# Releasing

1. Determine which package you're releasing
2. Determine the next version, following [semantic versioning](https://semver.org/)
3. Create a release branch: `git checkout -b release/{package}-v{version}`
4. Update that package's CHANGELOG with:
   - A new header with the new version
   - A new link at the bottom of the CHANGELOG for that header
5. `git push -u origin`
6. Once approved, merge the PR
7. `git checkout main && git pull && scripts/release {package}`
8. Go to the draft release href provided by the script, update that Github release with information from the CHANGELOG, and publish it
9. Github actions will automatically publish a new PyPI release

> [!IMPORTANT]
> You'll need to set up [.netrc authentication](https://pygithub.readthedocs.io/en/stable/examples/Authentication.html#netrc-authentication) to use `scripts/release`.
> The tag format created by the script (`{package}/v{version}`) is very important, because that's how we discover which package to build and publish in Github Actions.
