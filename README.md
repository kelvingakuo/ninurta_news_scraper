This scraper scrapes multiple RSS feeds for business and agriculture news. It's hosted on [morph.io](https://morph.io/documentation)

## Working
1. Every morning, the scraper runs and stores the day's news in a SQLLite table.
2. When the scraping is complete, the scraper notifies an AWS Lambda [defined here](https://github.com/ninurtalabs/rursus-db-lambdas) via an AWS API Gateway endpoint
3. The Lambda gets the day's news by hitting the scraper's data extraction endpoint
4. The Lambda then appends the data to a DynamoDB table which feeds Caesar