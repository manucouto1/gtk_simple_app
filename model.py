#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from __future__ import unicode_literals
from datetime import datetime, timezone
from tzlocal import get_localzone
from threading import Thread, Lock, Condition
from pymongo import errors

import os
import youtube_dl
import pytz
import pymongo
import base64

import time

utc_dt = datetime.now(timezone.utc)


class Model():

    def __init__(self, mongoClient):
        self.mongoClient = pymongo.MongoClient(mongoClient)

    def loadDatabase(self, database):
        try:
            self.db = self.mongoClient[database]
            self.workoutDao = self.WorkoutDao(self.db["workouts"])
            self.exerciseDao = self.ExerciseDao(self.db["exercises"])
        except AttributeError:
            print("ERROR: client not connected!")

    class ExerciseDao():

        def __init__(self, dbTable):
            self.table = dbTable

        def findByName(self, exerciseInfo):
            try:
                aux = self.table.find_one({"name": exerciseInfo[0]})
                notReduce = False
                if aux != None:
                    id = aux["_id"]
                    if 'video' in aux:
                        video = Video(aux['video'])
                    else:
                        video = Video("")

                    image = Image(aux["image"])
                    notReduce = aux["image"] != ""

                    result = Exercise(
                        id, image, exerciseInfo[0], exerciseInfo[1], video, aux["description"], notReduce)
                else:
                    result = Exercise(
                        id, Image(""), exerciseInfo[0], exerciseInfo[1], Video(""), "", notReduce)

                return result
            except errors.OperationFailure as err:
                print("PyMongo ERROR:", err, "\n")

        def findAll(self):
            try:
                tuples = self.table.find({})
                result = []
                for aux in tuples:
                    notReduce = False
                    id = aux["_id"]
                    exercise = aux["name"]
                    
                    if 'video' in aux:
                        video = Video(aux['video'])
                    else:
                        video = Video("")

                    image = Image(aux["image"])
                    notReduce = aux["image"] != ""

                    result.append(Exercise(
                        id, image, exercise, aux["description"], None, video, notReduce))

                return result
            except errors.OperationFailure as err:
                print("PyMongo ERROR:", err, "\n")

    class WorkoutDao():
        def __init__(self, dbTable):
            try:
                self.table = dbTable
            except AttributeError:
                print("ERROR: database not load!")
        #db.workouts.find({exercises:{$elemMatch:{$elemMatch:{$in:["raised leg hold"]}}}},{"name":1}).pretty()

        def findWorkoutsWithExercie(self, exercise):
            try:
                tuples = self.table.find({"exercises": {"$elemMatch": {"$elemMatch": {
                                         "$in": [exercise]}}}}, {"unique": True, "dropDups": True, "name": 1})
                result = ""
                for i in range(tuples.count()):
                    #print(tuples[i])
                    result += tuples[i]["name"]
                    if i < tuples.count() - 1:
                        result += "\n"
                return result
            except AttributeError:
                print(
                    "ERROR: table not present!, load the database and init the dao again")

        def findAll(self):
            try:
                result = []
                tuples = self.table.find({})
                for aux in tuples:
                    if "date" in aux:
                        result.append(
                            Workout(str(aux["_id"]), Image(aux["image"]), aux["name"], aux["date"], aux["exercises"]))
                    else:
                        result.append(
                            Workout(str(aux["_id"]), Image(aux["image"]), aux["name"], "", aux["exercises"]))

                return result
            except AttributeError:
                print(
                    "ERROR: table not present!, load the database and init the dao again")
        def delete(self, id):
            print("\tDeleting workout ", id, " in the database")
            self.table.remove({"_id": id})
            print("\tDeleted")

class Workout():
    def __init__(self, id, image, workout, date, exercises):
        self.id = id
        self.image = image
        self.workout = workout
        self.exercises = exercises
        if date.strip() :
            self.date = date
        else:
            self.date = utc_dt.astimezone(
                get_localzone()).strftime("%d/%m/%Y")


class Exercise():
    def __init__(self, id, image, name, description, ocurrencia, video, notReduce):
        self.id = id
        self.image = image
        self.name = name
        self.description = description
        self.video = video
        self.notReduce = notReduce


class Image():
    def __init__(self, strImage):
        self.defaultImage = "downloads/images/error/404.png"
        if(strImage == ""):
            with open(self.defaultImage, "rb") as image_file:
                self.strImage = base64.b64encode(image_file.read())
                print(self.strImage)
        else:
            self.strImage = strImage

    def fromStringToBinary(self):
        return base64.b64decode(self.strImage)


class Video():
    def __init__(self, strVideo):
        self.defaultUrl = "/error/404"
        if(strVideo == ""):
            self.strVideo = self.defaultUrl
        else:
            self.strVideo = strVideo

    def my_hook(self, d):
        if d['status'] == 'finished':
            print('Done downloading, now converting ...')

    def fromStringToMp4(self):
        ydl_opts = {
            'download_archive': 'downloads/videos/downloaded_videos.txt',
            'outtmpl': 'downloads/videos/%(id)s.%(ext)s',
            'logger': self.MyLogger(),
            'progress_hooks': [self.my_hook],
        }

        aux = self.strVideo.split("?v=")
        idstr = aux[len(aux)-1]

        if not os.path.isfile('downloads/videos/'+idstr+'.mp4'):
            if not self.supported(self.strVideo):
                self.strVideo = self.defaultUrl
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                videoInfo = ydl.extract_info(self.strVideo, download=True)
                fileName = ydl.prepare_filename(videoInfo)
        else:
            fileName = "downloads/videos/"+idstr+".mp4"
        print(fileName)
        return fileName

    def supported(self, url):
        ies = youtube_dl.extractor.gen_extractors()
        for ie in ies:
            if ie.suitable(url) and ie.IE_NAME != 'generic':
                return True
        return False

    class MyLogger(object):
            def debug(self, msg):
                pass

            def warning(self, msg):
                pass

            def error(self, msg):
                print(msg)
