# SCRAPER

This code scrapes screenings from movie theater websites and the content of our newsletter.

## Manual run
```
python manual_run.py --screenings True --newsletter True
```

## How to set up the function on GCP
```
gcloud functions deploy upload_movies --trigger-topic upload_movies --entry-point upload_movies --runtime python37 --memory 256MB --project website-cine --region "europe-west1" --timeout 500s
gcloud functions deploy upload_newsletter --trigger-topic upload_newsletter --entry-point upload_newsletter --runtime python37 --memory 256MB --project website-cine --region "europe-west1" --timeout 500s
```
