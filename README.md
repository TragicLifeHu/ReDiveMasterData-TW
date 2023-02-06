# Re:Dive TW Master Data Downloader

Guess the TruthVersion of Princess Connect! Re:Dive Taiwan server and download the database  
Support both local machine and GitHub Action automation workflow

## Feature

* Fetch Database new version
* Download database file and decrypt
* (TBD) Database diff

## Outputs

* `version.json` - Contains current TruthVersion and hash
* `redive_tw.db` - The latest database
* `redive_tw.db.br` - Same as above, but compressed with Brotli
* `prev.redive_tw.db` - Previous version of the database (Disabled for GitHub Action)
