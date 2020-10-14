import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import pandas as pd


# Set youtube api client
scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

# Disable OAuthlib's HTTPS verification when running locally.
# *DO NOT* leave this option enabled in production.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
api_service_name = "youtube"
api_version = "v3"
client_secrets_file = "PLEASE CHANGE THIS TO YOUR OWN SECRET .json FILE!!!"

# Get credentials and create an API client
flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
    client_secrets_file, scopes)
credentials = flow.run_console()
youtube = googleapiclient.discovery.build(
    api_service_name, api_version, credentials=credentials)


# Get channel information by searching channel id
def channel_list_info(channel_id):
    request = youtube.channels().list(
        part="id, snippet, statistics",
        id=channel_id
    )
    response = request.execute()

    return response


# Get playlist information by searching channel id
def get_playlist_info(channel_id, channel_pagetoken):
    request = youtube.playlists().list(
        part="id, snippet, contentDetails",
        channelId=channel_id,
        maxResults=50,
        pageToken=channel_pagetoken
    )
    response = request.execute()
    return response


# Get video_id by searching playlist id
def get_video_id(playlist_id, playlist_pagetoken):
    request = youtube.playlistItems().list(
        part="id, contentDetails",
        maxResults=50,
        playlistId=playlist_id,
        pageToken=playlist_pagetoken
    )
    response = request.execute()
    return response


# Get video information by searching video id
def get_video_info(video_id):
    request = youtube.videos().list(
        part="id, contentDetails, snippet, statistics, topicDetails",
        id=video_id
    )
    response = request.execute()
    return response


# General channel information for each singer or group, save into one file
def channel_info(singer_list, singer_id_list):
    channel_info_df = pd.DataFrame(columns=['Name', 'Channel_ID', 'Channel_Title',
                                            'Channel_Description', 'Publish_At', 'Channel_View',
                                            'Channel_Comment', 'Channel_Subscriber', 'Channel_Video'])

    for i in range(len(singer_list)):
        channel_response = channel_list_info(singer_id_list[i])
        origin_dict = {'Name': singer_list[i],
                       'Channel_ID': singer_id_list[i],
                       'Channel_Title': channel_response['items'][0]['snippet']['title'],
                       'Channel_Description': channel_response['items'][0]['snippet']['description'],
                       'Publish_At': channel_response['items'][0]['snippet']['publishedAt'],
                       'Channel_View': channel_response['items'][0]['statistics']['viewCount'],
                       'Channel_Comment': channel_response['items'][0]['statistics']['commentCount'],
                       'Channel_Subscriber': channel_response['items'][0]['statistics']['subscriberCount'],
                       'Channel_Video': channel_response['items'][0]['statistics']['videoCount']}
        channel_info_df = channel_info_df.append(origin_dict, ignore_index=True)

    channel_info_df.to_csv('women_singer_channel_info.csv', index=False)


def playlist_video(singer_list, singer_id_list, loop_list=range(10)):
    for i in loop_list:
        playlist_df = pd.DataFrame(columns=['Name', 'Playlist_ID',
                                            'Playlist_Title','Playlist_Description',
                                            'Playlist_Publish_At', 'Playlist_VideoCount'])

        channel_pagetoken = ''
        while True:
            playlist_response = get_playlist_info(singer_id_list[i], channel_pagetoken)
            for k in range(len(playlist_response['items'])):
                playlist_dict = {'Name': singer_list[i],
                               'Playlist_ID': playlist_response['items'][k]['id'],
                               'Playlist_Title': playlist_response['items'][k]['snippet']['title'],
                               'Playlist_Description': playlist_response['items'][k]['snippet']['description'],
                               'Playlist_Publish_At': playlist_response['items'][k]['snippet']['publishedAt'],
                               'Playlist_VideoCount': playlist_response['items'][k]['contentDetails']['itemCount']}
                playlist_df = playlist_df.append(playlist_dict, ignore_index=True)
                print('get', k+1, 'playlist')
            if "nextPageToken" not in playlist_response:
                break
            channel_pagetoken = playlist_response["nextPageToken"]

        video_id_dict = {}
        # video_id_list = []
        video_info_df = pd.DataFrame(columns=['Name', 'Playlist_ID', 'Video_ID', 'Video_Title',
                                              'Video_Description', 'Video_Tags',
                                              'Video_Duration', 'Video_ViewCount',
                                              'Video_LikeCount', 'Video_DislikeCount',
                                              'Video_FavoriteCount', 'Video_CommentCount'])

        for playlist_id in list(playlist_df['Playlist_ID']):
            playlist_pagetoken = ''
            while True:
                video_id_response = get_video_id(playlist_id, playlist_pagetoken)

                for item in video_id_response['items']:
                    if playlist_id in video_id_dict:
                        video_id_dict[playlist_id] = video_id_dict[playlist_id] + [item['contentDetails']['videoId']]
                    else:
                        video_id_dict[playlist_id] = [item['contentDetails']['videoId']]
                   # video_id_list.append(item['contentDetails']['videoId'])

                if "nextPageToken" not in video_id_response:
                    break
                playlist_pagetoken = video_id_response["nextPageToken"]

        videoCount = 0
        for playlist_id in video_id_dict:
            for video_id in video_id_dict[playlist_id]:
                video_response = get_video_info(video_id)

                if len(video_response['items'])== 0:
                    continue

                video_dict = {'Name': singer_list[i],
                              'Playlist_ID': playlist_id,
                              'Video_ID': video_id,
                              'Video_Title': video_response['items'][0]['snippet']['title'],
                              'Video_Description': video_response['items'][0]['snippet']['description'],
                              'Video_Tags': video_response['items'][0]['snippet']['tags'] \
                                  if 'tags' in video_response['items'][0]['snippet'] else 'NA',
                              'Video_Duration': video_response['items'][0]['contentDetails']['duration'],
                              'Video_ViewCount': video_response['items'][0]['statistics']['viewCount'] \
                                  if 'viewCount' in video_response['items'][0]['statistics'] else 'NA',
                              'Video_LikeCount': video_response['items'][0]['statistics']['likeCount'] \
                                  if 'likeCount' in video_response['items'][0]['statistics'] else 'NA',
                              'Video_DislikeCount': video_response['items'][0]['statistics']['dislikeCount'] \
                                  if 'dislikeCount' in video_response['items'][0]['statistics'] else 'NA',
                              'Video_FavoriteCount': video_response['items'][0]['statistics']['favoriteCount'] \
                                  if 'favoriteCount' in video_response['items'][0]['statistics'] else 'NA',
                              'Video_CommentCount': video_response['items'][0]['statistics']['commentCount']\
                                  if 'commentCount' in video_response['items'][0]['statistics'] else 'NA'
                              }
                video_info_df = video_info_df.append(video_dict, ignore_index=True)
                videoCount += 1
                print('get', videoCount, 'video')

        playlist_df.to_csv(singer_list[i]+'_playlist_info.csv', index=False)
        video_info_df.to_csv(singer_list[i]+'_video_info.csv', index=False)


