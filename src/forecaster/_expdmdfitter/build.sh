#!/bin/bash

rm expdmd.zip
zip -r expdmd.zip .
aws s3 cp expdmd.zip s3://ay-emr-job/tmp/expdmd.zip

