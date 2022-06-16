import argparse
from main import upload_screenings, upload_newsletter

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--screenings', default=False, type=bool, help='Scrape screenings?')
    parser.add_argument('--newsletter', default=False, type=bool, help='Scrape newsletter?')
    args = parser.parse_args()

    if args.screenings:
        upload_movies(None, None)
    if args.newsletter:
        upload_newsletter(None, None)