## Test Part
w_singer_list = ['Taylor Swift',
                 'Cardi B',
                 'Camila Cabello',
                 'Ariana Grande',
                 'Dua Lipa',
                 'Halsey',
                 'P!nk',
                 'Nicki Minaj',
                 'Demi Lovato',
                 'Ella Mai']
w_singer_id_list = ['UCqECaJ8Gagnn7YCbPEzWH6g',
                    'UCxMAbVFmxKUVGAll0WVGpFw',
                    'UCio_FVgKVgqcHrRiXDpnqbw',
                    'UC9CoOnJkIBMdeijd9qYoT_g',
                    'UC-J-KZfRV8c13fOCkhXdLiQ',
                    'UCOCgB3xd-B-1qAm-hR9OLrA',
                    'UCE5yTn9ljzSnC_oMp9Jnckg',
                    'UC3jOd7GUMhpgJRBhiLzuLsg',
                    'UCZkURf9tDolFOeuw_4RD7XQ',
                    'UCy1qd93CcOTvOrQ-QM8_pyQ']

m_singer_list = ['Drake',
                 'Post Malone',
                 'Ed Sheeran',
                 'XXXTENTACION',
                 'Bruno Mars',
                 'Travis Scott',
                 'Eminem',
                 'Kendrick Lamar',
                 'Juice WRLD',
                 'Khalid']
m_singer_id_list = ['UCByOQJjav0CUDwxCk-jVNRQ',
                    'UCeLHszkByNZtPKcaVXOCOQQ',
                    'UC0C-w0YjGpqDXGB8IHb662A',
                    'UCM9r1xn6s30OnlJWb-jc3Sw',
                    'UCoUM-UJ7rirJYP8CQ0EIaHA',
                    'UCtxdfwb9wfkoGocVUAJ-Bmg',
                    'UCfM3zsQsOnfWNUppiycmBuw',
                    'UCprAFmT0C6O4X0ToEXpeFTQ',
                    'UC0BletW9phE4xHFM44q4qKA',
                    'UCkntT5Je5DDopF70YUsnuEQ']

g_singer_list = ['Imagine Dragons',
                 'BTS',
                 'Migos',
                 'Maroon 5',
                 'Florida Georgia Line',
                 'Panic! At The Disco',
                 'U2',
                 '5 Seconds Of Summer',
                 'Dan + Shay',
                 'The Rolling Stones']
g_singer_id_list = ['UCT9zcQNlyht7fRlcjmflRSA',
                    'UCLkAepWjdylmXSltofFvsYQ',
                    'UC9YcTIQuhwgoOQqYMKYqW9A',
                    'UCBVjMGOIkavEAhyqpxJ73Dw',
                    'UCRlwyGpIzfhZ6Rdj8mAVyEQ',
                    'UColJTBTSGqaaZr5NOk5r3Pg',
                    'UC4gPNusMDwx2Xm-YI35AkCA',
                    'UC-vKwDHcbPLtjml81ohGRng',
                    'UCx8v-goujcpBVF7QKALgp3g',
                    'UCB_Z6rBg3WW3NL4-QimhC2A']

# Overall Channel information
channel_info(w_singer_list, w_singer_id_list)
channel_info(m_singer_list, m_singer_id_list)
channel_info(g_singer_list, g_singer_id_list)

# playlist information and video information
# loop_list is use to run specific singer(s)

playlist_video(w_singer_list, w_singer_id_list, loop_list=[8])
playlist_video(m_singer_list, m_singer_id_list, loop_list=range(10))
playlist_video(g_singer_list, g_singer_id_list, loop_list=range(10))
