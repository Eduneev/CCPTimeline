import json
import os
import vimeo
import time
from datetime import datetime
import argparse
import pandas as pd

RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
MAX_RETRIES = 10

CONFIG_FILE = "config.json"

def get_client(config):

    if 'client_id' not in config or 'client_secret' not in config:
        raise Exception('We could not locate your client id or client secret ' +
                    'in `' + config_file + '`. Please create one, and ' +
                    'reference `config.json.example`.')

    # Instantiate the library with your client id, secret and access token
    # (pulled from dev site)
    client = vimeo.VimeoClient(
        token=config['access_token'],
        key=config['client_id'],
        secret=config['client_secret']
    )

    return client

def download(client, output):
    print ('Downloading videos')
    try:

        about_me = client.get('/me')

        # Make sure we got back a successful response.
        assert about_me.status_code == 200

        #write_to_file(about_me.json(), output)

        per_page = 100
        all_videos = []
        try:
            for i in range(1,41):
                url = "/me/videos?per_page="+str(per_page)+"&page="+str(i)
                data = client.get(url, params={"fields": "parent_folder.name,parent_folder.metadata.connections.items.total,name,duration"})
                #data = client.get(url)
                assert data.status_code == 200

                val = data.json()
                data = val['data']
                all_videos.extend(data)
        except:
            print(len(all_videos))

        print(len(all_videos))
        handle_data(all_videos, output)
        
    except vimeo.exceptions.VideoDownloadFailure as e:
        print('Server reported: %s' % e.message)

def handle_data(data, out):

    for i in range(len(data)):
        data[i]['duration'] = round(data[i]['duration']/60.0, 2)
        if data[i]['parent_folder']:
            data[i]['total_videos'] = int(data[i]['parent_folder']['metadata']['connections']['items']['total'])
            data[i]['parent_folder'] = data[i]['parent_folder']['name']

    df = pd.DataFrame(data)

    print("writing to csv file")
    df.to_csv(out)

    print("writing to excel file")
    #df.to_excel("out.xslx")


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description='Process meeting info.')
    argparser.add_argument("--output", default="out.csv", help="Specifies output file")
    args = argparser.parse_args()
    try:
        config = json.load(open(CONFIG_FILE))
        project_id = config['project_id']
        client = get_client(config)
        # If video not already published to vimeo, publish it
        print("Successfully loaded client")
        try:
            download(client, args.output)
            #upload(client,file_url, args.name, args.meetingid, project_id)
        except (HttpError, e):
            print ("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
    
    except:
        print("Unable to open config file")