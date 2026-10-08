### Overview
`papers-dl` is a command line application for downloading scientific papers.

### Installation
```shell
# install with uv
uv tool install papers-dl

# install with pip
pip install papers-dl
```

### Usage
```shell
# parse DOI identifiers from a file:
papers-dl parse -m doi --path pages/my-paper.html

# parse ISBN identifiers from a file, output matches as CSV:
papers-dl parse -m isbn --path pages/my-paper.html -f csv

# fetch paper with given identifier from any known provider:
papers-dl fetch "10.1016/j.cub.2019.11.030"

# fetch paper from any known Sci-Hub URL with verbose logging on, and store in "papers" directory:
papers-dl -v fetch -p "scihub" -o "papers" "10.1107/s0907444905036693"

# fetch paper from specific Sci-Hub URL:
papers-dl fetch -p "sci-hub.ee" "10.1107/s0907444905036693"

# fetch paper from SciDB (Anna's Archive):
papers-dl fetch -p "scidb" "10.1107/s0907444905036693"

# discover an openly accessible PDF from a DOI or publisher landing page:
papers-dl fetch -p "publisher" "https://joss.theoj.org/papers/10.21105/joss.01112"

# retrieve an article PDF from the public PMC Article Datasets:
papers-dl fetch -p "pmc" "10.1126/sciadv.1602552"
```

The default `all` provider selection includes `publisher`, `pmc`, `zenodo`,
`figshare`, `ntrs`, `osti`, `hal`, `scihub`, `scidb`, and `arxiv`.
Providers can also be selected with a comma-separated list.

`publisher` follows DOI redirects and reads `citation_pdf_url` metadata,
PDF-typed links, and embedded PDF URLs. Relative links resolve against the final
landing-page URL (including an HTML base URL when present). Direct PDF URLs work
too, including URLs without a `.pdf` extension. Publisher pages that require
authentication or JavaScript challenges may not be accessible.

`pmc` accepts DOI identifiers/URLs, PubMed IDs, and PMC IDs (including explicit
versions such as `PMC1193645.2`). It resolves identifiers through the
[Europe PMC literature API](https://europepmc.org/RestfulWebService) and downloads
the article PDF identified by metadata in
[NLM's public PMC Article Datasets](https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/).
It discovers available versions instead of assuming version 1 exists, preferring
published articles to author manuscripts. Only PDFs distributed in this public
dataset are available; a PMC record alone does not guarantee a downloadable PDF.
Article-level license terms still apply. NLM is the source of the PMC data.

Five additional repository providers use public metadata and download endpoints;
none needs an account, login, or API key:

| Provider | Accepted identifiers | PDF discovery |
| --- | --- | --- |
| `zenodo` | Zenodo record URLs and `10.5281/zenodo.*` DOIs | Open-record file metadata and file content links |
| `figshare` | Figshare and institutional article URLs, including version URLs; repository DOIs | Exact DOI lookup or article/version metadata, then PDF file download URLs |
| `ntrs` | NASA NTRS citation URLs or `ntrs:20170009584` | Public citation metadata's PDF download links |
| `osti` | OSTI record URLs, `osti:3413920`, or DOIs | Exact DOI lookup or record metadata's full-text links |
| `hal` | HAL deposit URLs/IDs, explicit versions, or DOIs | HAL search metadata's main-document URL, preserving an explicit version |

```shell
papers-dl fetch -p zenodo 10.5281/zenodo.13886268
papers-dl fetch -p figshare 10.25405/ncl.34202931.v1
papers-dl fetch -p ntrs https://ntrs.nasa.gov/citations/20170009584
papers-dl fetch -p osti 10.2172/3413920
papers-dl fetch -p hal hal-01232674v1
```

These providers retrieve only files offered by the repositories' public APIs.
Records without an available PDF produce no result; restricted or embargoed
files are not unlocked. Figshare download redirects may contain short-lived
signed URLs, so discovery uses the stable download URL from its public API.

Downloads must have a successful HTTP status and PDF signature; an HTML error
page is never saved as a PDF, and PDFs served as binary data are accepted. The
success message reports the final URL of the download that actually completed.

### Tests

```shell
uv run python -m unittest discover -v
```

The open-access integration tests make real requests to publishers, Europe PMC,
NLM's public S3 dataset, and all five additional repositories. They run the CLI,
open the resulting PDFs, and check article text and page counts. They require
network access and do not mock external services.

### About

`papers-dl` attempts to be a comprehensive tool for gathering research papers from popular open libraries. There are other solutions for this (see "Other tools" below), but `papers-dl` is trying to fill its own niche:

- comprehensive: other tools usually work with a single library, while `papers-dl` is trying to support a collection of popular libraries.
- performant: `papers-dl` tries to improve search and retrieval times by making use of concurrency where possible.

That said, `papers-dl` may not be the best choice for your specific use case right now. For example, if you require features supported by a specific library, one of the more mature and specialized tools listed below may be a better option.

`papers-dl` was initially created to serve as an extractor for [ArchiveBox](https://archivebox.io), a powerful solution for self-hosted web archiving.

This project started as a fork of [scihub.py](https://github.com/zaytoun/scihub.py).

### Other tools

- [Scidownl](https://pypi.org/project/scidownl/)
- [arxiv-dl](https://pypi.org/project/arxiv-dl/)
- [Anna's Archive API](https://github.com/dheison0/annas-archive-api)

### Roadmap

`papers-dl`'s CLI is not yet stable.

Short-term roadmap:

**parsing**
- add support for parsing more identifier types like PMID and ISSN

**fetching**
- add support for downloading formats other than PDFs, like HTML or epub

**searching**
- add a CLI command for searching libraries for papers and metadata
