#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, hashlib, re, inspect, json
from io import open
import json
import xml.etree.ElementTree as ET

def Start():
    Log("Starting up ...")

class YoutubeDLAgent(Agent.TV_Shows):
    name, primary_provider, fallback_agent, contributes_to, languages, accepts_from = (
    'Youtube-DL', True, False, None, [Locale.Language.English, ], None)

    def search(self, results, media, lang, manual=False):
        results.Append(MetadataSearchResult(
            id='youtube-dl|{}|{}'.format(media.filename, media.openSubtitlesHash),
            name=media.title,
            year=None,
            lang=lang,
            score=100
        ))

        results.Sort('score', descending=True)

    def update(self, metadata, media, lang):
        Log("".ljust(157, '='))

        file = ""

        # Get the path to an media file
        for s in media.seasons:
            for e in media.seasons[s].episodes:
                file = media.seasons[s].episodes[e].items[0].parts[0].file

                # If there is no file we can't get any metadata
                if file == "":
                    continue

                # Split the filepath and file extension
                filepath, file_extension = os.path.splitext(file)
                filepath = filepath.strip()

                if os.path.exists(filepath + ".info.json"):
                    try:
                        with open(filepath + ".info.json", encoding="utf-8") as json_file:
                            data = json.load(json_file)

                            metadata.title = data['uploader']
                            metadata.studio = data['uploader']
                            metadata.summary = data['playlist_title']

                            break
                    except IOError:
                        file = ""
                        Log("Could not access file '{}'".format(filepath + ".info.json"))
                        continue
                elif os.path.exists(filepath + ".nfo"):
                    try:
                        with open(filepath + ".nfo", encoding="utf-8") as xml_file:
                            data = ET.parse(xml_file, parser=ET.XMLParser(encoding='utf-8'))
                            root = data.getroot()
                            if root.tag != 'episodedetails':
                                continue
                            metadata.title = root.findtext('.//studio')
                            metadata.studio = root.findtext('.//studio')
                            metadata.summary = root.findtext('.//studio')

                            break
                    except IOError:
                        file = ""
                        Log("Could not access file '{}'".format(filepath + ".nfo"))
                        continue

            break

        @parallelize
        def UpdateEpisodes():
            for year in media.seasons:
                for shootID in media.seasons[year].episodes:
                    episode = metadata.seasons[year].episodes[shootID]
                    episode_media = media.seasons[year].episodes[shootID]
                    filepath, file_extension = os.path.splitext(episode_media.items[0].parts[0].file)
                    filepath = filepath.strip()

                    Log("Processing: '{}' in {}".format(filepath, metadata.title))

                    # Check if there is a thumbnail for this episode
                    for extension in [".jpg", ".jpeg", ".webp", ".png", ".tiff", ".gif", ".jp2"]:
                        maybeFile = filepath + extension
                        if os.path.isfile(maybeFile):
                            Log("Found thumbnail {}".format(maybeFile))
                            # we found an image, attempt to create an Proxy Media object to store it
                            try:
                                picture = Core.storage.load(maybeFile)
                                picture_hash = hashlib.md5(picture).hexdigest()
                                episode.thumbs[picture_hash] = Proxy.Media(picture, sort_order=1)
                                break
                            except:
                                Log("Could not access file '{}'".format(maybeFile))

                    # Attempt to open the .info.json file Youtube-DL stores.
                    if os.path.exists(filepath + ".info.json"):
                        try:
                            with open(filepath + ".info.json", encoding="utf-8") as json_file:
                                data = json.load(json_file)

                                episode.title = data['fulltitle']
                                episode.summary = data["description"]

                                if data['playlist_index']:
                                    episode.absolute_index = data['playlist_index']

                                if data['upload_date']:
                                    episode.originally_available_at = Datetime.ParseDate(data['upload_date']).date()

                                if data['average_rating']:
                                    episode.rating = (data['average_rating'] * 2)

                                Log("Processed successfully! This episode was named '{}'".format(data['fulltitle']))
                        except IOError:
                            # Attempt to make a title out of the filename
                            episode.title = re.sub('\[.{11}\]', '', os.path.basename(filepath)).strip()
                            Log("Could not access file '{}', named the episode '{}'".format(filepath + ".info.json", episode.title))
                    elif os.path.exists(filepath + ".nfo"):
                        try:
                            with open(filepath + ".nfo", encoding="utf-8") as xml_file:
                                data = data = ET.parse(xml_file, parser=ET.XMLParser(encoding='utf-8'))
                                root = data.getroot()
                                if root.tag != 'episodedetails':
                                    break
                                episode.title = root.findtext('.//title')
                                episode.summary = root.findtext('.//plot')
                                episode.originally_available_at = Datetime.ParseDate(root.findtext('.//aired'))

                        except IOError:
                            # Attempt to make a title out of the filename
                            episode.title = re.sub('\[.{11}\]', '', os.path.basename(filepath)).strip()
                            Log("Could not access file '{}', named the episode '{}'".format(filepath + ".nfo",
                                                                                            episode.title))