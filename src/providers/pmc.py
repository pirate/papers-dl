"""Find article PDFs in NLM's public PMC Article Datasets."""

import asyncio
import re
from urllib.parse import unquote, urlsplit, urlunsplit
from xml.etree import ElementTree

import aiohttp
from loguru import logger

from parse.parse import parse_ids_from_text

SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
DATASET = "https://pmc-oa-opendata.s3.amazonaws.com/"
TIMEOUT = aiohttp.ClientTimeout(total=30)
S3_NAMESPACE = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}


async def get_urls(session, identifier):
    identifier = unquote(identifier.strip())
    if identifier.startswith(("http://", "https://")):
        identifier = urlsplit(identifier).path.strip("/")
    pmcid = re.search(r"\bPMC\d+(?:\.\d+)?\b", identifier, re.IGNORECASE)
    dois = parse_ids_from_text(identifier, ["doi"])
    if pmcid:
        identifier = pmcid.group().upper()
        query = None
    elif dois:
        identifier = dois[0]["id"]
        query = f'DOI:"{identifier}"'
    elif identifier.isdigit():
        query = f"EXT_ID:{identifier} AND SRC:MED"
    else:
        return []

    logger.info("Searching PubMed Central: {}", identifier)
    try:
        if query:
            async with session.get(
                SEARCH,
                params={"query": query, "format": "json"},
                timeout=TIMEOUT,
            ) as response:
                response.raise_for_status()
                result = await response.json()
            records = result.get("resultList", {}).get("result", [])
            pmcids = [
                record["pmcid"]
                for record in records
                if record.get("pmcid")
                and (
                    record.get("doi", "").lower() == identifier.lower()
                    if dois
                    else str(record.get("pmid")) == identifier
                )
            ]
        else:
            pmcids = [identifier]

        urls = []
        for pmcid in dict.fromkeys(pmcids):
            if not re.fullmatch(r"PMC\d+(?:\.\d+)?", pmcid):
                continue
            if "." in pmcid:
                keys = [f"metadata/{pmcid}.json"]
            else:
                # List available metadata, not article files: supplements can
                # also be PDFs, and version 1 is not necessarily distributed.
                keys = []
                params = {"list-type": "2", "prefix": f"metadata/{pmcid}."}
                while True:
                    async with session.get(
                        DATASET, params=params, timeout=TIMEOUT
                    ) as response:
                        response.raise_for_status()
                        listing = ElementTree.fromstring(await response.read())
                    keys.extend(
                        key.text
                        for key in listing.findall("s3:Contents/s3:Key", S3_NAMESPACE)
                        if re.fullmatch(rf"metadata/{pmcid}\.\d+\.json", key.text or "")
                    )
                    token = listing.findtext(
                        "s3:NextContinuationToken", namespaces=S3_NAMESPACE
                    )
                    if not token:
                        break
                    params["continuation-token"] = token

            versions = []
            for key in keys:
                async with session.get(DATASET + key, timeout=TIMEOUT) as response:
                    # Only licensed, publicly distributed versions are in S3.
                    if response.status == 404:
                        continue
                    response.raise_for_status()
                    # NLM's S3 JSON objects are served as binary/octet-stream.
                    metadata = await response.json(content_type=None)
                if metadata.get("pdf_url"):
                    versions.append(metadata)
            # Prefer published articles to author manuscripts, then the newest
            # deposited version of that kind. Do not pick a supplemental PDF.
            versions.sort(
                key=lambda v: (v.get("is_manuscript", False), -int(v["version"]))
            )
            for metadata in versions:
                pdf_url = metadata["pdf_url"]
                url = urlsplit(pdf_url)
                if url.scheme == "s3" and url.netloc == "pmc-oa-opendata":
                    pdf_url = urlunsplit(
                        (
                            "https",
                            "pmc-oa-opendata.s3.amazonaws.com",
                            url.path,
                            url.query,
                            "",
                        )
                    )
                if urlsplit(pdf_url).scheme in ("https", "http"):
                    urls.append(pdf_url)
                    break
        return urls
    except (
        aiohttp.ClientError,
        asyncio.TimeoutError,
        ValueError,
        ElementTree.ParseError,
    ) as error:
        logger.info("Couldn't find a PubMed Central PDF: {}", error)
        return []
