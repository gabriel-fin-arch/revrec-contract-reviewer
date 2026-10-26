# The offline review in a container: the committed corpus, the rules
# extractor, no API key. Build, and run with a folder for the memos:
#
#   docker build -t revrec-contract-reviewer .
#   docker run --rm -v "$PWD/out:/app/out" revrec-contract-reviewer
#
# On Linux, add --user "$(id -u):$(id -g)" so the memos belong to you and the
# container can write to the folder. Open out/index.html when it's done.
FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.3 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Runtime dependencies only, in their own layer, so a code change doesn't
# reinstall them. There is no lock file in the repo; uv resolves the same
# constraints CI does.
COPY pyproject.toml README.md ./
RUN uv sync --no-install-project

COPY src ./src
COPY corpus ./corpus
RUN uv sync

# Not root. The memos go to /app/out, which is where a host folder is mounted.
RUN useradd --create-home demo && mkdir -p /app/out && chown -R demo /app
USER demo

# review, not demo: demo rebuilds the corpus under /app, which a container run
# with --user as someone other than demo can't write; review only reads it and
# writes to /app/out.
CMD ["revrec", "review", "corpus", "--extractor", "rules", "--out", "out"]
