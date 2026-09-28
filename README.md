# homebrew-net-benchmark

Homebrew tap for [net-benchmark](https://github.com/net-benchmark/net-benchmark): DNS, HTTP, and SSL/TLS network benchmarking from a single CLI.

## Install

```bash
brew tap net-benchmark/net-benchmark
brew trust net-benchmark/net-benchmark
brew install net-benchmark
```

Homebrew 6.0 and later refuse to load formulae from a third-party tap until you trust it, which is what the `brew trust` line does. Earlier versions don't have that command; skip it.

Check that it worked:

```bash
net-benchmark --version
net-benchmark dns --help
net-benchmark http --help
```

### Expect a long first install

This tap has no prebuilt bottles. Homebrew builds net-benchmark and its Python dependencies (numpy, pandas, matplotlib, pillow, cryptography) from source, so the first install can take a while. If you'd rather not wait, `pip install net-benchmark` or the Docker image gets you the same CLI faster (see below).

## Upgrade and uninstall

```bash
brew update
brew upgrade net-benchmark

brew uninstall net-benchmark
brew untap net-benchmark/net-benchmark
```

## Other ways to install

```bash
pip install net-benchmark
docker pull joeovo/net-benchmark:latest    # also on GHCR: ghcr.io/net-benchmark/net-benchmark
```

Documentation: https://net-benchmark.readthedocs.io/en/latest/

## How this tap is maintained

- `Formula/net-benchmark.rb` is a Python virtualenv formula. Every dependency is pinned as a `resource` with its own URL and sha256.
- `.github/workflows/auto-bump.yml` checks PyPI daily at 06:00 UTC. When a newer release exists, it runs `scripts/update_formula.py` to regenerate the formula and proposes the change from an `auto-bump-formula` branch.
- `.github/workflows/test-formula.yml` runs `brew install --build-from-source`, `brew test`, and `brew audit --new --strict --online` on macOS. Expect it to take a long time, for the same build-from-source reason as above.

## Issues

- Problems with the CLI itself: [net-benchmark issues](https://github.com/net-benchmark/net-benchmark/issues)
- Problems installing through this tap: open an issue here.

## License

net-benchmark is MIT-licensed; see the [main repository](https://github.com/net-benchmark/net-benchmark/blob/main/LICENSE).
