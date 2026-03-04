#!/bin/bash

rm expdmd.zip
zip -r expdmd.zip .
aws s3 cp expdmd.zip s3://ay-rmp-home/tmp/expdmd.zip

