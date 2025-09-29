import csv
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime 
import subprocess


from groupsmultieval import GroupsMultiEvaluator
from funcutils import *
from s3utils import *


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)


@app.post("/eval/{optimization_id}")
async def eval(optimization_id, info: Request):
    requests = await info.json()
    GroupsMultiEvaluator.process(optimization_id, requests)
    return {
        "status": "OK",
    }